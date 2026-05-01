'use client';
import { useState, useEffect } from 'react';
import { Wand2, Copy, CheckCheck, AlertCircle, Plus, RefreshCw, ChevronDown, ExternalLink, Play, Search, SlidersHorizontal, CheckCircle2 } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { ColumnTypeDef } from './DataInspectionPanel';
import { validateSql } from '../../lib/api';
import { PROVIDERS, CUSTOM_MODEL_OPTION, type Provider } from '../../config/ai-providers';

/**
 * Build system prompt for LLM-based SQL generation.
 *
 * Creates a detailed prompt that includes table schema, SQL syntax rules,
 * and constraints for DuckDB query generation.
 *
 * @param {ColumnTypeDef[]} schema - Column type definitions for the input dataset
 * @returns {string} Formatted system prompt for the LLM
 *
 * @example
 * ```tsx
 * const prompt = buildSystemPrompt([
 *   { column_name: 'name', column_type: 'VARCHAR' },
 *   { column_name: 'age', column_type: 'INTEGER' }
 * ]);
 * // Returns: "You are a DuckDB SQL expert... Table Schema: "name" VARCHAR\n  "age" INTEGER..."
 * ```
 */
function buildSystemPrompt(schema: ColumnTypeDef[]): string {
  const schemaTxt = schema.map(c => `  "${c.column_name}" ${c.column_type}`).join('\n');
  return `You are a DuckDB SQL expert. Generate a complete, valid DuckDB SQL query based on the user's natural language request.

Table Schema:
${schemaTxt}

Important rules:
- ONLY use column names that are explicitly listed in the "Table Schema" section above. DO NOT invent or guess column names even if the user request suggests them.
- If the user request uses a term that doesn't exactly match a column name, use your best judgement to map it to the closest available column (e.g. if user says "total" but the schema has "amount", use "amount").
- Use standard DuckDB SQL syntax (Standard SQL, NOT MySQL/Backticks)
- Use DOUBLE QUOTES (") for column and table names (e.g. "Last Name")
- NEVER use backticks for identifiers.
- DO NOT quote function calls like COUNT(), SUM(), etc.
- ALWAYS use clear aliases (AS "alias") for all aggregations and expressions
- ALWAYS wrap columns in TRY_CAST("col" AS DOUBLE) when performing arithmetic (SUM, AVG, +, -, etc.) if the column type in the provided schema is VARCHAR.
- Reference the input dataset using {{input}} as the table name
- Return ONLY the raw SQL query without explanations or markdown fences`;
}

/**
 * Call LLM API to generate SQL query from natural language.
 *
 * Supports multiple LLM providers (OpenAI, Anthropic, Google, Groq, Cerebras, OpenRouter)
 * with provider-specific request/response format handling.
 *
 * @param {Provider} provider - LLM provider configuration (base URL, type, headers)
 * @param {string} model - Model identifier (e.g., 'gpt-4', 'claude-3-opus-20240229')
 * @param {string} apiKey - API authentication key
 * @param {string} userPrompt - Natural language request from the user
 * @param {ColumnTypeDef[]} schema - Column type definitions for context
 * @returns {Promise<string>} Generated SQL query
 * @throws {Error} If API request fails or returns invalid response
 *
 * @example
 * ```tsx
 * const sql = await callLLM(
 *   { id: 'openai', baseUrl: 'https://api.openai.com/v1/chat/completions', type: 'openai' },
 *   'gpt-4',
 *   'sk-...',
 *   'Show me the total sales by region',
 *   [{ column_name: 'region', column_type: 'VARCHAR' }, { column_name: 'sales', column_type: 'DOUBLE' }]
 * );
 * ```
 */
