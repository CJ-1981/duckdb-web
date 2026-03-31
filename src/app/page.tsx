"use client";

import React, { useState } from 'react';
import WorkspaceCanvas from '@/components/workflow/canvas';
import { Database, Filter, ArrowRightLeft, Table, Settings, Play, Download, Search, LayoutDashboard, SlidersHorizontal, FileText, FileDown, Save, FolderOpen, Sigma, Eye, ChevronDown, ChevronRight, SortAsc, ListOrdered, Calculator, Code, Fingerprint, PenLine, GitBranch, BarChart3, Plus, Trash2 } from 'lucide-react';
import { Node, useReactFlow, ReactFlowProvider } from '@xyflow/react';
import { executeWorkflow, uploadFile, saveWorkflow, listSavedWorkflows, loadWorkflowGraph } from '@/lib/api';

// ─── SQL Preview helpers ──────────────────────────────────────────────────────
function SqlPreview({ sql }: { sql: string }) {
  if (!sql) return null;
  return (
    <div className="mt-3">
      <label className="flex items-center gap-1.5 text-xs font-semibold text-[#6B778C] mb-1">
        <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
        Generated SQL Preview
      </label>
      <pre className="bg-[#1E1E2E] text-[#CDD6F4] text-[11px] rounded-md p-3 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">{sql}</pre>
    </div>
  );
}

function buildSql(subtype: string, cfg: any): string {
  const T = '<prev_table>';
  switch (subtype) {
    case 'filter': {
      const col = cfg?.column ? `"${cfg.column}"` : '/* column */';
      const op = cfg?.operator || '==';
      const val = String(cfg?.value || '');
      const opMap: Record<string, string> = {
        '==': `${col} = '${val}'`, '!=': `${col} != '${val}'`,
        '>': `${col} > ${val}`, '<': `${col} < ${val}`,
        '>=': `${col} >= ${val}`, '<=': `${col} <= ${val}`,
        'contains': `${col} ILIKE '%${val}%'`,
        'not_contains': `${col} NOT ILIKE '%${val}%'`,
        'starts_with': `${col} ILIKE '${val}%'`,
        'ends_with': `${col} ILIKE '%${val}'`,
        'is_null': `${col} IS NULL`, 'is_not_null': `${col} IS NOT NULL`,
        'in': `${col} IN (${val})`, 'not_in': `${col} NOT IN (${val})`,
      };
      return `SELECT *\nFROM ${T}\nWHERE ${opMap[op] ?? `${col} ${op} '${val}'`}`;
    }
    case 'combine': {
      const jt = (cfg?.joinType || 'inner').toUpperCase();
      const lc = cfg?.leftColumn ? `"${cfg.leftColumn}"` : '/* left_key */';
      const rc = cfg?.rightColumn ? `"${cfg.rightColumn}"` : '/* right_key */';
      return `SELECT *\nFROM <left_table>\n${jt} JOIN <right_table>\n  ON <left_table>.${lc} = <right_table>.${rc}`;
    }
    case 'clean': {
      const col = cfg?.column || '/* column */';
      const op = cfg?.operation || 'trim';
      const exprMap: Record<string, string> = {
        trim: `TRIM(CAST("${col}" AS VARCHAR))`,
        upper: `UPPER(CAST("${col}" AS VARCHAR))`,
        lower: `LOWER(CAST("${col}" AS VARCHAR))`,
        numeric: `REGEXP_REPLACE(CAST("${col}" AS VARCHAR), '[^0-9.]', '', 'g')`,
        replace_null: `COALESCE(NULLIF(CAST("${col}" AS VARCHAR), ''), '${cfg?.newValue || ''}')`,
        to_date: `TRY_CAST("${col}" AS DATE)`,
      };
      return `SELECT * REPLACE (\n  ${exprMap[op] ?? `"${col}"`} AS "${col}"\n)\nFROM ${T}`;
    }
    case 'aggregate': {
      const groups = (cfg?.groupBy || '').split(',').map((c: string) => c.trim()).filter(Boolean);
      const aggs: any[] = cfg?.aggregations || [];
      const aggParts = aggs.length
        ? aggs.map((a: any) => `${(a.operation || 'COUNT').toUpperCase()}("${a.column || '*'}") AS "${a.alias || 'agg'}"`)
        : ['COUNT(*) AS count_all'];
      const sel = [...groups.map((c: string) => `"${c}"`), ...aggParts].join(',\n  ');
      const gb = groups.length ? `\nGROUP BY ${groups.map((c: string) => `"${c}"`).join(', ')}` : '';
      return `SELECT\n  ${sel}\nFROM ${T}${gb}`;
    }
    case 'sort': {
      const col = cfg?.column ? `"${cfg.column}"` : '/* column */';
      const dir = (cfg?.direction || 'asc').toUpperCase();
      return `SELECT *\nFROM ${T}\nORDER BY ${col} ${dir}`;
    }
    case 'limit':
      return `SELECT *\nFROM ${T}\nLIMIT ${cfg?.count || 100}`;
    case 'select': {
      const cols = (cfg?.columns || '').split(',').map((c: string) => `"${c.trim()}"`).filter((c: string) => c !== '""');
      return `SELECT ${cols.length ? cols.join(', ') : '*'}\nFROM ${T}`;
    }
    case 'computed': {
      const expr = cfg?.expression || '/* expression */';
      const alias = cfg?.alias || 'new_column';
      return `SELECT *,\n  ${expr} AS "${alias}"\nFROM ${T}`;
    }
    case 'rename': {
      const maps: any[] = cfg?.mappings || [];
      const items = maps.filter((m: any) => m.old && m.new).map((m: any) => `"${m.old}" AS "${m.new}"`);
      return `SELECT * REPLACE (\n  ${items.length ? items.join(',\n  ') : '/* add mappings */'}\n)\nFROM ${T}`;
    }
    case 'distinct': {
      const cols = (cfg?.columns || '').split(',').map((c: string) => `"${c.trim()}"`).filter((c: string) => c !== '""');
      return `SELECT DISTINCT ${cols.length ? cols.join(', ') : '*'}\nFROM ${T}`;
    }
    case 'case_when': {
      const conds: any[] = cfg?.conditions || [];
      const alias = cfg?.alias || 'case_result';
      const elsePart = cfg?.elseValue || 'NULL';
      const whenLines = conds.filter((c: any) => c.when && c.then)
        .map((c: any) => `  WHEN ${c.when} THEN '${c.then}'`).join('\n') || '  WHEN /* condition */ THEN /* value */';
      return `SELECT *,\n  CASE\n${whenLines}\n  ELSE ${elsePart}\n  END AS "${alias}"\nFROM ${T}`;
    }
    case 'raw_sql':
      return cfg?.sql ? cfg.sql.replace(/\{\{input\}\}/g, T) : `SELECT * FROM ${T}`;
    default:
      return '';
  }
}
// ─────────────────────────────────────────────────────────────────────────────

