'use client';
import React, { useState, useMemo } from 'react';
import { Copy, CheckCheck, RefreshCw, AlertCircle, Database } from 'lucide-react';

export interface ColumnTypeDef { column_name: string; column_type: string; }

export interface ColumnStats {
  column_name: string; column_type: string;
  count: number; distinct: number; null_count: number; null_pct: number;
  min?: string | number; max?: string | number; mean?: number; std?: number;
  q25?: string; q50?: string; q75?: string;
  top_value?: string; min_length?: number; max_length?: number;
}
export interface FullStats { total_rows: number; total_columns: number; columns: ColumnStats[]; }

interface Props {
  nodeId: string;
  nodeLabel: string;
  nodeSamples: Record<string, any[]>;
  nodeTypes: Record<string, ColumnTypeDef[]>;
  onFetchFullStats: (nodeId: string) => Promise<FullStats>;
}

function computeSampleStats(samples: any[], types: ColumnTypeDef[]): ColumnStats[] {
  if (!samples || samples.length === 0) return [];
  const total = samples.length;
  return types.map(({ column_name, column_type }) => {
    const values = samples.map(r => r[column_name]);
    const nonNull = values.filter(v => v !== null && v !== undefined && v !== '');
    const nullCount = total - nonNull.length;
    const distinct = new Set(nonNull.map(v => String(v))).size;
    const isNum = /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|BIGINT|HUGEINT|REAL/i.test(column_type);
    const isStr = /VARCHAR|TEXT|CHAR|STRING/i.test(column_type);
    let extra: Partial<ColumnStats> = {};
    if (isNum && nonNull.length > 0) {
      const nums = nonNull.map(v => parseFloat(String(v).replace(',', ''))).filter(n => !isNaN(n));
      if (nums.length > 0) {
        const sorted = [...nums].sort((a, b) => a - b);
        const mean = nums.reduce((a, b) => a + b, 0) / nums.length;
        const variance = nums.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / nums.length;
        extra = {
          min: sorted[0], max: sorted[sorted.length - 1],
          mean: Math.round(mean * 1000) / 1000,
          std: Math.round(Math.sqrt(variance) * 1000) / 1000,
          q25: String(sorted[Math.floor(sorted.length * 0.25)]),
          q50: String(sorted[Math.floor(sorted.length * 0.5)]),
          q75: String(sorted[Math.floor(sorted.length * 0.75)]),
        };
      }
    }
    if (isStr && nonNull.length > 0) {
      const lens = nonNull.map(v => String(v).length);
      const freq: Record<string, number> = {};
      nonNull.forEach(v => { const s = String(v); freq[s] = (freq[s] || 0) + 1; });
      const topValue = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0];
      extra = { min_length: Math.min(...lens), max_length: Math.max(...lens), top_value: topValue };
    }
    return { column_name, column_type, count: nonNull.length, distinct, null_count: nullCount, null_pct: Math.round((nullCount / total) * 1000) / 10, ...extra };
  });
}

interface Props {
  nodeId: string;
  nodeLabel: string;
  nodeSamples: Record<string, any[]>;
  nodeTypes: Record<string, ColumnTypeDef[]>;
  onFetchFullStats: (nodeId: string) => Promise<FullStats>;
}