async function callLLM(provider: Provider, model: string, apiKey: string, userPrompt: string, schema: ColumnTypeDef[]): Promise<string> {
  const systemPrompt = buildSystemPrompt(schema);
  const fullPrompt = `${systemPrompt}\n\nUser request: ${userPrompt}`;

  if (provider.type === 'google') {
    const res = await fetch(`${provider.baseUrl}/${model}:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: fullPrompt }] }],
        generationConfig: { temperature: 0.1, maxOutputTokens: 1024 }
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
    return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  }

  if (provider.type === 'anthropic') {
    // Anthropic format
    const res = await fetch(provider.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
        ...(provider.extraHeaders || {}),
      },
      body: JSON.stringify({
        model,
        max_tokens: 1024,
        messages: [{ role: 'user', content: fullPrompt }],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
    return data.content?.[0]?.text || '';
  }

  // provider.type === 'openai'
  const res = await fetch(provider.baseUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      ...(provider.extraHeaders || {}),
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: fullPrompt }],
      max_tokens: 1024,
      temperature: 0.1,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
  return data.choices?.[0]?.message?.content || '';
}

interface Props {
  schema: ColumnTypeDef[];
  onInsertSql: (sql: string) => void;
  initialPrompt?: string;
  nodes: Node[];
  edges: Edge[];
  nodeId: string;
  onPreviewSql: (nodes: Node[], edges: Edge[], nodeId: string, sql: string) => Promise<any>;
}

/**
 * AI-powered SQL builder panel for natural language to SQL query generation.
 *
 * Provides an interface for users to describe their data analysis needs in plain language,
 * then uses LLM APIs (OpenAI, Anthropic, Google, etc.) to generate DuckDB SQL queries.
 * Features include:
 * - Multiple LLM provider support (OpenAI, Anthropic, Google, Groq, Cerebras, OpenRouter)
 * - SQL preview and validation
 * - Workflow integration with node-based canvas
 * - Error handling and user feedback
 *
 * @component AiSqlBuilderPanel
 *
 * @param {Props} props - Component properties
 * @param {ColumnTypeDef[]} props.schema - Column type definitions for the input dataset
 * @param {(sql: string) => void} props.onInsertSql - Callback when SQL is generated and accepted
 * @param {string} [props.initialPrompt] - Pre-filled prompt text
 * @param {any[]} props.nodes - Workflow canvas nodes
 * @param {any[]} props.edges - Workflow canvas edges
 * @param {string} props.nodeId - Current workflow node ID
 * @param {(nodes: any[], edges: any[], nodeId: string, sql: string) => Promise<any>} props.onPreviewSql - Async function to preview SQL results
 *
 * @returns {JSX.Element} Rendered AI SQL builder panel
 *
 * @example
 * ```tsx
 * <AiSqlBuilderPanel
 *   schema={[{ column_name: 'name', column_type: 'VARCHAR' }, { column_name: 'age', column_type: 'INTEGER' }]}
 *   onInsertSql={(sql) => console.log('Generated SQL:', sql)}
 *   nodes={[]}
 *   edges={[]}
 *   nodeId="node-1"
 *   onPreviewSql={async (nodes, edges, nodeId, sql) => await previewQuery(sql)}
 * />
 * ```
 */
export default function AiSqlBuilderPanel({ schema, onInsertSql, initialPrompt, nodes, edges, nodeId, onPreviewSql }: Props) {
  const [providerId, setProviderId] = useState(PROVIDERS[0].id);
  const [modelId, setModelId] = useState(PROVIDERS[0].models[0].id);
  const [customModelId, setCustomModelId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [inserted, setInserted] = useState(false);
  const [isSchemaExpanded, setIsSchemaExpanded] = useState(false);
  const [previewResult, setPreviewResult] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationMessage, setValidationMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const visibleSchema = isSchemaExpanded ? schema : schema.slice(0, 8);

  const provider = PROVIDERS.find(p => p.id === providerId)!;
  const isCustomModel = modelId === CUSTOM_MODEL_OPTION.id;
  const effectiveModelId = isCustomModel ? customModelId : modelId;

  // Sync with initialPrompt if provided
  useEffect(() => {
    if (initialPrompt) {
      setPrompt(initialPrompt);
    }
  }, [initialPrompt]);

  // Load API key from localStorage when provider changes
  useEffect(() => {
    const stored = localStorage.getItem(`ai_sql_key_${providerId}`);
    setApiKey(stored || '');
    const firstModel = PROVIDERS.find(p => p.id === providerId)!.models[0].id;
    setModelId(firstModel);
    setCustomModelId('');
  }, [providerId]);

  const handleSaveKey = () => {
    if (apiKey) localStorage.setItem(`ai_sql_key_${providerId}`, apiKey);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (!apiKey.trim()) { setError('Please enter your API key.'); return; }
    if (isCustomModel && !customModelId.trim()) { setError('Please enter a custom model ID.'); return; }
    setIsGenerating(true); setError(null); setGeneratedSql(''); setPreviewResult(null);
    try {
      const sql = await callLLM(provider, effectiveModelId, apiKey, prompt, schema);
      setGeneratedSql(sql.trim());
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally { setIsGenerating(false); }
  };

  const handleExecute = async () => {
    if (!generatedSql) return;
    setIsExecuting(true);
    setError(null);
    try {
      const result = await onPreviewSql(nodes, edges, nodeId, generatedSql);
      if (result.status === 'error') {
        setError(result.message);
      } else {
        setPreviewResult(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedSql).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 4000);
    });
  };

  const handleInsert = () => {
    onInsertSql(generatedSql);
    setInserted(true); setTimeout(() => setInserted(false), 4000);
  };

  const handleValidate = async () => {
    if (!generatedSql) return;
    setIsValidating(true);
    setValidationMessage(null);
    try {
      const preparedColumns = schema.map(c => JSON.stringify(c));
      const res = await validateSql(generatedSql, 'input_table', preparedColumns);
      if (res.status === 'success') {
        setValidationMessage({ text: "SQL is valid!", type: 'success' });
      } else {
        setValidationMessage({ text: res.message || "Invalid SQL syntax.", type: 'error' });
      }
    } catch (err: any) {
      setValidationMessage({ text: err.message || "Validation failed.", type: 'error' });
    } finally {
      setIsValidating(false);
      // Auto-hide success message, keep error message visible
      if (validationMessage?.type === 'success') {
        setTimeout(() => setValidationMessage(null), 5000);
      }
    }
  };

  const handleBeautify = () => {
    if (!generatedSql) return;

    // Improved SQL formatter logic
    const tokens = generatedSql.split(/('(?:''|[^'])*'|--.*(?:\n|$))/g);
    const beautified = tokens.map((token: string) => {
      if (!token) return '';
      if (token.startsWith("'") || token.startsWith("--")) return token;

      return token
        .replace(/\s+/g, ' ')
        .replace(/\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|UNION|WITH|SET|VALUES|CASE|WHEN|THEN|ELSE|END|AS)\b/gi,
          (match: string) => `\n${match.toUpperCase()}`)
        .replace(/,/g, ',\n  ');
    }).join('')
      .replace(/\n\s*\n/g, '\n')
      .replace(/\s*\n/g, '\n')
      .replace(/^\n+/, '')
      .trim();

    setGeneratedSql(beautified);
  };

  return (
    <div className="h-full flex flex-col min-h-0 bg-white">
      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-12 space-y-4 custom-scrollbar">
        {/* Provider + Model Selection */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">Provider</label>
            <div className="relative">
              <select
                value={providerId}
                onChange={e => setProviderId(e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] appearance-none bg-white pr-8"
              >
                {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6B778C] pointer-events-none" />
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">Model</label>
            <div className="relative">
              <select
                value={modelId}
                onChange={e => setModelId(e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] appearance-none bg-white pr-8"
              >
                {provider.models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                <option value={CUSTOM_MODEL_OPTION.id}>{CUSTOM_MODEL_OPTION.name}</option>
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6B778C] pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Custom Model Input */}
        {isCustomModel && (
          <div>
            <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">Custom Model ID</label>
            <input
              type="text"
              placeholder="e.g. gemini-2.0-flash-thinking-exp-01-21, gpt-4-turbo-2024-04-09..."
              value={customModelId}
              onChange={e => setCustomModelId(e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm font-mono focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] outline-none"
            />
            <p className="text-[10px] text-[#6B778C] mt-1">Enter any model ID supported by {provider.name}. Check the provider&apos;s documentation for available models.</p>
          </div>
        )}

        {/* API Key */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">
              API Key <span className="font-normal normal-case text-[#6B778C]">(stored locally)</span>
            </label>
            <a
              href={provider.apiKeyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] font-bold text-[#0052CC] hover:underline flex items-center gap-1"
            >
              Get Key <ExternalLink size={10} />
            </a>
          </div>
          <div className="flex gap-2">
            <input
              type="password"
              placeholder={`Enter ${provider.name} API key…`}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              onBlur={handleSaveKey}
              className="flex-1 border border-[#DFE1E6] rounded-md px-3 py-2 text-sm font-mono focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] outline-none"
            />
          </div>
        </div>

        {/* Schema Context */}
        {schema.length > 0 && (
          <div className="p-2.5 bg-[#1E1E2E] rounded-md transition-all duration-300">
            <div className="flex items-center justify-between mb-1.5">
              <div className="text-[9px] font-bold text-[#89DCEB] uppercase tracking-wider">Schema Context</div>
              {schema.length > 8 && (
                <button
                  onClick={() => setIsSchemaExpanded(!isSchemaExpanded)}
                  className="text-[9px] font-bold text-[#565f89] hover:text-[#89DCEB] transition-colors uppercase tracking-widest outline-none"
                >
                  {isSchemaExpanded ? 'Collapse' : `+ ${schema.length - 8} more`}
                </button>
              )}
            </div>
            <div className="text-[10px] text-[#CDD6F4] font-mono leading-relaxed max-h-48 overflow-y-auto custom-scrollbar pr-2">
              {visibleSchema.map(c => (
                <div key={c.column_name} className="flex justify-between gap-4 py-0.5">
                  <span className="text-[#89DCEB] truncate">{c.column_name}</span>
                  <span className="text-[#6B778C] shrink-0 font-mono">{c.column_type}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {schema.length === 0 && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex items-center gap-2">
            <AlertCircle size={14} className="text-amber-600 shrink-0" />
            <p className="text-[11px] text-amber-700">Execute the workflow first to load schema context for accurate SQL generation.</p>
          </div>
        )}

        {/* Natural Language Input */}
        <div>
          <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">Your Request</label>
          <textarea
            rows={3}
            placeholder={'e.g. "Show me the top 10 customers by total revenue, excluding nulls"'}
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={e => { if ((e.code === 'Enter' || e.code === 'NumpadEnter' || e.code === 'KeyR') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleGenerate(); } }}
            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] outline-none resize-y min-h-[80px]"
          />
          <p className="text-[10px] text-[#6B778C] mt-1">Tip: Press Cmd/Ctrl+Enter to generate.</p>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="w-full py-2.5 bg-gradient-to-r from-[#6554C0] to-[#0052CC] text-white font-bold text-sm rounded-md shadow-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isGenerating ? <RefreshCw size={15} className="animate-spin" /> : <Wand2 size={15} />}
          {isGenerating ? 'Generating SQL…' : 'Generate SQL'}
        </button>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle size={14} className="text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-xs font-bold text-red-700 mb-1">Error</p>
              <p className="text-[11px] text-red-600 font-mono break-all">{error}</p>
            </div>
          </div>
        )}

        {/* Generated SQL Result */}
        {generatedSql && (
          <div className="border border-[#DFE1E6] rounded-md overflow-hidden flex flex-col transition-all animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center justify-between px-3 py-2 bg-[#1E1E2E] shrink-0">
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-bold text-[#89DCEB] uppercase tracking-wider">Generated SQL</span>
                {validationMessage && (
                  <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold transition-all animate-in fade-in zoom-in-95 ${validationMessage.type === 'success' ? 'bg-[#36B37E]/20 text-[#36B37E]' : 'bg-[#FF5630]/20 text-[#FF5630]'
                    }`}>
                    {validationMessage.type === 'success' ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
                    {validationMessage.text}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={handleValidate} disabled={isValidating}
                  title="Validate SQL"
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded bg-white/10 text-[#CDD6F4] hover:bg-white/20 transition-colors disabled:opacity-50">
                  {isValidating ? <RefreshCw size={10} className="animate-spin" /> : <Search size={10} />}
                  Validate
                </button>
                <button onClick={handleBeautify}
                  title="Beautify SQL"
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded bg-white/10 text-[#CDD6F4] hover:bg-white/20 transition-colors">
                  <SlidersHorizontal size={10} />
                  Format
                </button>
                <button onClick={handleCopy}
                  className={`flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded transition-colors ${copied ? 'bg-[#36B37E] text-white' : 'bg-white/10 text-[#CDD6F4] hover:bg-white/20'}`}>
                  {copied ? <CheckCheck size={10} /> : <Copy size={10} />}
                  {copied ? 'Copy' : 'Copy'}
                </button>
                <button onClick={handleExecute} disabled={isExecuting}
                  className={`flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded transition-colors bg-[#6554C0] text-white hover:bg-[#5243AA] disabled:opacity-50`}>
                  {isExecuting ? <RefreshCw size={10} className="animate-spin" /> : <Play size={10} />}
                  {isExecuting ? 'Run' : 'Run'}
                </button>
                <button onClick={handleInsert}
                  className={`flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded transition-colors ${inserted ? 'bg-[#36B37E] text-white' : 'bg-[#0052CC] text-white hover:bg-[#0065FF]'}`}>
                  <Plus size={10} />
                  {inserted ? 'Insert' : 'Insert'}
                </button>
              </div>
            </div>
            <pre className="bg-[#1E1E2E] text-[#CDD6F4] text-[11px] p-3 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed border-t border-white/10 custom-scrollbar flex-1 min-h-0">{generatedSql}</pre>
          </div>
        )}

        {/* Preview Results Table */}
        {previewResult && (
          <div className="border border-[#DFE1E6] rounded-md overflow-hidden flex flex-col transition-all animate-in fade-in slide-in-from-top-2">
            <div className="bg-[#FAFBFC] border-b border-[#DFE1E6] px-3 py-2 flex items-center justify-between shrink-0">
              <span className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">SQL Execution Result ({previewResult.row_count} rows)</span>
              <button onClick={() => setPreviewResult(null)} className="text-[#6B778C] hover:text-[#171717]">
                <Plus size={14} className="rotate-45" />
              </button>
            </div>
            <div className="overflow-x-auto overflow-y-auto custom-scrollbar flex-1">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 sticky top-0 z-10 shadow-sm">
                    {previewResult.columns.map((col: string) => (
                      <th key={col} className="px-3 py-2 text-[10px] font-bold text-[#6B778C] uppercase tracking-wider border-b border-[#DFE1E6] whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DFE1E6]">
                  {previewResult.preview.map((row: any, i: number) => (
                    <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                      {previewResult.columns.map((col: string) => (
                        <td key={col} className="px-3 py-1.5 text-[11px] text-[#171717] font-mono whitespace-nowrap">{String(row[col])}</td>
                      ))}
                    </tr>
                  ))}
                  {previewResult.preview.length === 0 && (
                    <tr>
                      <td colSpan={previewResult.columns.length} className="px-3 py-8 text-center text-xs text-[#6B778C]">No results returned.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