function ExecuteButton() {
  const { getNodes, getEdges, setNodes } = useReactFlow();

  const handleExecute = async () => {
    try {
      const nodes = getNodes();
      const edges = getEdges();
      console.log('--- Workflow Execution Start ---');
      console.log('Nodes structure:', JSON.stringify(nodes, null, 2));
      console.log('Executing workflow with', nodes.length, 'nodes');
      const result = await executeWorkflow(nodes, edges);
      
      // Update any filter nodes with the discovered columns so the user can select them
      if (result.columns) {
        setNodes((nds) => nds.map((node) => {
          if (node.id.includes('Filter') || node.type === 'default') {
            return {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...(node.data.config as any || {}),
                  availableColumns: result.columns
                }
              }
            };
          }
          return node;
        }));
      }

      alert(`Success! processed ${result.row_count} rows.`);
      
      // If there's an export file, trigger browser download
      if (result.export_url) {
        const downloadUrl = `http://localhost:8000${result.export_url}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        console.log('Export triggered for:', downloadUrl);

        // Update the output node in the UI to show the new path
        setNodes((nds) => nds.map((node) => {
          if (node.type === 'output') {
            return {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...(node.data.config as any || {}),
                  file_path: result.export_url
                }
              }
            };
          }
          return node;
        }));
      }

      console.log('Preview data:', result.preview);
    } catch (error) {
      console.error(error);
      alert('Execution failed. Trace: ' + (error instanceof Error ? error.message : String(error)));
    }
  };

  return (
    <button 
      onClick={handleExecute}
      className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-[#0052CC] hover:bg-[#0065FF] rounded-md transition-colors shadow-sm"
    >
      <Play size={16} fill="currentColor" />
      <span>Execute Workflow</span>
    </button>
  );
}

function Dashboard() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const { setNodes, setEdges, getNodes, getEdges } = useReactFlow();
  
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [isLoadModalOpen, setIsLoadModalOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState("");
  const [availableWorkflows, setAvailableWorkflows] = useState<string[]>([]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [previewHeight, setPreviewHeight] = useState(280);
  const [previewLimit, setPreviewLimit] = useState(50);
  const [nodeSamples, setNodeSamples] = useState<Record<string, any[]>>({});

  // Auto-initialize column selections if empty to avoid [SKIP] in backend
  React.useEffect(() => {
    if (selectedNode && selectedNode.data?.subtype) {
      const subtype = selectedNode.data.subtype;
      const config = selectedNode.data.config as any;
      
      // Helper to find all available columns for this node (redundant but matches current logic)
      const nodes = getNodes();
      const edges = getEdges();
      
      const getNodeOutputColumnsLocal = (nId: string, visited = new Set<string>()): string[] => {
        if (visited.has(nId)) return [];
        visited.add(nId);
        const node = nodes.find(n => n.id === nId);
        if (!node) return [];
        const cfg = node.data?.config as any;
        const sub = node.data?.subtype;
        if (sub === 'aggregate') {
          const groupBy = (cfg?.groupBy || "").split(',').map((c: string) => c.trim()).filter((c: string) => c);
          const op = cfg?.operation || 'sum';
          const col = cfg?.column || '';
          const alias = cfg?.alias || (col ? `${op}_${col}` : (cfg?.groupBy ? '' : 'count_all'));
          const predicted = [...groupBy];
          if (alias) predicted.push(alias);
          return predicted;
        }
        if (sub === 'select') {
          return (cfg?.columns || "").split(',').map((c: string) => c.trim()).filter((c: string) => c);
        }
        if (node.type === 'input') return cfg?.columns || [];
        const preds = edges.filter(e => e.target === nId).map(e => e.source);
        const allCols = new Set<string>();
        preds.forEach(pId => getNodeOutputColumnsLocal(pId, visited).forEach(c => allCols.add(c)));
        return Array.from(allCols);
      };

      const columns = getNodeOutputColumnsLocal(selectedNode.id);
      
      if (columns.length > 0) {
        let updatedConfig: any = null;
        
        // Handle standard 'column' picks
        if (['filter', 'aggregate', 'sort', 'clean'].includes(subtype as string) && !config?.column) {
          updatedConfig = { ...(config || {}), column: columns[0] };
        }
        
        // Handle Join keys
        if (subtype === 'combine' && (!config?.leftColumn || !config?.rightColumn)) {
          updatedConfig = { 
            ...(config || {}), 
            leftColumn: config?.leftColumn || columns[0],
            rightColumn: config?.rightColumn || columns[0]
          };
        }

        // Handle computed, window, case_when defaults
        if (subtype === 'computed' && !config?.alias) {
          updatedConfig = { ...(config || {}), alias: 'new_column' };
        }
        if (subtype === 'window' && !config?.alias) {
          updatedConfig = { ...(config || {}), function: 'ROW_NUMBER', alias: 'row_idx' };
        }

        if (updatedConfig) {
          const updatedNode = { 
            ...selectedNode, 
            data: { ...selectedNode.data, config: updatedConfig } 
          };
          setSelectedNode(updatedNode);
          setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
        }
      }
    }
  }, [selectedNode?.id, getNodes, getEdges]);

  const handleSaveWorkflow = async () => {
    if (!workflowName) return;
    try {
      await saveWorkflow(workflowName, getNodes(), getEdges());
      alert("Pipeline saved!");
      setIsSaveModalOpen(false);
      setWorkflowName("");
    } catch (e) { alert("Save failed."); console.error(e); }
  };

  const handleLoadWorkflow = async (name: string) => {
    try {
      const data = await loadWorkflowGraph(name);
      // Strip any legacy 'className' that causes double-rendering
      const sanitizedNodes = (data.nodes || []).map((n: any) => {
        const { className, ...rest } = n;
        return rest;
      });
      setNodes(sanitizedNodes);
      setEdges(data.edges || []);
      setIsLoadModalOpen(false);
    } catch (e) { alert("Load failed."); console.error(e); }
  };

  const openLoadModal = async () => {
    try {
      const { workflows } = await listSavedWorkflows();
      setAvailableWorkflows(workflows || []);
      setIsLoadModalOpen(true);
    } catch (e) { alert("Error fetching workflows."); }
  };

  const getUpstreamColumns = (nodeId: string) => {
    const nodes = getNodes();
    const edges = getEdges();
    
    const getNodeOutputColumns = (nId: string, visited = new Set<string>()): string[] => {
      if (visited.has(nId)) return [];
      visited.add(nId);
      
      const node = nodes.find(n => n.id === nId);
      if (!node) return [];

      const config = node.data?.config as any;
      const subtype = node.data?.subtype;

      // 1. If it's an aggregate node, it creates a new schema
      if (subtype === 'aggregate') {
        const predictedCols = new Set<string>();
        const groupBy = (config?.groupBy || "").split(',').map((c: string) => c.trim()).filter((c: string) => c);
        groupBy.forEach((c: string) => predictedCols.add(c));

        const aggs = config?.aggregations || [];
        if (aggs.length > 0) {
          aggs.forEach((a: any) => { if (a.alias) predictedCols.add(a.alias); });
        } else {
          const op = config?.operation || 'sum';
          const col = config?.column || '';
          const alias = config?.alias || (col ? `${op}_${col}` : (config?.groupBy ? '' : 'count_all'));
          if (alias) predictedCols.add(alias);
        }
        
        if (Array.isArray(config?.availableColumns) && config.availableColumns.length > 0) {
           return config.availableColumns;
        }
        return Array.from(predictedCols) as string[];
      }

      // 1b. Schema modifiers
      if (['computed', 'window', 'case_when'].includes(subtype as string)) {
        const upstream = edges.filter(e => e.target === nId).map(e => getNodeOutputColumns(e.source, visited)).flat();
        const predicted = new Set(upstream);
        if (config?.alias) predicted.add(config.alias);
        return Array.from(predicted);
      }

      if (subtype === 'rename') {
        const upstream = edges.filter(e => e.target === nId).map(e => getNodeOutputColumns(e.source, visited)).flat();
        const mapped = new Set<string>();
        const renames = config?.mappings || [];
        const oldToNew = Object.fromEntries(renames.map((r: any) => [r.old, r.new]));
        upstream.forEach(c => mapped.add(oldToNew[c] || c));
        return Array.from(mapped);
      }

      // 2. Select node reduction
      if (subtype === 'select') {
         const cols = (config?.columns || "").split(',').map((c: string) => c.trim()).filter((c: string) => c);
         if (cols.length > 0) return cols;
      }

      // 2. If it's an input node, use its columns
      if (node.type === 'input') {
        return config?.availableColumns || [];
      }

      // 3. Otherwise (Filter, Clean, etc.), trace upstream
      const incoming = edges.filter(e => e.target === nId);
      const upstreamCols = new Set<string>();
      for (const edge of incoming) {
        getNodeOutputColumns(edge.source, visited).forEach(c => upstreamCols.add(c));
      }
      
      // If we have real columns from execution, they are most accurate
      if (Array.isArray(config?.availableColumns) && config.availableColumns.length > 0) {
        return config.availableColumns;
      }
      
      return Array.from(upstreamCols);
    };

    const incoming = edges.filter(e => e.target === nodeId);
    const columns = new Set<string>();
    for (const edge of incoming) {
      getNodeOutputColumns(edge.source).forEach(c => columns.add(c));
    }
    return Array.from(columns);
  };

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string, subtype?: string) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ type: nodeType, label, subtype }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const saveNodeChanges = () => {
    if (!selectedNode) return;
    setNodes((nds) => 
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          node.data = { ...selectedNode.data };
        }
        return node;
      })
    );
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      const result = await executeWorkflow(getNodes(), getEdges(), previewLimit);
      setExecutionResult(result);
      if (result.node_samples) {
        setNodeSamples(result.node_samples);
      }
      
      setNodes((nds) => nds.map(node => ({
        ...node,
        data: {
            ...node.data,
            rowCount: result.node_counts?.[node.id] ?? result.row_count,
            config: {
              ...(node.data.config as any || {}),
              availableColumns: result.node_columns?.[node.id] ?? (node.data.config as any)?.availableColumns
            }
        }
      })));

      alert(`Success! Processed ${result.row_count} rows.`);
    } catch (e) {
      alert("Execution failed.");
      console.error(e);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleBeautify = () => {
     const nodes = getNodes();
     const edges = getEdges();
     
     if (nodes.length === 0) return;

     // 1. Calculate node depths (layered DAG approach)
     const depths: Record<string, number> = {};
     const incoming = (nodeId: string) => edges.filter(e => e.target === nodeId);
     
     // Initialize depths
     nodes.forEach(n => depths[n.id] = 0);

     // Iteratively assign depths (multi-pass to handle multi-step dependencies)
     let changed = true;
     for (let i = 0; i < nodes.length && changed; i++) {
        changed = false;
        nodes.forEach(node => {
           const predecessors = incoming(node.id);
           if (predecessors.length > 0) {
              const maxPrevDepth = Math.max(...predecessors.map(e => depths[e.source]));
              if (depths[node.id] !== maxPrevDepth + 1) {
                 depths[node.id] = maxPrevDepth + 1;
                 changed = true;
              }
           }
        });
     }

     // 2. Group nodes by depth for horizontal centering
     const depthGroups: Record<number, string[]> = {};
     Object.entries(depths).forEach(([id, depth]) => {
        if (!depthGroups[depth]) depthGroups[depth] = [];
        depthGroups[depth].push(id);
     });

     // 3. Update node positions
     const HORIZONTAL_GAP = 280;
     const VERTICAL_GAP = 180;
     const CANVAS_CENTER_X = 400; // Arbitrary center

     const newNodes = nodes.map(node => {
        const depth = depths[node.id];
        const group = depthGroups[depth];
        const indexInGroup = group.indexOf(node.id);
        const totalInGroup = group.length;

        // Spread nodes horizontally within each depth level
        const xOffset = (indexInGroup - (totalInGroup - 1) / 2) * HORIZONTAL_GAP;
        
        return {
           ...node,
           position: {
              x: CANVAS_CENTER_X + xOffset,
              y: 50 + depth * VERTICAL_GAP
           }
        };
     });

     setNodes(newNodes);
  };
   
  return (
    <div className="flex flex-col h-screen bg-[#FAFBFC] overflow-hidden text-[#171717]">
      {/* Top Header */}
      <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-[#DFE1E6] shrink-0">
        <div className="flex items-center space-x-4">
          <div className="p-2 bg-[#0052CC] text-white rounded-md">
            <LayoutDashboard size={20} />
          </div>
          <h1 className="text-xl font-bold text-[#171717]">
            Data Analyst Platform
          </h1>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-md border border-[#DFE1E6]">
            <Eye size={14} className="text-[#6B778C]" />
            <span className="text-xs font-semibold text-[#6B778C]">Preview:</span>
            <select 
              value={previewLimit}
              onChange={(e) => setPreviewLimit(Number(e.target.value))}
              className="bg-transparent text-xs font-bold text-[#171717] focus:outline-none border-none cursor-pointer"
            >
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
              <option value={200}>200 rows</option>
              <option value={500}>500 rows</option>
              <option value={1000}>1000 rows</option>
            </select>
          </div>

          <button 
            onClick={handleBeautify}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#0052CC] bg-white border border-[#0052CC]/30 hover:bg-blue-50 rounded-md transition-colors"
          >
            <SlidersHorizontal size={16} />
            <span>Beautify Layout</span>
          </button>
          <button 
            onClick={() => setIsSaveModalOpen(true)}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors"
          >
            <Save size={16} />
            <span>Save Pipeline</span>
          </button>
          <button 
            onClick={openLoadModal}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors"
          >
            <FolderOpen size={16} />
            <span>Open</span>
          </button>
          <button 
            onClick={handleExecute}
            disabled={isExecuting}
            className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white rounded-md transition-colors shadow-sm ${isExecuting ? 'bg-gray-400' : 'bg-[#0052CC] hover:bg-[#0065FF]'}`}
          >
            <Play size={16} fill="currentColor" />
            <span>{isExecuting ? 'Running...' : 'Execute Workflow'}</span>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Component Palette */}
        <aside className="w-64 bg-white border-r border-[#DFE1E6] flex flex-col overflow-y-auto">
          <div className="p-4 border-b border-[#DFE1E6]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-[#6B778C]" size={16} />
              <input 
                type="text" 
                placeholder="Search components..." 
                className="w-full pl-9 pr-4 py-2 text-sm border border-[#DFE1E6] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0052CC] focus:border-transparent"
              />
            </div>
          </div>
          
          <div className="flex-1 p-4">
            <h3 className="text-xs font-semibold text-[#6B778C] uppercase tracking-wider mb-3">Data Sources</h3>
            <div className="space-y-2 mb-6">
              <div draggable onDragStart={(e) => onDragStart(e, 'input', 'Database Table')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#0052CC] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-blue-50 text-[#0052CC] rounded">
                  <Database size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Database Table</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'input', 'CSV/Excel File')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#0052CC] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-blue-50 text-[#0052CC] rounded">
                  <Table size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">CSV/Excel File</span>
              </div>
            </div>

            <h3 className="text-xs font-semibold text-[#6B778C] uppercase tracking-wider mb-3">Transformations</h3>
            <div className="space-y-2 mb-6">
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Filter Records', 'filter')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Filter size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Filter Records</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Combine Datasets', 'combine')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <ArrowRightLeft size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Combine Datasets</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Clean & Format', 'clean')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Settings size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Clean & Format</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Aggregate Data', 'aggregate')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Sigma size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Aggregate Data</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Sort Data', 'sort')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <SortAsc size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Sort Data</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Limit Data', 'limit')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <ListOrdered size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Limit Data</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Select Columns', 'select')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Table size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Select Columns</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Add Column', 'computed')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Calculator size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Add Column</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Rename Columns', 'rename')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <PenLine size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Rename Columns</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Remove Duplicates', 'distinct')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Fingerprint size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Remove Duplicates</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Conditional Logic', 'case_when')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <GitBranch size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Conditional Logic</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Window Function', 'window')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <BarChart3 size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Window Function</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Custom SQL', 'raw_sql')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Code size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Custom SQL</span>
              </div>
            </div>
            
            <h3 className="text-xs font-semibold text-[#6B778C] uppercase tracking-wider mb-3">Outputs</h3>
            <div className="space-y-2 mb-6">
              <div draggable onDragStart={(e) => onDragStart(e, 'output', 'Export File')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#36B37E] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-green-50 text-[#36B37E] rounded">
                  <FileDown size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Export file</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Canvas Area */}
        <main className="flex-1 relative flex flex-col h-[calc(100vh-4rem)]">
          <WorkspaceCanvas onNodeSelect={setSelectedNode} />
        </main>

        {/* Right Sidebar - Properties Panel */}
        {selectedNode && (
          <aside className="w-80 bg-white border-l border-[#DFE1E6] flex flex-col overflow-y-auto">
            <div className="p-4 border-b border-[#DFE1E6] bg-[#FAFBFC] flex items-center space-x-2">
              <SlidersHorizontal size={18} className="text-[#6B778C]" />
              <h2 className="text-sm font-semibold text-gray-800">Node Properties</h2>
            </div>
            <div className="p-4 flex-1">
              <h3 className="text-base font-medium text-[#171717] mb-2 flex items-center justify-between">
                <input 
                  type="text" 
                  value={String(selectedNode.data?.label || '')} 
                  onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: e.target.value } })}
                  className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 p-0 font-medium text-lg placeholder-gray-400"
                  placeholder="Node Label"
                />
                {selectedNode.data?.rowCount !== undefined && (
                  <span className="ml-2 text-[10px] bg-[#EAE6FF] text-[#403294] px-2 py-0.5 rounded-full font-bold whitespace-nowrap">
                    {String(selectedNode.data.rowCount)} rows
                  </span>
                )}
              </h3>
              
              {selectedNode && selectedNode.type === 'input' && typeof selectedNode.data?.config === 'object' && selectedNode.data.config !== null && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">File Upload</label>
                    <label className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-[#DFE1E6] border-dashed rounded-md bg-[#FAFBFC] hover:border-[#0052CC] hover:bg-blue-50 transition-colors cursor-pointer relative">
                      <input 
                        type="file" 
                        accept=".csv,.xlsx"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        onChange={async (e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                             try {
                                const uploadResult = await uploadFile(file);
                                const updatedNode = { 
                                  ...selectedNode, 
                                  data: { 
                                    ...selectedNode.data, 
                                    config: { 
                                      ...(selectedNode.data.config as any), 
                                      file: uploadResult.filename, 
                                      file_path: uploadResult.file_path,
                                      availableColumns: uploadResult.available_columns
                                    } 
                                  } 
                                };
                                setSelectedNode(updatedNode);
                                // Automatically push column metadata to all filter nodes so dropdowns are ready
                                setNodes((nds) => nds.map((n) => {
                                  if (n.id === updatedNode.id) return updatedNode;
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
                             } catch (err) {
                                alert("File upload failed!");
                                console.error(err);
                             }
                          }
                        }}
                      />
                      <div className="space-y-1 text-center">
                        <FileText className="mx-auto h-8 w-8 text-[#6B778C]" />
                        <div className="flex justify-center text-sm text-gray-600">
                          <span className="font-medium text-[#0052CC] hover:text-[#0065FF]">Upload a file</span>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">CSV up to 1GB</p>
                      </div>
                    </label>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Server Upload Path</label>
                    <input type="text" readOnly value={String((selectedNode.data.config as Record<string, unknown>)?.file_path || "None uploaded")} className="w-full bg-gray-50 border border-[#DFE1E6] rounded-md px-3 py-2 text-xs text-[#6B778C] font-mono" />
                  </div>
                </div>
              )}

              {selectedNode.type === 'default' && typeof selectedNode.data?.config === 'object' && selectedNode.data.config !== null && (
                <div className="space-y-4">
                  {/* Filter Records UI */}
                  {selectedNode.data.subtype === 'filter' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Column to Filter</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.column || '')} 
                          onChange={(e) => {
                            const updatedNode = { 
                              ...selectedNode, 
                              data: { 
                                ...selectedNode.data, 
                                config: { 
                                  ...(selectedNode.data.config as any), 
                                  column: e.target.value
                                } 
                              } 
                            };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          {getUpstreamColumns(selectedNode.id).map((col: string) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Condition</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.operator || '==')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), operator: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="==">is equal to</option>
                          <option value="!=">is not equal to</option>
                          <option value=">">is greater than</option>
                          <option value="<">is less than</option>
                          <option value=">=">is greater or equal</option>
                          <option value="<=">is less or equal</option>
                          <option value="contains">contains</option>
                          <option value="not_contains">does not contain</option>
                          <option value="starts_with">starts with</option>
                          <option value="ends_with">ends with</option>
                          <option value="is_null">is empty / null</option>
                          <option value="is_not_null">is not empty</option>
                          <option value="in">is in list (a,b,c)</option>
                          <option value="not_in">is NOT in list (a,b,c)</option>
                        </select>
                      </div>
                      {!['is_null', 'is_not_null'].includes(String((selectedNode.data.config as any)?.operator)) && (
                        <div>
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Value</label>
                          <input 
                            type="text" 
                            value={String((selectedNode.data.config as Record<string, unknown>)?.value || '')} 
                            onChange={(e) => {
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), value: e.target.value } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }}
                            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                          />
                        </div>
                      )}
                    <SqlPreview sql={buildSql('filter', selectedNode.data.config as any)} />
                    </>
                  )}

                  {/* Combine Datasets UI */}
                  {selectedNode.data.subtype === 'combine' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Join Type</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.joinType || 'inner')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), joinType: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="inner">Inner Join</option>
                          <option value="left">Left Join</option>
                          <option value="right">Right Join</option>
                          <option value="full">Full Outer Join</option>
                          <option value="union">Union (Append)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Join Column</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.column || '')} 
                          onChange={(e) => {
                            const updatedNode = { 
                              ...selectedNode, 
                              data: { 
                                ...selectedNode.data, 
                                config: { 
                                  ...(selectedNode.data.config as any), 
                                  column: e.target.value
                                } 
                              } 
                            };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="">Select column...</option>
                          {getUpstreamColumns(selectedNode.id).map((col: string) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                    <SqlPreview sql={buildSql('combine', selectedNode.data.config as any)} />
                    </>
                  )}

                  {/* Combine / Join Datasets UI */}
                  {selectedNode.data.subtype === 'combine' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Join Type</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.joinType || 'inner')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), joinType: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="inner">Inner Join (Matching rows only)</option>
                          <option value="left">Left Join (All rows from first input)</option>
                          <option value="right">Right Join (All rows from second input)</option>
                          <option value="full">Full Outer Join (All rows from both)</option>
                        </select>
                      </div>
                      
                      <div className="bg-[#F4F5F7] p-3 rounded-md space-y-3">
                        <h4 className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">Join Conditions</h4>
                        <div className="grid grid-cols-2 gap-3 items-center">
                          <div>
                            <label className="block text-[9px] font-bold text-[#6B778C] mb-1 tracking-tighter uppercase">Left Input Key</label>
                            <select 
                              value={String((selectedNode.data.config as any)?.leftColumn || '')}
                              onChange={(e) => {
                                const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), leftColumn: e.target.value } } };
                                setSelectedNode(updatedNode);
                                setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                              }}
                              className="w-full border border-[#DFE1E6] rounded-md px-2 py-1.5 text-xs text-[#171717]"
                            >
                              <option value="">Select col...</option>
                              {getUpstreamColumns(selectedNode.id).map((col: string) => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>
                          <div className="relative pt-4 text-center">
                            <span className="text-sm font-bold text-[#6B778C]">=</span>
                          </div>
                          <div>
                            <label className="block text-[9px] font-bold text-[#6B778C] mb-1 tracking-tighter uppercase">Right Input Key</label>
                            <select 
                              value={String((selectedNode.data.config as any)?.rightColumn || '')}
                              onChange={(e) => {
                                const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), rightColumn: e.target.value } } };
                                setSelectedNode(updatedNode);
                                setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                              }}
                              className="w-full border border-[#DFE1E6] rounded-md px-2 py-1.5 text-xs text-[#171717]"
                            >
                              <option value="">Select col...</option>
                              {getUpstreamColumns(selectedNode.id).map((col: string) => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>
                    <SqlPreview sql={buildSql('combine', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Clean & Format UI */}
                  {selectedNode.data.subtype === 'clean' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Target Column</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.column || '')} 
                          onChange={(e) => {
                            const updatedNode = { 
                              ...selectedNode, 
                              data: { 
                                ...selectedNode.data, 
                                config: { 
                                  ...(selectedNode.data.config as any), 
                                  column: e.target.value
                                } 
                              } 
                            };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="">Select column...</option>
                          {getUpstreamColumns(selectedNode.id).map((col: string) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Operation</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.operation || 'trim')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), operation: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="trim">Trim Whitespace</option>
                          <option value="upper">Uppercase</option>
                          <option value="lower">Lowercase</option>
                          <option value="numeric">Remove non-numeric characters</option>
                          <option value="replace_null">Replace empty with value</option>
                          <option value="to_date">Convert to Date</option>
                        </select>
                      </div>
                      {String((selectedNode.data.config as any)?.operation) === 'replace_null' && (
                        <div>
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">New Value</label>
                          <input 
                            type="text" 
                            placeholder="Replacement text"
                            value={String((selectedNode.data.config as Record<string, unknown>)?.newValue || '')} 
                            onChange={(e) => {
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), newValue: e.target.value } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }}
                            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                          />
                        </div>
                      )}
                    <SqlPreview sql={buildSql('clean', selectedNode.data.config as any)} />
                    </>
                  )}

                  {/* Aggregate Data UI */}
                  {selectedNode.data.subtype === 'aggregate' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-2">Group By Columns</label>
                        <div className="border border-[#DFE1E6] rounded-md p-2 max-h-40 overflow-y-auto space-y-1 bg-[#FAFBFC]">
                          {getUpstreamColumns(selectedNode.id).map((col: string) => {
                            const isChecked = String((selectedNode.data.config as any)?.groupBy || '').split(',').map(s => s.trim()).includes(col);
                            return (
                              <label key={col} className={`flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-1.5 rounded transition-colors ${isChecked ? 'bg-blue-50' : ''}`}>
                                <input 
                                  type="checkbox" 
                                  className="w-4 h-4 rounded border-[#DFE1E6] text-[#0052CC]"
                                  checked={isChecked}
                                  onChange={(e) => {
                                     const currentList = String((selectedNode.data.config as any)?.groupBy || '').split(',').map(s => s.trim()).filter(s => s);
                                     let newList = e.target.checked ? [...currentList, col] : currentList.filter(s => s !== col);
                                     const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), groupBy: newList.join(', ') } } };
                                     setSelectedNode(updatedNode);
                                     setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                  }}
                                />
                                <span className={`text-sm ${isChecked ? 'font-bold' : ''}`}>{col}</span>
                              </label>
                            );
                          })}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <label className="block text-xs font-semibold text-[#6B778C]">Aggregations</label>
                        {((selectedNode.data.config as any)?.aggregations || []).map((agg: any, idx: number) => (
                           <div key={idx} className="p-3 bg-gray-50 border border-[#DFE1E6] rounded-md space-y-2 relative group">
                              <button 
                                className="absolute top-1 right-1 p-1 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => {
                                  const aggs = [...(selectedNode.data.config as any).aggregations];
                                  aggs.splice(idx, 1);
                                  const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), aggregations: aggs } } };
                                  setSelectedNode(updatedNode);
                                  setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                              ><Trash2 size={12} /></button>
                              <select 
                                value={agg.column} 
                                onChange={(e) => {
                                   const aggs = [...(selectedNode.data.config as any).aggregations];
                                   aggs[idx].column = e.target.value;
                                   const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), aggregations: aggs } } };
                                   setSelectedNode(updatedNode);
                                }}
                                className="w-full text-xs border rounded p-1"
                              >
                                <option value="">Count (*)</option>
                                {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                              </select>
                              <div className="flex space-x-1">
                                <select 
                                  value={agg.operation} 
                                  onChange={(e) => {
                                     const aggs = [...(selectedNode.data.config as any).aggregations];
                                     aggs[idx].operation = e.target.value;
                                     const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), aggregations: aggs } } };
                                     setSelectedNode(updatedNode);
                                  }}
                                  className="flex-1 text-xs border rounded p-1"
                                >
                                  <option value="sum">Sum</option>
                                  <option value="avg">Avg</option>
                                  <option value="count">Count</option>
                                  <option value="min">Min</option>
                                  <option value="max">Max</option>
                                </select>
                                <input 
                                  placeholder="Alias"
                                  value={agg.alias}
                                  onChange={(e) => {
                                     const aggs = [...(selectedNode.data.config as any).aggregations];
                                     aggs[idx].alias = e.target.value;
                                     const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), aggregations: aggs } } };
                                     setSelectedNode(updatedNode);
                                  }}
                                  className="flex-1 text-xs border rounded p-1"
                                />
                              </div>
                           </div>
                        ))}
                        <button 
                          onClick={() => {
                            const aggs = [...((selectedNode.data.config as any)?.aggregations || [])];
                            aggs.push({ column: '', operation: 'count', alias: `count_${aggs.length}` });
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), aggregations: aggs } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full py-1.5 border border-dashed border-[#0052CC] text-[#0052CC] text-xs font-bold rounded flex items-center justify-center space-x-1 hover:bg-blue-50"
                        >
                          <Plus size={12} /> <span>Add Aggregation</span>
                        </button>
                      </div>
                    <SqlPreview sql={buildSql('aggregate', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Computed Column UI */}
                  {selectedNode.data.subtype === 'computed' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">SQL Expression</label>
                        <textarea 
                          rows={3}
                          placeholder="e.g. price * quantity"
                          value={String((selectedNode.data.config as any)?.expression || '')}
                          onChange={(e) => {
                             const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), expression: e.target.value } } };
                             setSelectedNode(updatedNode);
                             setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">New Column Header</label>
                        <input 
                          type="text"
                          value={String((selectedNode.data.config as any)?.alias || '')}
                          onChange={(e) => {
                             const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), alias: e.target.value } } };
                             setSelectedNode(updatedNode);
                             setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                        />
                      </div>
                    <SqlPreview sql={buildSql('computed', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Rename Columns UI */}
                  {selectedNode.data.subtype === 'rename' && (
                    <div className="space-y-4">
                      <label className="block text-xs font-semibold text-[#6B778C]">Mappings</label>
                      {((selectedNode.data.config as any)?.mappings || []).map((m: any, idx: number) => (
                        <div key={idx} className="flex items-center space-x-2">
                           <select 
                             value={m.old} 
                             onChange={(e) => {
                               const maps = [...(selectedNode.data.config as any).mappings];
                               maps[idx].old = e.target.value;
                               const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), mappings: maps } } };
                               setSelectedNode(updatedNode);
                             }}
                             className="flex-1 text-xs border rounded p-1"
                           >
                              <option value="">Select...</option>
                              {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                           </select>
                           <ArrowRightLeft size={12} className="text-[#6B778C]" />
                           <input 
                             value={m.new}
                             onChange={(e) => {
                               const maps = [...(selectedNode.data.config as any).mappings];
                               maps[idx].new = e.target.value;
                               const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), mappings: maps } } };
                               setSelectedNode(updatedNode);
                             }}
                             className="flex-1 text-xs border rounded p-1"
                           />
                           <button onClick={() => {
                             const maps = [...(selectedNode.data.config as any).mappings];
                             maps.splice(idx, 1);
                             const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), mappings: maps } } };
                             setSelectedNode(updatedNode);
                             setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                           }}><Trash2 size={12} className="text-red-400" /></button>
                        </div>
                      ))}
                      <button 
                        onClick={() => {
                          const maps = [...((selectedNode.data.config as any)?.mappings || [])];
                          maps.push({ old: '', new: '' });
                          const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), mappings: maps } } };
                          setSelectedNode(updatedNode);
                          setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                        }}
                        className="w-full py-1.5 border border-dashed text-xs text-[#0052CC] font-bold rounded"
                      >+ Add Mapping</button>
                    <SqlPreview sql={buildSql('rename', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Remove Duplicates UI */}
                  {selectedNode.data.subtype === 'distinct' && (
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-2">Deduplicate based on:</label>
                      <div className="text-[10px] text-gray-500 mb-2 italic">Select columns to check for uniqueness. Leave empty to check entire row.</div>
                      <div className="border border-[#DFE1E6] rounded-md p-2 max-h-60 overflow-y-auto space-y-1 bg-[#FAFBFC]">
                        {getUpstreamColumns(selectedNode.id).map((col: string) => {
                          const isChecked = String((selectedNode.data.config as any)?.columns || '').split(',').map(s => s.trim()).includes(col);
                          return (
                            <label key={col} className={`flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-1.5 rounded transition-colors ${isChecked ? 'bg-blue-50' : ''}`}>
                              <input 
                                type="checkbox" 
                                className="w-4 h-4 rounded border-[#DFE1E6] text-[#0052CC]"
                                checked={isChecked}
                                onChange={(e) => {
                                   const currentList = String((selectedNode.data.config as any)?.columns || '').split(',').map(s => s.trim()).filter(s => s);
                                   let newList = e.target.checked ? [...currentList, col] : currentList.filter(s => s !== col);
                                   const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), columns: newList.join(', ') } } };
                                   setSelectedNode(updatedNode);
                                   setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                              />
                              <span className="text-sm font-inter">{col}</span>
                            </label>
                          );
                        })}
                      </div>
                    <SqlPreview sql={buildSql('distinct', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Custom SQL UI */}
                  {selectedNode.data.subtype === 'raw_sql' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Direct DuckDB SQL</label>
                        <div className="p-2 mb-2 bg-blue-50 text-[10px] text-[#0052CC] rounded leading-relaxed border border-blue-100">
                          Use <b>{"{{input}}"}</b> to reference the incoming dataset table name.
                        </div>
                        <textarea 
                          rows={6}
                          placeholder="SELECT * FROM {{input}} WHERE row_num > 10"
                          value={String((selectedNode.data.config as any)?.sql || '')}
                          onChange={(e) => {
                             const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sql: e.target.value } } };
                             setSelectedNode(updatedNode);
                             setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-[#0052CC]"
                        />
                      </div>
                    <SqlPreview sql={buildSql('raw_sql', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* CASE/WHEN Logic UI */}
                  {selectedNode.data.subtype === 'case_when' && (
                    <div className="space-y-4">
                       <label className="block text-xs font-semibold text-[#6B778C]">Logic Steps</label>
                       
                       <div className="p-2 mb-2 bg-blue-50 text-[10px] text-[#0052CC] rounded leading-relaxed border border-blue-100">
                         <b>Tip:</b> Text values (like <i>Gold</i> or <i>VIP</i>) are <b>automatically quoted</b>. No need to add single quotes manually.
                       </div>

                       {((selectedNode.data.config as any)?.conditions || []).map((c: any, idx: number) => (
                         <div key={idx} className="p-2 bg-gray-50 border rounded space-y-2 relative">
                            <button className="absolute top-1 right-1" onClick={() => {
                               const conds = [...(selectedNode.data.config as any).conditions];
                               conds.splice(idx, 1);
                               const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                               setSelectedNode(updatedNode);
                            }}><Trash2 size={12} className="text-red-400" /></button>
                            <div>
                               <label className="text-[9px] uppercase font-bold text-[#6B778C]">When (Condition)</label>
                               <input value={c.when} onChange={(e) => {
                                  const conds = [...(selectedNode.data.config as any).conditions];
                                  conds[idx].when = e.target.value;
                                  setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } });
                               }} className="w-full text-xs p-1 border rounded" placeholder="age > 20" />
                            </div>
                            <div>
                               <label className="text-[9px] uppercase font-bold text-[#6B778C]">Then (Result)</label>
                               <input value={c.then} onChange={(e) => {
                                  const conds = [...(selectedNode.data.config as any).conditions];
                                  conds[idx].then = e.target.value;
                                  setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } });
                               }} className="w-full text-xs p-1 border rounded" placeholder="'Adult'" />
                            </div>
                         </div>
                       ))}
                       <button onClick={() => {
                          const conds = [...((selectedNode.data.config as any)?.conditions || [])];
                          conds.push({ when: '', then: '' });
                          setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } });
                       }} className="w-full py-1.5 border border-dashed text-xs text-[#0052CC] font-bold rounded">+ Add Case</button>
                       <div className="pt-2 border-t mt-2">
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Else / Default Result</label>
                          <input 
                            value={String((selectedNode.data.config as any)?.elseValue || '')} 
                            onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), elseValue: e.target.value } } })}
                            className="w-full text-xs border rounded p-2" placeholder="'Unknown'" 
                          />
                       </div>
                       <div>
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Output Alias</label>
                          <input 
                            value={String((selectedNode.data.config as any)?.alias || '')} 
                            onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), alias: e.target.value } } })}
                            className="w-full text-xs border rounded p-2" placeholder="my_status" 
                          />
                       </div>
                    <SqlPreview sql={buildSql('case_when', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Window Function UI */}
                  {selectedNode.data.subtype === 'window' && (
                    <div className="space-y-4">
                      {/* Function */}
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Window Function</label>
                        <select
                          value={String((selectedNode.data.config as any)?.function || 'ROW_NUMBER')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), function: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="ROW_NUMBER">ROW_NUMBER — Sequential number (1…N)</option>
                          <option value="RANK">RANK — Rank with gaps on ties</option>
                          <option value="DENSE_RANK">DENSE_RANK — Rank without gaps</option>
                          <option value="LAG">LAG — Previous row value</option>
                          <option value="LEAD">LEAD — Next row value</option>
                          <option value="SUM">SUM — Running total</option>
                          <option value="AVG">AVG — Running average</option>
                          <option value="MIN">MIN — Running minimum</option>
                          <option value="MAX">MAX — Running maximum</option>
                          <option value="COUNT">COUNT — Running count</option>
                        </select>
                      </div>

                      {/* Value Column — required for LAG/LEAD/SUM/AVG/MIN/MAX/COUNT */}
                      {['LAG', 'LEAD', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT'].includes(String((selectedNode.data.config as any)?.function || 'ROW_NUMBER')) && (
                        <div>
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">
                            Value Column
                            <span className="ml-1 text-red-400">*</span>
                          </label>
                          <select
                            value={String((selectedNode.data.config as any)?.valueColumn || '')}
                            onChange={(e) => {
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), valueColumn: e.target.value } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }}
                            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          >
                            <option value="">Select column…</option>
                            {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                          <p className="text-[11px] text-[#6B778C] mt-1">Column passed as argument to the function</p>
                        </div>
                      )}

                      {/* Partition By */}
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Partition By <span className="font-normal text-[#6B778C]">(Groups)</span></label>
                        <select
                          value={String((selectedNode.data.config as any)?.partitionBy || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), partitionBy: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="">Whole Table (no partition)</option>
                          {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <p className="text-[11px] text-[#6B778C] mt-1">Reset counter per group. Leave blank for a global window.</p>
                      </div>

                      {/* Order By + Direction */}
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Order By</label>
                        <div className="flex gap-2">
                          <select
                            value={String((selectedNode.data.config as any)?.orderBy || '')}
                            onChange={(e) => {
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), orderBy: e.target.value } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }}
                            className="flex-1 border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          >
                            <option value="">No ordering</option>
                            {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                          {/* ASC / DESC toggle buttons */}
                          <div className="flex rounded-md border border-[#DFE1E6] overflow-hidden shrink-0">
                            {(['ASC', 'DESC'] as const).map((dir) => {
                              const current = String((selectedNode.data.config as any)?.direction || 'ASC');
                              const isActive = current === dir;
                              return (
                                <button
                                  key={dir}
                                  type="button"
                                  onClick={() => {
                                    const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), direction: dir } } };
                                    setSelectedNode(updatedNode);
                                    setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                  }}
                                  className={`px-3 py-2 text-xs font-bold transition-colors ${
                                    isActive
                                      ? 'bg-[#0052CC] text-white'
                                      : 'bg-white text-[#6B778C] hover:bg-gray-50'
                                  }`}
                                >
                                  {dir === 'ASC' ? '↑ ASC' : '↓ DESC'}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                        <p className="text-[11px] text-[#6B778C] mt-1">
                          Current: <span className="font-bold text-[#0052CC]">{String((selectedNode.data.config as any)?.direction || 'ASC')}</span>
                          {' '}— default is ASC (smallest first)
                        </p>
                      </div>

                      {/* Alias */}
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Output Column Name</label>
                        <input
                          value={String((selectedNode.data.config as any)?.alias || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), alias: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. row_idx, rank, running_total"
                        />
                      </div>

                      {/* Live SQL Preview (window uses its own builder) */}
                      {(() => {
                        const cfg = selectedNode.data.config as any;
                        const fn = cfg?.function || 'ROW_NUMBER';
                        const needsCol = ['LAG', 'LEAD', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT'].includes(fn);
                        const colArg = needsCol && cfg?.valueColumn ? `"${cfg.valueColumn}"` : needsCol ? '/* column */' : '';
                        const fnSQL = `${fn}(${colArg})`;
                        const overParts: string[] = [];
                        if (cfg?.partitionBy) overParts.push(`PARTITION BY "${cfg.partitionBy}"`);
                        if (cfg?.orderBy) overParts.push(`ORDER BY "${cfg.orderBy}" ${cfg?.direction || 'ASC'}`);
                        const alias = cfg?.alias || 'window_result';
                        const sql = `SELECT *,\n  ${fnSQL} OVER (${overParts.join(' ')})\n  AS "${alias}"\nFROM <prev_table>`;
                        return <SqlPreview sql={sql} />;
                      })()}
                    </div>
                  )}

                  {/* Select Columns UI */}
                  {selectedNode.data.subtype === 'select' && (
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-2">Columns to Keep</label>
                      <div className="border border-[#DFE1E6] rounded-md p-2 max-h-60 overflow-y-auto space-y-1 bg-[#FAFBFC] shadow-inner">
                        {getUpstreamColumns(selectedNode.id).map((col: string) => {
                          const isChecked = String((selectedNode.data.config as any)?.columns || '').split(',').map(s => s.trim()).includes(col);
                          return (
                            <label key={col} className={`flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-1.5 rounded transition-colors group ${isChecked ? 'bg-blue-50' : ''}`}>
                              <input 
                                type="checkbox" 
                                className="w-4 h-4 rounded border-[#DFE1E6] text-[#0052CC] focus:ring-[#0052CC]"
                                checked={isChecked}
                                onChange={(e) => {
                                   const currentList = String((selectedNode.data.config as any)?.columns || '').split(',').map(s => s.trim()).filter(s => s);
                                   let newList;
                                   if (e.target.checked) {
                                      newList = [...currentList, col].join(', ');
                                   } else {
                                      newList = currentList.filter(s => s !== col).join(', ');
                                   }
                                   const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), columns: newList } } };
                                   setSelectedNode(updatedNode);
                                   setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                              />
                              <span className={`text-sm ${isChecked ? 'font-bold text-[#0052CC]' : 'text-[#171717]'}`}>{col}</span>
                            </label>
                          );
                        })}
                        {getUpstreamColumns(selectedNode.id).length === 0 && (
                          <div className="text-xs text-center text-[#6B778C] py-4 italic">Connect an input node first</div>
                        )}
                      </div>
                    <SqlPreview sql={buildSql('select', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Sort Data UI */}
                  {selectedNode.data.subtype === 'sort' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Sort Column</label>
                        <select 
                          value={String((selectedNode.data.config as any)?.column || '')} 
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), column: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="">Select column...</option>
                          {getUpstreamColumns(selectedNode.id).map((col: string) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Direction</label>
                        <select 
                          value={String((selectedNode.data.config as any)?.direction || 'asc')} 
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), direction: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="asc">Ascending (A-Z, 0-9)</option>
                          <option value="desc">Descending (Z-A, 9-0)</option>
                        </select>
                      </div>
                    <SqlPreview sql={buildSql('sort', selectedNode.data.config as any)} />
                    </>
                  )}

                  {/* Limit Data UI */}
                  {selectedNode.data.subtype === 'limit' && (
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-1">Row Limit</label>
                      <input 
                        type="number" 
                        value={Number((selectedNode.data.config as any)?.count || 100)} 
                        onChange={(e) => {
                          const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), count: parseInt(e.target.value) } } };
                          setSelectedNode(updatedNode);
                          setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                        }}
                        className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                      />
                    <SqlPreview sql={buildSql('limit', selectedNode.data.config as any)} />
                    </div>
                  )}
                </div>
              )}

              {selectedNode.type === 'output' && typeof selectedNode.data?.config === 'object' && selectedNode.data.config !== null && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Export Format</label>
                    <select 
                      value={String((selectedNode.data.config as Record<string, unknown>)?.format || 'CSV')}
                      onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), format: e.target.value } } })}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                    >
                      <option value="CSV">CSV Document (.csv)</option>
                      <option value="Excel">Excel Document (.xlsx)</option>
                      <option value="JSON">JSON Data (.json)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">File Name</label>
                    <input 
                      type="text" 
                      value={String((selectedNode.data.config as Record<string, unknown>)?.filename || 'aggregated_results.csv')}
                      onChange={(e) => {
                        const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), filename: e.target.value } } };
                        setSelectedNode(updatedNode);
                        setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                      }}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Last Export Path (Server)</label>
                    <input type="text" readOnly value={String((selectedNode.data.config as Record<string, unknown>)?.file_path || "No export yet")} className="w-full bg-gray-50 border border-[#DFE1E6] rounded-md px-3 py-2 text-xs text-[#6B778C] font-mono" />
                  </div>
                </div>
              )}
            </div>
            <div className="p-4 border-t border-[#DFE1E6]">
              <button 
                onClick={saveNodeChanges}
                className="w-full px-4 py-2 bg-[#0052CC] hover:bg-[#0065FF] text-white text-sm font-medium rounded-md transition-colors shadow-sm"
              >
                Save Changes
              </button>
            </div>
          </aside>
        )}
      </div>

      {/* Resizable Bottom Preview Panel */}
      {selectedNode && (
        <div 
          style={{ height: `${previewHeight}px` }}
          className="bg-white border-t border-[#DFE1E6] flex flex-col relative z-20 shadow-[0_-4px_12px_rgba(0,0,0,0.05)] transition-all duration-300"
        >
          {/* Resize Handle */}
          <div 
            className="absolute -top-1.5 left-0 right-0 h-3 cursor-ns-resize hover:bg-[#0052CC]/10 transition-colors z-30 flex items-center justify-center group"
            onMouseDown={(e) => {
              const startY = e.clientY;
              const startHeight = previewHeight;
              const onMouseMove = (moveEvent: MouseEvent) => {
                const delta = startY - moveEvent.clientY;
                setPreviewHeight(Math.max(100, Math.min(800, startHeight + delta)));
              };
              const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
              };
              document.addEventListener('mousemove', onMouseMove);
              document.addEventListener('mouseup', onMouseUp);
            }}
          >
            <div className="w-12 h-1 bg-[#DFE1E6] rounded-full group-hover:bg-[#0052CC] transition-colors"></div>
          </div>

          <div className="flex items-center justify-between px-6 py-2 border-b border-[#DFE1E6] bg-[#FAFBFC] shrink-0">
            <div className="flex items-center space-x-3">
              <div className="p-1 bg-orange-50 text-[#FF8B00] rounded">
                <Eye size={16} />
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#6B778C]">Dataset Preview</span>
                <h4 className="text-sm font-bold text-[#171717]">{String(selectedNode.data.label)}</h4>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {nodeSamples[selectedNode.id] && (
                <span className="text-[10px] bg-gray-100 text-[#6B778C] px-2 py-1 rounded font-bold uppercase">
                  Showing {nodeSamples[selectedNode.id].length} sample rows
                </span>
              )}
              <button 
                onClick={() => setSelectedNode(null)} 
                className="p-1.5 text-[#6B778C] hover:bg-gray-200 rounded-md transition-colors"
                title="Close Preview"
              >
                <ChevronDown size={18} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-auto bg-white p-0">
            {nodeSamples[selectedNode.id] && nodeSamples[selectedNode.id].length > 0 ? (
              <table className="w-full text-left border-collapse min-w-max">
                <thead className="sticky top-0 bg-[#FAFBFC] z-10 border-b border-[#DFE1E6]">
                  <tr>
                    {Object.keys(nodeSamples[selectedNode.id][0]).map((key) => (
                      <th key={key} className="px-4 py-2.5 text-[11px] font-bold text-[#6B778C] uppercase tracking-wider border-r border-[#DFE1E6] last:border-0">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DFE1E6]">
                  {nodeSamples[selectedNode.id].map((row: any, i: number) => (
                    <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                      {Object.values(row).map((val: any, j: number) => (
                        <td key={j} className="px-4 py-2 text-sm text-[#171717] border-r border-[#DFE1E6] last:border-0 max-w-[300px] truncate">
                          {String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-[#6B778C] space-y-3 bg-[#FAFBFC]/50">
                <div className="p-3 bg-gray-100 rounded-full"><Table size={24} className="opacity-40" /></div>
                <p className="text-sm font-medium">No preview data available for this node.</p>
                <p className="text-xs">Execute the workflow to generate sample data for all nodes.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Save Modal */}
      {isSaveModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 border border-[#DFE1E6] animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-bold text-[#172B4D] mb-4">Save Pipeline</h3>
            <p className="text-sm text-[#6B778C] mb-4">Enter a name for your data processing pipeline.</p>
            <input
              autoFocus
              type="text"
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC] mb-6 outline-none"
              placeholder="e.g., Weekly Sales Stats"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSaveWorkflow(); }}
            />
            <div className="flex justify-end space-x-3">
              <button onClick={() => setIsSaveModalOpen(false)} className="px-4 py-2 text-sm text-[#6B778C] hover:bg-gray-100 rounded-md transition-colors">Cancel</button>
              <button 
                onClick={handleSaveWorkflow}
                disabled={!workflowName}
                className="px-4 py-2 text-sm bg-[#0052CC] text-white font-medium rounded-md hover:bg-[#0065FF] disabled:opacity-50 transition-colors shadow-sm"
              >
                Save Pipeline
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Modal */}
      {isLoadModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 border border-[#DFE1E6] animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-bold text-[#172B4D] mb-4 font-inter">Open Pipeline</h3>
            {availableWorkflows.length === 0 ? (
              <p className="text-sm text-[#6B778C] mb-6">No saved pipelines found on server.</p>
            ) : (
              <div className="space-y-2 mb-6 max-h-[350px] overflow-y-auto px-1">
                {availableWorkflows.map(name => (
                  <button
                    key={name}
                    onClick={() => handleLoadWorkflow(name)}
                    className="w-full text-left px-4 py-3 text-sm text-[#172B4D] hover:bg-[#F4F5F7] border border-[#DFE1E6] rounded-md transition-all flex items-center justify-between group hover:border-[#0052CC]"
                  >
                    <span className="font-medium">{name}</span>
                    <FolderOpen size={14} className="text-[#6B778C] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            )}
            <div className="flex justify-end">
              <button 
                onClick={() => setIsLoadModalOpen(false)} 
                className="px-4 py-2 text-sm text-[#6B778C] hover:bg-gray-100 rounded-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <ReactFlowProvider>
      <Dashboard />
    </ReactFlowProvider>
  );
}
