import React from 'react';
import { Node, Edge } from '@xyflow/react';
import { 
  SlidersHorizontal, PenLine, Trash2, Plus, Save, FileText, 
  Microscope, Globe, Repeat, Search, DatabaseBackup, Filter,
  ArrowRightLeft, Settings, Sigma, SortAsc, ListOrdered, Table,
  Calculator, Fingerprint, GitBranch, BarChart3, Dices, Braces, Code,
  Play, X, LayoutTemplate
} from 'lucide-react';
import { uploadFile, inspectNode, previewSql, generateReport, getBackendUrl } from '@/lib/api-unified';

interface PropertiesPanelProps {
  selectedNode: Node | null;
  setSelectedNode: React.Dispatch<React.SetStateAction<Node | null>>;
  nodes: Node[];
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>;
  edges: Edge[];
  setNodeSamples: React.Dispatch<React.SetStateAction<Record<string, any[]>>>;
  setNodeTypes: React.Dispatch<React.SetStateAction<Record<string, any[]>>>;
  setExecutionMessage: (msg: { title: string; detail: string; type: 'success' | 'error' | 'info' } | null) => void;
  setExecutionSuccess: (success: boolean) => void;
  setActiveBottomTab: (idx: number) => void;
  setIsBottomPanelVisible: (visible: boolean) => void;
  previewLimit: number;
  getUpstreamColumns: (nodeId: string) => string[];
}

// Internal SQL Preview component
const SqlPreview = ({ sql }: { sql: string }) => (
  <div className="mt-4 p-3 bg-[#091E42] rounded-md border border-[#253858] shadow-inner overflow-hidden">
    <div className="flex items-center justify-between mb-2">
      <span className="text-[10px] font-bold text-[#97A0AF] uppercase tracking-widest">Live SQL Preview</span>
      <Code size={12} className="text-[#4C9AFF]" />
    </div>
    <pre className="text-[10px] text-[#EAE6FF] font-mono whitespace-pre-wrap leading-relaxed">
      {sql}
    </pre>
  </div>
);

