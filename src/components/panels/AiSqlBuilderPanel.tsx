'use client';
import React, { useState, useEffect } from 'react';
import { Wand2, Copy, CheckCheck, AlertCircle, Plus, RefreshCw, ChevronDown } from 'lucide-react';
import type { ColumnTypeDef } from './DataInspectionPanel';

interface Provider {
  id: string; name: string; baseUrl: string;
  type: 'openai' | 'anthropic' | 'google';
  extraHeaders?: Record<string, string>;
  models: { id: string; name: string }[];
}

const PROVIDERS: Provider[] = [
  {
    id: 'google', name: 'Google (Gemini)', baseUrl: 'https://generativelanguage.googleapis.com/v1beta/models', type: 'google',
    models: [
      { id: 'gemini-2.0-flash', name: 'Gemini 2.5 Flash' },
      { id: 'gemini-2.0-flash-lite', name: 'Gemini 2.0 Flash Lite' },
      { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
      { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
    ],
  },
  {
    id: 'groq', name: 'Groq', baseUrl: 'https://api.groq.com/openai/v1/chat/completions', type: 'openai',
    models: [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile' },
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant' },
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B 32K' },
      { id: 'gemma2-9b-it', name: 'Gemma 2 9B' },
    ],
  },
  {
    id: 'cerebras', name: 'Cerebras', baseUrl: 'https://api.cerebras.ai/v1/chat/completions', type: 'openai',
    models: [
      { id: 'llama-3.3-70b', name: 'Llama 3.3 70B' },
      { id: 'llama3.1-8b', name: 'Llama 3.1 8B' },
    ],
  },
  {
    id: 'openrouter', name: 'OpenRouter', baseUrl: 'https://openrouter.ai/api/v1/chat/completions', type: 'openai',
    extraHeaders: { 'HTTP-Referer': 'https://duckdb-platform.local', 'X-Title': 'DuckDB AI SQL Builder' },
    models: [
      { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet' },
      { id: 'openai/gpt-4o', name: 'GPT-4o' },
      { id: 'openai/gpt-4o-mini', name: 'GPT-4o mini' },
      { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B' },
      { id: 'google/gemini-flash-1.5', name: 'Gemini 1.5 Flash' },
      { id: 'google/gemini-pro-1.5', name: 'Gemini 1.5 Pro' },
      { id: 'deepseek/deepseek-chat', name: 'DeepSeek Chat' },
    ],
  },
  {
    id: 'openai', name: 'OpenAI', baseUrl: 'https://api.openai.com/v1/chat/completions', type: 'openai',
    models: [
      { id: 'gpt-4o', name: 'GPT-4o' },
      { id: 'gpt-4o-mini', name: 'GPT-4o mini' },
      { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
    ],
  },
  {
    id: 'anthropic', name: 'Anthropic', baseUrl: 'https://api.anthropic.com/v1/messages', type: 'anthropic',
    models: [
      { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet' },
      { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku' },
      { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus' },
    ],
  },
];

function buildSystemPrompt(schema: ColumnTypeDef[]): string {
  const schemaTxt = schema.map(c => `  "${c.column_name}" ${c.column_type}`).join('\n');
  return `You are a DuckDB SQL expert. Generate a complete, valid DuckDB SQL query based on the user's natural language request.

Table Schema:
${schemaTxt}

Important rules:
- Use DuckDB SQL syntax (not PostgreSQL or MySQL)
- Use double quotes around column names (e.g. "column_name")
- Reference the input dataset using {{input}} as the table name
- Return ONLY the raw SQL query — no markdown, no code fences, no explanations
- Use TRY_CAST for numeric conversions where appropriate`;
}

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
}

export default function AiSqlBuilderPanel({ schema, onInsertSql }: Props) {
  const [providerId, setProviderId] = useState(PROVIDERS[0].id);
  const [modelId, setModelId] = useState(PROVIDERS[0].models[0].id);
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [inserted, setInserted] = useState(false);
  const [isSchemaExpanded, setIsSchemaExpanded] = useState(false);
  const visibleSchema = isSchemaExpanded ? schema : schema.slice(0, 8);

  const provider = PROVIDERS.find(p => p.id === providerId)!;

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
    setIsGenerating(true); setError(null); setGeneratedSql('');
    try {
      const sql = await callLLM(provider, modelId, apiKey, prompt, schema);
      setGeneratedSql(sql.trim());
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally { setIsGenerating(false); }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedSql).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleInsert = () => {
    onInsertSql(generatedSql);
    setInserted(true); setTimeout(() => setInserted(false), 2000);
  };

  return (
    <div className="h-full flex flex-col overflow-auto p-4 gap-4">
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
        <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">
          API Key <span className="font-normal normal-case text-[#6B778C]">(stored locally in your browser)</span>
        </label>
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
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate(); }}
          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] outline-none resize-none"
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
          <div>
            <p className="text-xs font-bold text-red-700 mb-1">API Error</p>
            <p className="text-[11px] text-red-600 font-mono break-all">{error}</p>
          </div>
        </div>
      )}

      {/* Generated SQL Result */}
      {generatedSql && (
        <div className="border border-[#DFE1E6] rounded-md overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-[#1E1E2E]">
            <span className="text-[10px] font-bold text-[#89DCEB] uppercase tracking-wider">Generated SQL</span>
            <div className="flex gap-2">
              <button onClick={handleCopy}
                className={`flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded transition-colors ${copied ? 'bg-[#36B37E] text-white' : 'bg-white/10 text-[#CDD6F4] hover:bg-white/20'}`}>
                {copied ? <CheckCheck size={10} /> : <Copy size={10} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button onClick={handleInsert}
                className={`flex items-center gap-1 px-2 py-1 text-[10px] font-bold rounded transition-colors ${inserted ? 'bg-[#36B37E] text-white' : 'bg-[#0052CC] text-white hover:bg-[#0065FF]'}`}>
                <Plus size={10} />
                {inserted ? 'Inserted!' : 'Insert as Node'}
              </button>
            </div>
          </div>
          <pre className="bg-[#1E1E2E] text-[#CDD6F4] text-xs p-3 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed border-t border-white/10">{generatedSql}</pre>
        </div>
      )}
    </div>
  );
}
