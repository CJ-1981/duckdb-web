'use client';
import { useState, useEffect } from 'react';
import { Wand2, AlertCircle, Plus, ChevronDown, RefreshCw, CheckCheck } from 'lucide-react';
import { Node, Edge } from '@xyflow/react';
import type { ColumnTypeDef } from './DataInspectionPanel';
import { PROVIDERS, CUSTOM_MODEL_OPTION, type Provider } from '../../config/ai-providers';

function buildSystemPrompt(sourceSchemas: { nodeId: string, label: string, schema: ColumnTypeDef[] }[]): string {
  const schemasText = sourceSchemas.map(s => {
    return `Source Node ID: ${s.nodeId} (Label: ${s.label})\nSchema:\n${s.schema.map(c => `  - ${c.column_name} (${c.column_type})`).join('\n')}`;
  }).join('\n\n');

  return `You are an expert data engineer and workflow builder. 
Your task is to generate a JSON representing a data processing pipeline (React Flow nodes and edges) based on the user's natural language request.

Available Source Nodes (DO NOT modify or recreate these, just use their IDs as sources for your new edges):
${schemasText}

You must return ONLY a valid JSON object with two arrays: "nodes" and "edges". Do not include markdown fences like \`\`\`json.

The JSON format must be:
{
  "nodes": [
    {
      "id": "generated_node_1",
      "type": "default",
      "position": { "x": 300, "y": 100 },
      "data": {
        "label": "Filter data",
        "subtype": "filter",
        "config": { "column": "age", "operator": ">", "value": "18" }
      }
    }
  ],
  "edges": [
    {
      "id": "generated_edge_1",
      "source": "source_node_id",
      "target": "generated_node_1"
    }
  ]
}

Available node subtypes and their configs:
- filter: { column, operator (==, !=, >, <, >=, <=, contains, starts_with, is_null), value }
- aggregate: { groupBy: "col1, col2", aggregations: [{ column, operation (sum, avg, count, min, max), alias }] }
- sort: { column, direction (asc, desc) }
- limit: { count: number }
- select: { columns: "col1, col2" }
- computed: { expression: "sql expression", alias: "new_col" }
- clean: { column, operation (trim, upper, lower, numeric, replace_null, to_date) }
- distinct: { columns: "col1, col2" (empty for all) }
- case_when: { conditions: [{ when: "col > 10", then: "High" }], elseValue: "Low", alias: "category" }
- combine: { joinType: "inner", leftColumn: "id", rightColumn: "id" }
- raw_sql: { sql: "SELECT a.*, b.* FROM {{input1}} a JOIN {{input2}} b ON a.id = b.id" } (Note: use {{input1}}, {{input2}} etc. to refer to the 1st, 2nd incoming edges)

Instructions:
1. Generate logical node IDs (e.g., "ai_filter_1", "ai_agg_1").
2. Position them logically (e.g., x spacing 300, y spacing 100).
3. Create edges connecting existing source nodes to your new nodes, and connecting your new nodes sequentially.
4. Return ONLY valid JSON. No explanations.`;
}