export function PropertiesPanel({ 
  selectedNode: node, 
  setSelectedNode,
  nodes, 
  setNodes,
  edges,
  setNodeSamples,
  setNodeTypes,
  setExecutionMessage,
  setExecutionSuccess,
  setActiveBottomTab,
  setIsBottomPanelVisible,
  previewLimit,
  getUpstreamColumns
}: PropertiesPanelProps) {
  const [saveSuccess, setSaveSuccess] = React.useState(false);
  const [customSqlPreviewResult, setCustomSqlPreviewResult] = React.useState<{ columns: string[], preview: any[] } | null>(null);

  if (!node) return null;

  const onUpdate = (updatedNode: Node) => {
    setSelectedNode(updatedNode);
    setNodes((nds) => nds.map((n) => (n.id === updatedNode.id ? updatedNode : n)));
  };

  const handleSave = () => {
    onUpdate(node);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const updateNodeData = (key: string, value: any) => {
    onUpdate({
      ...node,
      data: {
        ...node.data,
        [key]: value
      }
    });
  };

  const updateConfig = (key: string, value: any) => {
    const updatedNode = {
      ...node,
      data: {
        ...node.data,
        config: {
          ...(node.data.config as any || {}),
          [key]: value
        }
      }
    };
    onUpdate(updatedNode);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setExecutionMessage({ title: "Uploading...", detail: `Uploading ${file.name} to server.`, type: 'info' });
      setExecutionSuccess(true);
      
      const uploadResult = await uploadFile(file);
      
      const updatedNode = {
        ...node,
        data: {
          ...node.data,
          config: {
            ...(node.data.config as any || {}),
            file: uploadResult.filename,
            file_path: uploadResult.file_path,
            availableColumns: uploadResult.available_columns,
            format: uploadResult.detected_format,
            detectedFormat: uploadResult.detected_format,
            sheetNames: uploadResult.sheet_names,
            selectedSheet: uploadResult.sheet_names?.[0] || null
          }
        }
      };
      
      onUpdate(updatedNode);

      setNodes((nds) => nds.map((n) => {
        if (n.id === updatedNode.id) return updatedNode;
        // Automatically push column metadata to all filter nodes so dropdowns are ready
        if (n.type === 'default' || n.id.includes('Filter')) {
          return {
            ...n,
            data: {
              ...n.data,
              config: {
                ...(n.data.config as any || {}),
                availableColumns: uploadResult.available_columns
              }
            }
          };
        }
        return n;
      }));

      if (uploadResult.column_types) {
        setNodeTypes(prev => ({
          ...prev,
          [node.id]: uploadResult.column_types
        }));
      }

      // Fetch sample data
      try {
        const inspectResult = await inspectNode(
          nodes.map(n => n.id === node.id ? updatedNode : n),
          edges,
          node.id,
          previewLimit
        );

        if (inspectResult.node_samples) {
          setNodeSamples(prev => ({
            ...prev,
            [node.id]: inspectResult.node_samples
          }));
        }
      } catch (error) {
        console.error('Failed to fetch sample data after upload:', error);
      }

      setExecutionMessage({ 
        title: "File uploaded!", 
        detail: `${file.name} ready for analysis. Discovered ${uploadResult.available_columns?.length || 0} columns.`, 
        type: 'success' 
      });
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);

    } catch (err) {
      setExecutionMessage({ title: "File upload failed!", detail: String(err), type: 'error' });
      setExecutionSuccess(true);
      console.error(err);
    }
  };

  const handleInspect = async () => {
    try {
      setExecutionMessage({ title: "Connecting to server...", detail: `Fetching schema and samples for ${node.data?.label || 'node'}.`, type: 'info' });
      setExecutionSuccess(true);
      
      const res = await inspectNode(nodes, edges, node.id, previewLimit);
      
      if (res.node_samples) {
        setNodeSamples(prev => ({ ...prev, [node.id]: res.node_samples }));
      }
      
      if (res.columns) {
        setNodeTypes(prev => ({ ...prev, [node.id]: res.columns }));
      }
      
      setActiveBottomTab(0); // Data Inspection
      setIsBottomPanelVisible(true);
      setExecutionMessage({ 
        title: "Ready for Inspection", 
        detail: `Successfully loaded ${res.total_rows?.toLocaleString() || 0} rows.`, 
        type: 'success' 
      });
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
    } catch (e: any) {
      setExecutionMessage({ title: "Inspection failed.", detail: e.message || "Could not fetch data sample.", type: 'error' });
      setExecutionSuccess(true);
    }
  };

  // SQL Builder logic ported from page.tsx
  const buildSql = (type: string, config: any): string => {
    if (type === 'filter') {
      if (config.isAdvanced) return `SELECT * FROM <prev_table>\nWHERE ${config.customWhere || '/* condition */'}`;
      const val = isNaN(Number(config.value)) ? `'${config.value}'` : config.value;
      let op = config.operator || '==';
      if (op === '==') op = '=';
      if (op === 'contains') return `SELECT * FROM <prev_table>\nWHERE "${config.column}" LIKE '%${config.value}%'`;
      return `SELECT * FROM <prev_table>\nWHERE "${config.column}" ${op} ${val}`;
    }
    if (type === 'combine') {
      const joinType = (config.joinType || 'inner').toUpperCase();
      if (['UNION', 'UNION ALL'].includes(joinType)) {
        return `SELECT * FROM <input_1>\n${joinType}\nSELECT * FROM <input_2>`;
      }
      return `SELECT a.*, b.*\nFROM <input_1> a\n${joinType} JOIN <input_2> b\n  ON a."${config.leftColumn}" = b."${config.rightColumn}"`;
    }
    if (type === 'clean') {
      const action = config.action || 'trim';
      const col = config.column || 'col';
      if (action === 'trim') return `SELECT * EXCLUDE("${col}"),\n  TRIM("${col}") AS "${col}"\nFROM <prev_table>`;
      if (action === 'uppercase') return `SELECT * EXCLUDE("${col}"),\n  UPPER("${col}") AS "${col}"\nFROM <prev_table>`;
      if (action === 'lowercase') return `SELECT * EXCLUDE("${col}"),\n  LOWER("${col}") AS "${col}"\nFROM <prev_table>`;
      if (action === 'fill_null') return `SELECT * EXCLUDE("${col}"),\n  COALESCE("${col}", '${config.fillValue || ''}') AS "${col}"\nFROM <prev_table>`;
      return `SELECT * FROM <prev_table> -- ${action}`;
    }
    if (type === 'aggregate') {
      const op = (config.operation || 'count').toUpperCase();
      const col = config.column ? `"${config.column}"` : '*';
      const group = config.groupBy ? `"${config.groupBy}"` : '';
      return `SELECT ${group}${group ? ', ' : ''}${op}(${col}) AS result\nFROM <prev_table>${group ? `\nGROUP BY ${group}` : ''}`;
    }
    if (type === 'computed') {
      return `SELECT *,\n  ${config.expression || '/* expr */'} AS "${config.alias || 'new_col'}"\nFROM <prev_table>`;
    }
    if (type === 'select') {
      const cols = config.columns ? config.columns.split(',').map((c: string) => `"${c.trim()}"`).join(', ') : '*';
      return `SELECT ${cols}\nFROM <prev_table>`;
    }
    if (type === 'sort') {
      return `SELECT * FROM <prev_table>\nORDER BY "${config.column || 'col'}" ${(config.direction || 'asc').toUpperCase()}`;
    }
    if (type === 'limit') {
      return `SELECT * FROM <prev_table>\nLIMIT ${config.count || 100}`;
    }
    if (type === 'distinct') {
        const cols = config.columns ? config.columns.split(',').map((c: string) => `"${c.trim()}"`).join(', ') : '';
        return `SELECT DISTINCT ${cols || '*'} FROM <prev_table>`;
    }
    if (type === 'pivot') {
        return `PIVOT <prev_table>\nON "${config.pivot}"\nUSING FIRST("${config.value}")\nGROUP BY "${config.index}"`;
    }
    if (type === 'unpivot') {
        return `UNPIVOT <prev_table>\nON COLUMNS(*) EXCLUDE (${config.exclude || ''})\nINTO\n  NAME "${config.headerName || 'attribute'}"\n  VALUE "${config.valueName || 'value'}"`;
    }
    if (type === 'raw_sql') {
        return config.sql || 'SELECT * FROM <prev_table>';
    }
    if (type === 'case_when') {
        const conds = (config.conditions || []).map((c: any) => `    WHEN ${c.when} THEN ${c.then}`).join('\n');
        return `SELECT *,\n  CASE\n${conds}\n    ELSE ${config.elseValue || 'NULL'}\n  END AS "${config.alias || 'result'}"\nFROM <prev_table>`;
    }
    if (type === 'sample') {
        const amount = config.amount || 10;
        const method = config.sampleType === 'percent' ? `${amount}%` : `${amount} ROWS`;
        return `SELECT * FROM <prev_table>\nUSING SAMPLE ${method}`;
    }
    if (type === 'unnest') {
        return `SELECT *,\n  UNNEST("${config.column}")\nFROM <prev_table>`;
    }
    return 'SELECT * FROM <prev_table>';
  };

  const getConditionSql = (col: string, op: string, val: string) => {
    if (!col) return '';
    const formattedVal = isNaN(Number(val)) ? `'${val}'` : val;
    if (op === '==') return `"${col}" = ${formattedVal}`;
    if (op === '!=') return `"${col}" != ${formattedVal}`;
    if (op === '>') return `"${col}" > ${formattedVal}`;
    if (op === '<') return `"${col}" < ${formattedVal}`;
    if (op === '>=') return `"${col}" >= ${formattedVal}`;
    if (op === '<=') return `"${col}" <= ${formattedVal}`;
    if (op === 'contains') return `"${col}" LIKE '%${val}%'`;
    if (op === 'not_contains') return `"${col}" NOT LIKE '%${val}%'`;
    if (op === 'starts_with') return `"${col}" LIKE '${val}%'`;
    if (op === 'ends_with') return `"${col}" LIKE '%${val}'`;
    if (op === 'is_null') return `"${col}" IS NULL`;
    if (op === 'is_not_null') return `"${col}" IS NOT NULL`;
    if (op === 'in') return `"${col}" IN (${val})`;
    if (op === 'not_in') return `"${col}" NOT IN (${val})`;
    return '';
  };

  const renderInputConfig = () => {
    const subtype = node.data?.subtype as string | undefined;
    const config = (node.data?.config as any) || {};

    if (!subtype) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">File Upload</label>
            <label className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-[#DFE1E6] border-dashed rounded-md bg-[#FAFBFC] hover:border-[#0052CC] hover:bg-blue-50 transition-colors cursor-pointer relative">
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json,.jsonl,.parquet"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={handleFileUpload}
              />
              <div className="space-y-1 text-center">
                <FileText className="mx-auto h-8 w-8 text-[#6B778C]" />
                <div className="flex justify-center text-sm text-gray-600">
                  <span className="font-medium text-[#0052CC] hover:text-[#0065FF]">Upload a file</span>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">CSV/Excel/JSON/Parquet up to 1GB</p>
              </div>
            </label>
          </div>

          {config.sheetNames && config.sheetNames.length > 1 && (
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Select Sheet</label>
              <select
                value={config.selectedSheet || ''}
                onChange={(e) => updateConfig('selectedSheet', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              >
                {config.sheetNames.map((sheet: string) => (
                  <option key={sheet} value={sheet}>{sheet}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-[#6B778C]">Server Upload Path</label>
              <button
                onClick={handleInspect}
                className="text-[10px] font-bold text-[#0052CC] hover:bg-[#0052CC] hover:text-white px-2 py-0.5 rounded border border-[#0052CC]/20 transition-all"
              >
                INSPECT
              </button>
            </div>
            <input 
              type="text" 
              readOnly 
              value={config.file_path || "None uploaded"} 
              className="w-full bg-gray-50 border border-[#DFE1E6] rounded-md px-3 py-2 text-xs text-[#6B778C] font-mono" 
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">Parsing Format</label>
            <select
              value={config.format || 'flat'}
              onChange={(e) => updateConfig('format', e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
            >
              <option value="flat">Standard Flat CSV (Rows & Columns)</option>
              <option value="kv">Key-Value Pairs (id, key:val, timestamp)</option>
            </select>
          </div>
        </div>
      );
    }

    if (['sql_server', 'mysql', 'postgresql'].includes(subtype as string)) {
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">
              {subtype === 'sql_server' ? 'SQL Server' : 
               subtype === 'mysql' ? 'MySQL' : 'PostgreSQL'} Connection String
            </label>
            <input
              type="text"
              value={config.connection_string || ''}
              onChange={(e) => updateConfig('connection_string', e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              placeholder={
                subtype === 'sql_server' ? "DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=...;" :
                subtype === 'mysql' ? "mysql://user:password@host:port/database" :
                "postgresql://user:password@host:port/database"
              }
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">SQL Query</label>
            <textarea
              rows={4}
              value={config.query || ''}
              onChange={(e) => updateConfig('query', e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs font-mono"
              placeholder="SELECT * FROM table_name"
            />
          </div>
        </div>
      );
    }

    if (subtype === 'remote_file') {
      return (
        <div>
          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Remote URL (HTTP / S3)</label>
          <input
            value={config.url || ''}
            onChange={(e) => updateConfig('url', e.target.value)}
            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
            placeholder="https://... or s3://..."
          />
        </div>
      );
    }

    if (subtype === 'rest_api') {
      return (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">API URL</label>
            <input
              value={config.api_url || ''}
              onChange={(e) => updateConfig('api_url', e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              placeholder="https://api.example.com/data"
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Method</label>
              <select
                value={config.method || 'GET'}
                onChange={(e) => updateConfig('method', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Auth</label>
              <select
                value={config.auth_type || 'none'}
                onChange={(e) => updateConfig('auth_type', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              >
                <option value="none">None</option>
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="basic">Basic Auth</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#6B778C] mb-1">JSON Data Path</label>
            <input 
              value={config.data_path || ''} 
              onChange={(e) => updateConfig('data_path', e.target.value)} 
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm" 
              placeholder="e.g. data.items" 
            />
          </div>
        </div>
      );
    }

    if (subtype === 'web_scraper') {
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Web Page URL</label>
              <input value={config.web_url || ''} onChange={(e) => updateConfig('web_url', e.target.value)} className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm" placeholder="https://en.wikipedia.org/wiki/..." />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Extraction Mode</label>
              <select value={config.extract_mode || 'table'} onChange={(e) => updateConfig('extract_mode', e.target.value)} className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm">
                <option value="table">HTML Table</option>
                <option value="css">CSS Selector</option>
                <option value="xpath">XPath</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Selector</label>
              <input value={config.selector || 'table'} onChange={(e) => updateConfig('selector', e.target.value)} className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm" placeholder="table, .data-table, #results" />
            </div>
          </div>
        );
    }

    return null;
  };

  const renderTransformConfig = () => {
    const subtype = node.data?.subtype as string | undefined;
    const config = (node.data?.config as any) || {};
    const columns = getUpstreamColumns(node.id);

    if (subtype === 'filter') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-2">
            <label className="text-[10px] uppercase font-bold text-[#6B778C]">Filter Configuration</label>
            <button
              onClick={() => updateConfig('isAdvanced', !config.isAdvanced)}
              className={`text-[9px] px-2 py-0.5 rounded font-bold border transition-all ${
                config.isAdvanced ? 'bg-[#0052CC] text-white' : 'bg-white text-[#6B778C]'
              }`}
            >
              {config.isAdvanced ? 'SQL MODE' : 'SIMPLE'}
            </button>
          </div>

          {config.isAdvanced ? (
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Raw WHERE Clause</label>
              <textarea
                rows={3}
                placeholder="e.g. status = 'active' OR priority = 'high'"
                value={config.customWhere || ''}
                onChange={(e) => updateConfig('customWhere', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs font-mono"
              />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Column</label>
                <select
                  value={config.column || ''}
                  onChange={(e) => updateConfig('column', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                >
                  <option value="">Select col...</option>
                  {columns.map((col: string) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Operator</label>
                <select
                  value={config.operator || '=='}
                  onChange={(e) => updateConfig('operator', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                >
                  <option value="==">is equal to</option>
                  <option value="!=">is not equal to</option>
                  <option value=">">is greater than</option>
                  <option value="<">is less than</option>
                  <option value="contains">contains</option>
                  <option value="is_null">is null</option>
                </select>
              </div>
              {!['is_null', 'is_not_null'].includes(config.operator) && (
                <div>
                  <label className="block text-xs font-semibold text-[#6B778C] mb-1">Value</label>
                  <input
                    type="text"
                    value={config.value || ''}
                    onChange={(e) => updateConfig('value', e.target.value)}
                    className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                    placeholder="Filter value..."
                  />
                </div>
              )}
            </>
          )}
          <SqlPreview sql={buildSql('filter', config)} />
        </div>
      );
    }

    if (subtype === 'combine') {
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Merge Type</label>
              <select
                value={config.joinType || 'inner'}
                onChange={(e) => updateConfig('joinType', e.target.value)}
                className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
              >
                <optgroup label="Join">
                  <option value="inner">Inner Join</option>
                  <option value="left">Left Join</option>
                  <option value="right">Right Join</option>
                  <option value="full">Full Join</option>
                </optgroup>
                <optgroup label="Append">
                  <option value="union">Union</option>
                  <option value="union_all">Union All</option>
                </optgroup>
              </select>
            </div>
            {!['union', 'union_all'].includes(config.joinType) && (
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-bold text-[#6B778C] mb-1">Left Key</label>
                  <select
                    value={config.leftColumn || ''}
                    onChange={(e) => updateConfig('leftColumn', e.target.value)}
                    className="w-full border rounded px-2 py-1 text-xs"
                  >
                    <option value="">Select...</option>
                    {getUpstreamColumns(edges.find(e => e.target === node.id)?.source || '').map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-[#6B778C] mb-1">Right Key</label>
                  <select
                    value={config.rightColumn || ''}
                    onChange={(e) => updateConfig('rightColumn', e.target.value)}
                    className="w-full border rounded px-2 py-1 text-xs"
                  >
                    <option value="">Select...</option>
                    {getUpstreamColumns(edges.filter(e => e.target === node.id)[1]?.source || '').map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            )}
            <SqlPreview sql={buildSql('combine', config)} />
          </div>
        );
    }

    if (subtype === 'clean') {
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Column</label>
              <select value={config.column || ''} onChange={(e) => updateConfig('column', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                <option value="">Select...</option>
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Action</label>
              <select value={config.action || 'trim'} onChange={(e) => updateConfig('action', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                <option value="trim">Trim</option>
                <option value="uppercase">Uppercase</option>
                <option value="lowercase">Lowercase</option>
                <option value="fill_null">Fill Nulls</option>
              </select>
            </div>
            {config.action === 'fill_null' && (
              <input value={config.fillValue || ''} onChange={(e) => updateConfig('fillValue', e.target.value)} className="w-full border rounded px-3 py-2 text-sm" placeholder="Replacement value..." />
            )}
            <SqlPreview sql={buildSql('clean', config)} />
          </div>
        );
    }

    if (subtype === 'aggregate') {
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Group By</label>
              <select value={config.groupBy || ''} onChange={(e) => updateConfig('groupBy', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                <option value="">Grand Total (No group)</option>
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Metric</label>
                <select value={config.column || ''} onChange={(e) => updateConfig('column', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="">Count (*)</option>
                  {columns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Operation</label>
                <select value={config.operation || 'count'} onChange={(e) => updateConfig('operation', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="count">Count</option>
                  <option value="sum">Sum</option>
                  <option value="avg">Avg</option>
                  <option value="min">Min</option>
                  <option value="max">Max</option>
                </select>
              </div>
            </div>
            <SqlPreview sql={buildSql('aggregate', config)} />
          </div>
        );
    }

    if (subtype === 'computed') {
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Expression (SQL)</label>
              <textarea value={config.expression || ''} onChange={(e) => updateConfig('expression', e.target.value)} className="w-full border rounded px-3 py-2 text-xs font-mono" rows={3} placeholder="price * 1.1" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Alias</label>
              <input value={config.alias || ''} onChange={(e) => updateConfig('alias', e.target.value)} className="w-full border rounded px-3 py-2 text-sm" placeholder="new_column_name" />
            </div>
            <SqlPreview sql={buildSql('computed', config)} />
          </div>
        );
    }

    if (subtype === 'select') {
      return (
        <div>
          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Columns to Keep</label>
          <div className="border rounded p-2 max-h-40 overflow-y-auto space-y-1 bg-gray-50">
            {columns.map(c => {
                const isChecked = (config.columns || '').split(',').map((s:string)=>s.trim()).includes(c);
                return (
                    <label key={c} className="flex items-center gap-2 text-xs p-1 hover:bg-white rounded cursor-pointer">
                        <input 
                            type="checkbox" 
                            checked={isChecked} 
                            onChange={(e) => {
                                const list = (config.columns || '').split(',').map((s:string)=>s.trim()).filter((s:string)=>s);
                                const newList = e.target.checked ? [...list, c] : list.filter((s:string)=>s!==c);
                                updateConfig('columns', newList.join(', '));
                            }}
                        />
                        {c}
                    </label>
                );
            })}
          </div>
          <SqlPreview sql={buildSql('select', config)} />
        </div>
      );
    }

    if (subtype === 'sort') {
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Sort Column</label>
              <select value={config.column || ''} onChange={(e) => updateConfig('column', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                {columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#6B778C] mb-1">Order</label>
              <select value={config.direction || 'asc'} onChange={(e) => updateConfig('direction', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
            </div>
            <SqlPreview sql={buildSql('sort', config)} />
          </div>
        );
    }

    if (subtype === 'raw_sql') {
        return (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
                <label className="block text-xs font-semibold text-[#6B778C]">Raw SQL</label>
                <button 
                    onClick={async () => {
                        try {
                            setExecutionMessage({ title: "Running SQL...", detail: "Executing custom query", type: 'info' });
                            setExecutionSuccess(true);
                            const res = await previewSql(nodes, edges, node.id, config.sql, previewLimit);
                            if (res.preview) {
                                setCustomSqlPreviewResult({ columns: res.columns || [], preview: res.preview });
                                setExecutionMessage({ title: "Success", detail: `Loaded ${res.preview.length} rows.`, type: 'success' });
                            }
                        } catch(e: any) {
                            setExecutionMessage({ title: "SQL Error", detail: e.message, type: 'error' });
                        }
                    }}
                    className="text-[10px] font-bold text-[#0052CC] hover:bg-blue-50 px-2 py-0.5 rounded flex items-center gap-1"
                >
                    <Play size={10} /> RUN
                </button>
            </div>
            <textarea value={config.sql || ''} onChange={(e) => updateConfig('sql', e.target.value)} className="w-full border rounded p-2 text-[11px] font-mono" rows={8} />
            {customSqlPreviewResult && (
                <div className="border rounded overflow-hidden">
                    <div className="bg-gray-100 px-2 py-1 text-[9px] font-bold flex justify-between">
                        <span>PREVIEW</span>
                        <X size={10} className="cursor-pointer" onClick={() => setCustomSqlPreviewResult(null)} />
                    </div>
                    <div className="max-h-32 overflow-auto text-[9px]">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-white border-b">
                                    {customSqlPreviewResult.columns.map(c => <th key={c} className="p-1 text-left border-r">{c}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {customSqlPreviewResult.preview.slice(0, 5).map((r, i) => (
                                    <tr key={i} className="border-b">
                                        {customSqlPreviewResult.columns.map(c => <td key={c} className="p-1 border-r truncate max-w-[80px]">{String(r[c])}</td>)}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
          </div>
        );
    }

    if (subtype === 'case_when') {
        return (
          <div className="space-y-3">
            <label className="block text-xs font-semibold text-[#6B778C]">Conditions</label>
            {(config.conditions || []).map((c: any, i: number) => (
                <div key={i} className="p-2 border rounded bg-gray-50 space-y-2 relative group">
                    <button 
                        onClick={() => {
                            const list = [...config.conditions];
                            list.splice(i, 1);
                            updateConfig('conditions', list);
                        }}
                        className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 p-1 text-red-500"
                    ><Trash2 size={10} /></button>
                    <input value={c.when} onChange={(e) => {
                        const list = [...config.conditions];
                        list[i].when = e.target.value;
                        updateConfig('conditions', list);
                    }} className="w-full text-[10px] p-1 border rounded" placeholder="WHEN condition" />
                    <input value={c.then} onChange={(e) => {
                        const list = [...config.conditions];
                        list[i].then = e.target.value;
                        updateConfig('conditions', list);
                    }} className="w-full text-[10px] p-1 border rounded" placeholder="THEN result" />
                </div>
            ))}
            <button 
                onClick={() => {
                    const list = [...(config.conditions || [])];
                    list.push({ when: '', then: '' });
                    updateConfig('conditions', list);
                }}
                className="w-full py-1 text-[10px] border border-dashed border-[#0052CC] text-[#0052CC] rounded"
            >+ Add Condition</button>
            <input value={config.alias || ''} onChange={(e) => updateConfig('alias', e.target.value)} className="w-full border rounded px-3 py-2 text-sm" placeholder="Output Alias" />
            <SqlPreview sql={buildSql('case_when', config)} />
          </div>
        );
    }

    if (subtype === 'report') {
        return (
          <div className="space-y-4">
            <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Report Title</label>
                <input value={config.title || ''} onChange={(e) => updateConfig('title', e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div>
                <label className="block text-xs font-semibold text-[#6B778C] mb-1">Format</label>
                <select value={config.format || 'PDF'} onChange={(e) => updateConfig('format', e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                    <option value="PDF">PDF</option>
                    <option value="Markdown">Markdown</option>
                </select>
            </div>
            <button 
                onClick={async () => {
                    try {
                        const res = await generateReport(nodes, edges, config);
                        if (res.report_url) {
                          const link = document.createElement('a');
                          const baseUrl = getBackendUrl().replace(/\/$/, '');
                          link.href = res.report_url.startsWith('http') ? res.report_url : `${baseUrl}${res.report_url}`;
                          link.setAttribute('download', '');
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }
                    } catch(e) { console.error(e); }
                }}
                className="w-full py-2 bg-[#36B37E] text-white font-bold rounded flex items-center justify-center gap-2"
            >
                <FileText size={14} /> GENERATE
            </button>
          </div>
        );
    }

    return (
      <div className="p-3 bg-blue-50 border border-blue-100 rounded-md text-xs text-blue-700">
        Configuration for <span className="font-bold uppercase">{String(subtype)}</span> is being initialized.
        <SqlPreview sql={buildSql((subtype as string) || 'transform', config)} />
      </div>
    );
  };

  return (
    <aside className="w-80 bg-white border-l border-[#DFE1E6] flex flex-col h-full overflow-y-auto shadow-sm">
      <div className="p-4 border-b border-[#DFE1E6] bg-[#FAFBFC] flex items-center space-x-2 shrink-0">
        <SlidersHorizontal size={18} className="text-[#6B778C]" />
        <h2 className="text-sm font-semibold text-gray-800">Node Properties</h2>
      </div>

      <div className="p-4 flex-1">
        <h3 className="text-base font-medium text-[#171717] mb-6 flex items-center justify-between group border-b border-transparent hover:border-[#DFE1E6] focus-within:border-[#0052CC] transition-colors pb-1">
          <input
            type="text"
            value={String(node.data?.label || '')}
            onChange={(e) => updateNodeData('label', e.target.value)}
            className="flex-1 bg-transparent border-none focus:outline-none font-bold text-lg"
            placeholder="Node Label"
          />
          <PenLine size={14} className="text-[#6B778C] opacity-40 group-hover:opacity-100 transition-opacity" />
        </h3>

        <div className="space-y-6">
          <div>
            <label className="block text-[10px] uppercase font-bold text-[#6B778C] mb-2 tracking-wider">Node Metadata</label>
            <div className="space-y-2">
              <div className="flex items-center justify-between px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md">
                <span className="text-xs text-[#6B778C]">Type</span>
                <span className="text-xs font-semibold text-[#171717] capitalize">{String(node.type)} {node.data?.subtype ? `(${node.data.subtype})` : ''}</span>
              </div>
              {node.data?.rowCount !== undefined && (
                <div className="flex items-center justify-between px-3 py-2 bg-[#EAE6FF] border border-[#D1CAFF] rounded-md">
                  <span className="text-xs text-[#403294]">Rows</span>
                  <span className="text-xs font-bold text-[#403294]">{(node.data.rowCount as number).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-[#6B778C] mb-2 tracking-wider">Configuration</label>
            <div className="p-1">
              {node.type === 'input' && renderInputConfig()}
              {node.type === 'default' && renderTransformConfig()}
              {node.type === 'output' && renderTransformConfig()}
              {node.type === 'note' && (
                <textarea
                  value={String(node.data?.description || '')}
                  onChange={(e) => updateNodeData('description', e.target.value)}
                  className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm min-h-[200px] bg-[#FFFAE6] border-[#FFAB00]/30 focus:border-[#FFAB00] focus:ring-1 focus:ring-[#FFAB00]"
                  placeholder="Enter note content..."
                />
              )}
            </div>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-[#6B778C] mb-2 tracking-wider">Description</label>
            <textarea
              value={String(node.data?.description || '')}
              onChange={(e) => updateNodeData('description', e.target.value)}
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm min-h-[80px]"
              placeholder="Add internal notes about this node..."
            />
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-[#DFE1E6] bg-[#FAFBFC] shrink-0">
        <button
          onClick={handleSave}
          disabled={saveSuccess}
          className={`w-full px-4 py-2.5 text-white text-sm font-bold rounded-md shadow-sm transition-all flex items-center justify-center space-x-2 ${
            saveSuccess ? 'bg-[#36B37E] scale-95' : 'bg-[#0052CC] hover:bg-[#0065FF] active:scale-95'
          }`}
        >
          {saveSuccess ? <Fingerprint size={16} /> : <Save size={16} />}
          <span>{saveSuccess ? 'Saved Changes' : 'Save Changes'}</span>
        </button>
      </div>
    </aside>
  );
}