export default function DataInspectionPanel({ nodeId, nodeLabel, nodeSamples, nodeTypes, onFetchFullStats }: Props) {
  const [activeTab, setActiveTab] = useState<'schema' | 'stats' | 'data'>('data');
  const [copied, setCopied] = useState<string | null>(null);
  const [fullStats, setFullStats] = useState<FullStats | null>(null);
  const [isLoadingFull, setIsLoadingFull] = useState(false);
  const [fullStatsError, setFullStatsError] = useState<string | null>(null);
  const [useFullStats, setUseFullStats] = useState(false);

  const samples = nodeSamples[nodeId] || [];
  const types = nodeTypes[nodeId] || [];

  const sampleStats = useMemo(() => computeSampleStats(samples, types), [samples, types]);
  const displayStats = useFullStats && fullStats ? fullStats.columns : sampleStats;

  const handleFetchFullStats = async () => {
    setIsLoadingFull(true); setFullStatsError(null);
    try {
      const res = await onFetchFullStats(nodeId);
      setFullStats(res);
      setUseFullStats(true);
    } catch (e: any) { setFullStatsError(e.message || "Failed to fetch full stats"); }
    finally { setIsLoadingFull(false); }
  };

  const handleCopy = (format: string) => {
    let text = "";
    if (format === 'md') {
      text = `| Column | Type |\n|---|---|\n` + types.map(t => `| ${t.column_name} | ${t.column_type} |`).join('\n');
    } else if (format === 'json') {
      text = JSON.stringify(types, null, 2);
    } else if (format === 'sql') {
      text = `CREATE TABLE ${nodeLabel.replace(/[^a-zA-Z0-9]/g, '_')} (\n  ` + types.map(t => `"${t.column_name}" ${t.column_type}`).join(',\n  ') + `\n);`;
    }
    navigator.clipboard.writeText(text);
    setCopied(format);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!nodeId) return (
    <div className="h-full flex flex-col items-center justify-center text-[#6B778C] bg-white p-8">
      <Database size={32} className="mb-3 opacity-20" />
      <p className="text-sm font-medium">Select a node to inspect its data.</p>
    </div>
  );

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white">
      <div className="flex border-b border-[#DFE1E6] bg-[#FAFBFC] px-4 shrink-0">
        {(['data', 'schema', 'stats'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`py-2 px-3 text-xs font-bold border-b-2 transition-colors mr-2 capitalize ${activeTab === t ? 'border-[#0052CC] text-[#0052CC]' : 'border-transparent text-[#6B778C] hover:text-[#171717]'}`}>
            {t === 'schema' ? 'Schema' : t === 'stats' ? 'Statistics' : 'Data Table'}
          </button>
        ))}
      </div>

      {samples.length === 0 && types.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-[#6B778C] bg-white p-8">
          <RefreshCw size={32} className="mb-3 opacity-20" />
          <p className="text-sm font-medium">Execute the workflow to inspect data.</p>
        </div>
      ) : (
        <>
          {activeTab === 'data' && (
        <div className="flex-1 overflow-auto p-4 custom-scrollbar">
          <div className="flex items-center justify-between mb-3">
             <div>
               <span className="text-xs font-bold text-[#6B778C] uppercase tracking-wider">Data Sample Preview</span>
               <div className="text-[10px] text-[#6B778C] mt-0.5">Showing {samples.length} sample rows</div>
             </div>
          </div>
          <div className="border border-[#DFE1E6] rounded-md overflow-hidden bg-white">
            <div className="overflow-x-auto overflow-y-auto max-h-[600px] custom-scrollbar">
              <table className="w-full text-left border-collapse min-w-full">
                <thead>
                  <tr className="bg-[#FAFBFC] sticky top-0 z-10 shadow-sm">
                    {types.map(t => (
                      <th key={t.column_name} className="px-3 py-2 text-[10px] font-bold text-[#6B778C] uppercase tracking-wider border-b border-[#DFE1E6] whitespace-nowrap bg-[#FAFBFC]">{t.column_name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DFE1E6]">
                  {samples.map((row, i) => (
                    <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                      {types.map(t => (
                        <td key={t.column_name} className="px-3 py-1.5 text-[11px] text-[#171717] font-mono whitespace-nowrap">{String(row[t.column_name] ?? '')}</td>
                      ))}
                    </tr>
                  ))}
                  {samples.length === 0 && (
                     <tr>
                       <td colSpan={types.length} className="px-3 py-8 text-center text-xs text-[#6B778C]">No sample data available.</td>
                     </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'schema' && (
        <div className="flex-1 overflow-auto p-4 custom-scrollbar">
          <div className="flex items-center justify-between mb-3">
            <div>
              <span className="text-xs font-bold text-[#6B778C] uppercase tracking-wider">Table Schema</span>
              <div className="text-[10px] text-[#6B778C] mt-0.5">{types.length} columns</div>
            </div>
            <div className="flex gap-1.5">
              {[['md', 'Markdown'], ['json', 'JSON'], ['sql', 'SQL DDL']].map(([fmt, label]) => (
                <button key={fmt} onClick={() => handleCopy(fmt)}
                  className={`flex items-center gap-1 px-2 py-1.5 text-[10px] font-bold rounded-md border transition-colors ${copied === fmt ? 'bg-[#36B37E] text-white border-[#36B37E]' : 'text-[#0052CC] bg-blue-50 hover:bg-blue-100 border-blue-200'}`}>
                  {copied === fmt ? <CheckCheck size={10} /> : <Copy size={10} />}
                  {copied === fmt ? 'Copied!' : label}
                </button>
              ))}
            </div>
          </div>
          <table className="w-full text-left border-collapse border border-[#DFE1E6] rounded-md overflow-hidden bg-white">
            <thead>
              <tr className="bg-[#FAFBFC]">
                {['Column', 'Type', 'Category'].map(h => (
                  <th key={h} className="px-3 py-2 text-[10px] font-bold text-[#6B778C] uppercase tracking-wider border-b border-[#DFE1E6] font-inter">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#DFE1E6]">
              {types.map((col, i) => {
                const isNum = /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|BIGINT|REAL/i.test(col.column_type);
                const isDate = /DATE|TIME|TIMESTAMP/i.test(col.column_type);
                const isBool = /BOOL/i.test(col.column_type);
                const cat = isNum ? 'Numeric' : isDate ? 'Date/Time' : isBool ? 'Boolean' : 'Text';
                const catColor = isNum ? 'bg-blue-50 text-blue-700' : isDate ? 'bg-purple-50 text-purple-700' : isBool ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600';
                return (
                  <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                    <td className="px-3 py-2 text-sm font-medium text-[#171717] font-mono">{col.column_name}</td>
                    <td className="px-3 py-2 text-xs text-[#6B778C] font-mono">{col.column_type}</td>
                    <td className="px-3 py-2"><span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${catColor}`}>{cat}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="flex-1 overflow-auto p-4 custom-scrollbar">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-xs font-bold text-[#6B778C] uppercase tracking-wider">Column Statistics</div>
              <div className="text-[10px] text-[#6B778C] mt-0.5">
                {useFullStats && fullStats ? `Full dataset · ${fullStats.total_rows.toLocaleString()} rows` : `Based on ${samples.length} sample rows`}
              </div>
            </div>
            <div className="flex gap-2">
              {useFullStats ? (
                <button onClick={() => { setUseFullStats(false); setFullStats(null); }} className="text-[10px] text-[#6B778C] hover:text-red-500 px-2 py-1 rounded border border-[#DFE1E6] hover:border-red-300 transition-colors font-bold">Reset to Sample</button>
              ) : (
                <button onClick={handleFetchFullStats} disabled={isLoadingFull}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold text-white bg-[#0052CC] hover:bg-[#0065FF] rounded-md transition-colors disabled:opacity-60 shadow-sm active:scale-95">
                  <RefreshCw size={10} className={isLoadingFull ? 'animate-spin' : ''} />
                  {isLoadingFull ? 'Computing…' : 'Full Dataset Analysis'}
                </button>
              )}
            </div>
          </div>
          {isLoadingFull && (
            <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-md flex items-center gap-2">
              <AlertCircle size={14} className="text-amber-600 shrink-0" />
              <p className="text-[11px] text-amber-700">Computing full statistics… This may take a moment for large datasets.</p>
            </div>
          )}
          {fullStatsError && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
              <AlertCircle size={14} className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-[11px] text-red-700 font-medium">{fullStatsError}</p>
            </div>
          )}
          <div className="space-y-2" data-testid="column-stats">
            {displayStats.map((stat, i) => {
              const isNum = /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|BIGINT|REAL/i.test(stat.column_type);
              const isStr = /VARCHAR|TEXT|CHAR|STRING/i.test(stat.column_type);
              return (
                <div key={i} className="p-3 border border-[#DFE1E6] rounded-md hover:border-[#0052CC]/30 hover:bg-blue-50/10 transition-all bg-white group">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-[#171717] font-mono group-hover:text-[#0052CC] transition-colors">{stat.column_name}</span>
                    <span className="text-[9px] font-bold text-[#6B778C] bg-gray-100 px-1.5 py-0.5 rounded uppercase">{stat.column_type}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {[
                      [String(stat.count), 'Non-Null', 'text-[#171717]'],
                      [String(stat.distinct), 'Distinct', 'text-[#6554C0]'],
                      [String(stat.null_count), 'Nulls', stat.null_count > 0 ? 'text-amber-600' : 'text-[#36B37E]'],
                      [String(stat.null_pct) + '%', 'Null %', stat.null_pct > 20 ? 'text-red-500' : stat.null_pct > 0 ? 'text-amber-600' : 'text-[#36B37E]'],
                    ].map(([val, label, color]) => (
                      <div key={label} className="text-center p-1.5 bg-[#FAFBFC] rounded border border-[#DFE1E6]" data-testid="stat-row">
                        <div className={`text-xs font-bold ${color}`} data-testid="stat-value">{val}</div>
                        <div className="text-[9px] text-[#6B778C] font-semibold" data-testid="stat-label">{label}</div>
                      </div>
                    ))}
                  </div>
                  {isNum && stat.min !== undefined && (
                    <div className="mt-2 grid grid-cols-5 gap-1">
                      {[['Min', stat.min], ['Q25', stat.q25], ['Median', stat.q50], ['Mean', stat.mean], ['Max', stat.max]].map(([lbl, val]) => (
                        <div key={String(lbl)} className="text-center p-1 bg-blue-50/50 rounded border border-blue-100">
                          <div className="text-[10px] font-bold text-blue-700 truncate">{String(val ?? '—')}</div>
                          <div className="text-[9px] text-[#6B778C] font-inter font-medium">{String(lbl)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {isStr && stat.top_value !== undefined && (
                    <div className="mt-2 text-[10px] text-[#6B778C] flex flex-wrap gap-3 p-1.5 bg-gray-50 rounded italic">
                      <span><b>Top:</b> <code className="bg-white border px-1 rounded not-italic text-[#171717]">{String(stat.top_value).substring(0, 40)}</code></span>
                      {stat.min_length !== undefined && <span><b>Length:</b> {stat.min_length}–{stat.max_length} chars</span>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
}
