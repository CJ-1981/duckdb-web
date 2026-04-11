'use client';
import React, { useState, useEffect } from 'react';
import { Wand2, Copy, CheckCheck, AlertCircle, Plus, RefreshCw, ChevronDown, ExternalLink, Play, Search, SlidersHorizontal, CheckCircle2 } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { ColumnTypeDef } from './DataInspectionPanel';
import { validateSql } from '../../lib/api';

interface Provider {
  id: string; name: string; baseUrl: string;
  type: 'openai' | 'anthropic' | 'google';
  apiKeyUrl: string;
  extraHeaders?: Record<string, string>;
  models: { id: string; name: string }[];
}

const PROVIDERS: Provider[] = [
  {
    id: 'google', name: 'Google (Gemini)', baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models', type: 'google',
    apiKeyUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      // Gemini 2.5 Series (Latest Stable)
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
      { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
      { id: 'gemini-2.5-flash-exp', name: 'Gemini 2.5 Flash (Experimental)' },
      { id: 'gemini-2.5-pro-exp', name: 'Gemini 2.5 Pro (Experimental)' },
      // Gemini 2.0 Series
      { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
      { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash (Experimental)' },
      { id: 'gemini-2.0-flash-thinking', name: 'Gemini 2.0 Flash Thinking' },
      { id: 'gemini-2.0-flash-thinking-exp', name: 'Gemini 2.0 Flash Thinking (Experimental)' },
      { id: 'gemini-2.0-pro', name: 'Gemini 2.0 Pro' },
      { id: 'gemini-2.0-pro-exp', name: 'Gemini 2.0 Pro (Experimental)' },
      // Gemini 1.5 Series
      { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
      { id: 'gemini-1.5-flash-8b', name: 'Gemini 1.5 Flash (8B)' },
      { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
      { id: 'gemini-1.5-pro-8b', name: 'Gemini 1.5 Pro (8B)' },
      // Gemini 1.0 Series (Legacy)
      { id: 'gemini-1.0-pro', name: 'Gemini 1.0 Pro' },
      { id: 'gemini-1.0-pro-001', name: 'Gemini 1.0 Pro (001)' },
      // Gemini 3.0 Preview (Cutting Edge)
      { id: 'gemini-3-flash-preview', name: 'Gemini 3.0 Flash (Preview)' },
      { id: 'gemini-3-flash-preview-exp', name: 'Gemini 3.0 Flash (Experimental)' },
      { id: 'gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash Lite (Preview)' },
      { id: 'gemini-exp-1206', name: 'Gemini Experimental (1206)' },
    ],
  },
  {
    id: 'groq', name: 'Groq', baseUrl: 'https://api.groq.com/openai/v1/chat/completions', type: 'openai',
    apiKeyUrl: 'https://console.groq.com/keys',
    models: [
      // Llama 3.3 Series
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile' },
      // Llama 3.1 Series
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant' },
      { id: 'llama-3.1-70b-versatile', name: 'Llama 3.1 70B Versatile' },
      // Mixtral
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B 32K' },
      // Gemma
      { id: 'gemma2-9b-it', name: 'Gemma 2 9B' },
      { id: 'gemma-7b-it', name: 'Gemma 7B' },
      // Qwen
      { id: 'qwen-2.5-72b-instruct', name: 'Qwen 2.5 72B' },
    ],
  },
  {
    id: 'cerebras', name: 'Cerebras', baseUrl: 'https://api.cerebras.ai/v1/chat/completions', type: 'openai',
    apiKeyUrl: 'https://cloud.cerebras.ai/',
    models: [
      // Llama 3.3 Series
      { id: 'llama-3.3-70b', name: 'Llama 3.3 70B' },
      // Llama 3.1 Series
      { id: 'llama3.1-8b', name: 'Llama 3.1 8B' },
      { id: 'llama-3.1-70b', name: 'Llama 3.1 70B' },
      // Llama 3 Series
      { id: 'llama-3-8b', name: 'Llama 3 8B' },
      { id: 'llama-3-70b', name: 'Llama 3 70B' },
      // Mixtral
      { id: 'mixtral-8x7b', name: 'Mixtral 8x7B' },
    ],
  },
  {
    id: 'openrouter', name: 'OpenRouter', baseUrl: 'https://openrouter.ai/api/v1/chat/completions', type: 'openai',
    apiKeyUrl: 'https://openrouter.ai/keys',
    extraHeaders: { 'HTTP-Referer': 'https://duckdb-platform.local', 'X-Title': 'DuckDB AI SQL Builder' },
    models: [
      // Anthropic
      { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
      { id: 'anthropic/claude-3.5-haiku', name: 'Claude 3.5 Haiku' },
      { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus' },
      // OpenAI
      { id: 'openai/gpt-4o', name: 'GPT-4o' },
      { id: 'openai/gpt-4o-mini', name: 'GPT-4o mini' },
      { id: 'openai/o1-mini', name: 'o1-mini' },
      { id: 'openai/o1-preview', name: 'o1-preview' },
      // Meta
      { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B' },
      { id: 'meta-llama/llama-3.1-405b-instruct', name: 'Llama 3.1 405B' },
      { id: 'meta-llama/llama-3.1-70b-instruct', name: 'Llama 3.1 70B' },
      { id: 'meta-llama/llama-3.1-8b-instruct', name: 'Llama 3.1 8B' },
      // Google Gemini (Latest)
      { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
      { id: 'google/gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' },
      { id: 'google/gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
      { id: 'google/gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
      { id: 'google/gemini-2.0-flash-thinking', name: 'Gemini 2.0 Flash Thinking' },
      { id: 'google/gemini-2.0-pro', name: 'Gemini 2.0 Pro' },
      { id: 'google/gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
      { id: 'google/gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
      { id: 'google/gemini-flash-1.5', name: 'Gemini 1.5 Flash (Legacy)' },
      { id: 'google/gemini-pro-1.5', name: 'Gemini 1.5 Pro (Legacy)' },
      { id: 'google/gemini-3-flash-preview', name: 'Gemini 3.0 Flash (Preview)' },
      { id: 'google/gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash Lite (Preview)' },
      // DeepSeek
      { id: 'deepseek/deepseek-chat', name: 'DeepSeek Chat' },
      { id: 'deepseek/deepseek-chat:latest', name: 'DeepSeek Chat (Latest)' },
      { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1' },
      // Mistral
      { id: 'mistralai/mistral-large', name: 'Mistral Large' },
      { id: 'mistralai/mistral-small', name: 'Mistral Small' },
      { id: 'mistralai/ministral-3b', name: 'Ministral 3B' },
      // Qwen
      { id: 'qwen/qwen-2.5-72b-instruct', name: 'Qwen 2.5 72B' },
      { id: 'qwen/qwen-2-72b-instruct', name: 'Qwen 2 72B' },
      { id: 'qwen/qwen-2.5-coder-32b-instruct', name: 'Qwen 2.5 Coder 32B' },
    ],
  },
  {
    id: 'openai', name: 'OpenAI', baseUrl: 'https://api.openai.com/v1/chat/completions', type: 'openai',
    apiKeyUrl: 'https://platform.openai.com/api-keys',
    models: [
      // GPT-4o Series
      { id: 'gpt-4o', name: 'GPT-4o' },
      { id: 'gpt-4o-mini', name: 'GPT-4o mini' },
      // O1 Series (Reasoning Models)
      { id: 'o1-mini', name: 'o1-mini' },
      { id: 'o1-preview', name: 'o1-preview' },
      // GPT-4 Turbo (Legacy)
      { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
      { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo Preview' },
    ],
  },
  {
    id: 'anthropic', name: 'Anthropic', baseUrl: 'https://api.anthropic.com/v1/messages', type: 'anthropic',
    apiKeyUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      // Claude 3.5 Series (Latest)
      { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet' },
      { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku' },
      // Claude 3 Series (Previous)
      { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus' },
      { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet' },
      { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
    ],
  },
];

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
    const firstModel = provider.models[0].id;
    setModelId(firstModel);
  }, [providerId]);

  const handleSaveKey = () => {
    if (apiKey) localStorage.setItem(`ai_sql_key_${providerId}`, apiKey);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (!apiKey.trim()) { setError('Please enter your API key.'); return; }
    setIsGenerating(true); setError(null); setGeneratedSql(''); setPreviewResult(null);
    try {
      const sql = await callLLM(provider, modelId, apiKey, prompt, schema);
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
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6B778C] pointer-events-none" />
            </div>
          </div>
        </div>

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
