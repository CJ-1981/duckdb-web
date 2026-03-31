"use client";

import React, { useState } from 'react';
import WorkspaceCanvas from '@/components/workflow/canvas';
import { Database, Filter, ArrowRightLeft, Table, Settings, Play, Download, Search, LayoutDashboard, SlidersHorizontal, FileText, FileDown, Save, FolderOpen, Sigma } from 'lucide-react';
import { Node, useReactFlow, ReactFlowProvider } from '@xyflow/react';
import { executeWorkflow, uploadFile, saveWorkflow, listSavedWorkflows, loadWorkflowGraph } from '@/lib/api';


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
        const op = config?.operation || 'sum';
        const col = config?.column || '';
        const alias = config?.alias || (col ? `${op}_${col}` : (config?.groupBy ? '' : 'count_all'));
        
        groupBy.forEach((c: string) => predictedCols.add(c));
        if (alias) predictedCols.add(alias);
        
        // If we have actual columns from execution, use those instead as they are more accurate
        if (Array.isArray(config?.availableColumns) && config.availableColumns.length > 0) {
           return config.availableColumns;
        }
        
        return Array.from(predictedCols);
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
      const result = await executeWorkflow(getNodes(), getEdges());
      setExecutionResult(result);
      
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
                          <option value="starts_with">starts with</option>
                          <option value="ends_with">ends with</option>
                          <option value="is_null">is empty / null</option>
                          <option value="is_not_null">is not empty</option>
                          <option value="in">is in list (a,b,c)</option>
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
                    </>
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
                          {((selectedNode.data.config as any)?.availableColumns || getUpstreamColumns(selectedNode.id))?.map((col: string) => (
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
                    </>
                  )}

                  {/* Aggregate Data UI */}
                  {selectedNode.data.subtype === 'aggregate' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Group By (optional, comma-separated)</label>
                        <input 
                          type="text" 
                          placeholder="e.g. category, region"
                          value={String((selectedNode.data.config as Record<string, unknown>)?.groupBy || '')} 
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), groupBy: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Aggregation Column</label>
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
                          {((selectedNode.data.config as any)?.availableColumns || getUpstreamColumns(selectedNode.id))?.map((col: string) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Function</label>
                        <select 
                          value={String((selectedNode.data.config as Record<string, unknown>)?.operation || 'sum')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), operation: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="sum">Sum (Total)</option>
                          <option value="avg">Average (Mean)</option>
                          <option value="count">Count (Frequency)</option>
                          <option value="min">Minimum</option>
                          <option value="max">Maximum</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Output Alias</label>
                        <input 
                          type="text" 
                          placeholder="e.g. total_sales"
                          value={String((selectedNode.data.config as Record<string, unknown>)?.alias || '')} 
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), alias: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]" 
                        />
                      </div>
                    </>
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

      {/* Execution Result Preview Panel */}
      {executionResult && (
        <div className="h-64 border-t border-[#DFE1E6] bg-white flex flex-col animate-in slide-in-from-bottom duration-300">
          <div className="flex items-center justify-between px-4 py-2 border-b border-[#DFE1E6] bg-[#FAFBFC]">
            <div className="flex items-center space-x-4">
              <h4 className="text-xs font-bold text-[#172B4D] uppercase tracking-wider">Data Preview ({executionResult.row_count} total rows)</h4>
              <span className="text-[10px] bg-[#EAE6FF] text-[#403294] px-2 py-0.5 rounded-full font-bold">Showing first 50 rows</span>
            </div>
            <button 
              onClick={() => setExecutionResult(null)}
              className="text-[#6B778C] hover:text-[#172B4D]"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            <table className="w-full text-left border-collapse min-w-max">
              <thead className="sticky top-0 bg-white shadow-sm z-10">
                <tr>
                  {executionResult.columns?.map((col: string) => (
                    <th key={col} className="px-4 py-2 text-xs font-bold text-[#6B778C] border-b border-r border-[#DFE1E6] bg-gray-50 uppercase tracking-tight">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {executionResult.preview?.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-[#F4F5F7] transition-colors border-b border-[#DFE1E6]">
                    {executionResult.columns?.map((col: string) => (
                      <td key={col} className="px-4 py-2 text-sm text-[#172B4D] border-r border-[#DFE1E6] font-inter">
                        {String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
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