async function callLLM(provider: Provider, model: string, apiKey: string, userPrompt: string, sourceSchemas: { nodeId: string, label: string, schema: ColumnTypeDef[] }[]): Promise<string> {
  const systemPrompt = buildSystemPrompt(sourceSchemas);
  const fullPrompt = `${systemPrompt}\n\nUser request: ${userPrompt}`;

  if (provider.type === 'google') {
    const res = await fetch(`${provider.baseUrl}/${model}:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: fullPrompt }] }],
        generationConfig: { temperature: 0.1, responseMimeType: "application/json" }
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
    return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  }

  if (provider.type === 'anthropic') {
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
        max_tokens: 2000,
        messages: [{ role: 'user', content: fullPrompt }],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
    return data.content?.[0]?.text || '';
  }

  const res = await fetch(provider.baseUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + apiKey,
      ...(provider.extraHeaders || {}),
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: userPrompt }],
      response_format: { type: "json_object" },
      temperature: 0.1,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || JSON.stringify(data));
  return data.choices?.[0]?.message?.content || '';
}

interface Props {
  sourceSchemas: { nodeId: string, label: string, schema: ColumnTypeDef[] }[];
  onApplyPipeline: (nodes: Node[], edges: Edge[]) => void;
  onClose: () => void;
}

export default function AiPipelineBuilderPanel({ sourceSchemas, onApplyPipeline, onClose }: Props) {
  const [providerId, setProviderId] = useState(PROVIDERS[0].id);
  const [modelId, setModelId] = useState(PROVIDERS[0].models[0].id);
  const [customModelId, setCustomModelId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('');
  const [generatedJson, setGeneratedJson] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);

  const provider = PROVIDERS.find(p => p.id === providerId)!;
  const isCustomModel = modelId === CUSTOM_MODEL_OPTION.id;
  const effectiveModelId = isCustomModel ? customModelId : modelId;

  useEffect(() => {
    const stored = localStorage.getItem('ai_pipeline_key_' + providerId);
    setApiKey(stored || '');
    const firstModel = PROVIDERS.find(p => p.id === providerId)!.models[0].id;
    setModelId(firstModel);
    setCustomModelId('');
  }, [providerId]);

  const handleSaveKey = () => {
    if (apiKey) localStorage.setItem('ai_pipeline_key_' + providerId, apiKey);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (!apiKey.trim()) { setError('Please enter your API key.'); return; }
    if (isCustomModel && !customModelId.trim()) { setError('Please enter a custom model ID.'); return; }
    setIsGenerating(true); setError(null); setGeneratedJson('');
    try {
      const rawJson = await callLLM(provider, effectiveModelId, apiKey, prompt, sourceSchemas);
      // Clean up potential markdown
      const cleaned = rawJson.replace(/^\`\`\`(?:json)?\n/, '').replace(/\n\`\`\`$/, '').trim();
      // Validate JSON
      JSON.parse(cleaned);
      setGeneratedJson(cleaned);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally { setIsGenerating(false); }
  };

  const handleApply = () => {
    try {
      const pipeline = JSON.parse(generatedJson);
      if (pipeline.nodes && pipeline.edges) {
        onApplyPipeline(pipeline.nodes, pipeline.edges);
        setApplied(true);
        setTimeout(() => setApplied(false), 2000);
      } else {
        setError('Generated JSON is missing nodes or edges arrays.');
      }
    } catch (err) {
      setError('Invalid JSON format.');
    }
  };

  return (
    <div className="h-full flex flex-col bg-white border-l border-[#DFE1E6] shadow-xl w-[400px]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#DFE1E6] bg-[#FAFBFC]">
        <div className="flex items-center space-x-2 text-[#0052CC]">
          <Wand2 size={18} />
          <h2 className="text-sm font-bold text-[#171717]">AI Pipeline Builder</h2>
        </div>
        <button onClick={onClose} className="text-[#6B778C] hover:text-[#171717]">
          &times;
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 custom-scrollbar">
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

        <div>
          <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder={`Enter ${provider.name} API Key`}
              className="flex-1 border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC]"
            />
            <button onClick={handleSaveKey} className="px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md text-sm font-medium text-[#42526E] hover:bg-gray-50 transition-colors">
              Save
            </button>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-100 rounded-md p-3">
          <p className="text-xs text-blue-800 font-medium mb-1">Available Source Nodes:</p>
          {sourceSchemas.length === 0 ? (
            <p className="text-[11px] text-blue-600">No source nodes found or inspected yet. Add inputs and preview them first.</p>
          ) : (
            <ul className="text-[11px] text-blue-700 list-disc list-inside pl-3 space-y-1">
              {sourceSchemas.map(s => (
                <li key={s.nodeId}>
                  <span className="font-bold">{s.label}</span> ({s.schema.length} columns)
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-1.5">Describe your pipeline</label>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="e.g. Filter for age > 18, then group by department and calculate the average salary..."
            className="w-full h-28 border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-1 focus:ring-[#0052CC] focus:border-[#0052CC] resize-none"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim() || sourceSchemas.length === 0}
          className="w-full flex items-center justify-center space-x-2 py-2.5 bg-[#0052CC] text-white rounded-md text-sm font-bold hover:bg-[#0047B3] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? <RefreshCw size={16} className="animate-spin" /> : <Wand2 size={16} />}
          <span>{isGenerating ? 'Generating Pipeline...' : 'Generate Pipeline'}</span>
        </button>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start space-x-2">
            <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
            <span className="text-xs text-red-700 break-words">{error}</span>
          </div>
        )}

        {generatedJson && (
          <div className="space-y-3 pt-2 border-t border-[#DFE1E6]">
            <div className="flex items-center justify-between">
              <label className="block text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">Generated JSON</label>
              <button
                onClick={handleApply}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-colors ${applied ? 'bg-green-100 text-green-700 border border-green-200' : 'bg-[#EDEFFF] text-[#0052CC] hover:bg-[#DEE1FF]'}`}
              >
                {applied ? <CheckCheck size={14} /> : <Plus size={14} />}
                <span>{applied ? 'Applied!' : 'Apply to Canvas'}</span>
              </button>
            </div>
            <pre className="p-3 bg-[#1E1E2E] text-[#CDD6F4] text-[11px] rounded-md font-mono overflow-auto max-h-[300px] whitespace-pre-wrap">
              {generatedJson}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
