"use client";

import React, { useState } from 'react';
import WorkspaceCanvas from '@/components/workflow/canvas';
import { Database, Filter, ArrowRightLeft, Table, Settings, Play, Download, Search, LayoutDashboard, SlidersHorizontal, FileText, FileDown } from 'lucide-react';
import { Node } from '@xyflow/react';

import { useReactFlow, ReactFlowProvider } from '@xyflow/react';
import { executeWorkflow, uploadFile } from '@/lib/api';

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
  const { setNodes } = useReactFlow();

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ type: nodeType, label }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const saveNodeChanges = () => {
    if (!selectedNode) return;
    setNodes((nds) => 
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          // It's important to merge the new config properly
          node.data = { ...selectedNode.data };
          if (selectedNode.data.label) {
            // Also need to reflect label if changed
            node.data.label = selectedNode.data.label;
          }
        }
        return node;
      })
    );
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
          <ExecuteButton />
          <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-[#6B778C] bg-white border border-[#DFE1E6] hover:bg-gray-50 rounded-md transition-colors">
            <Download size={16} />
            <span>Export</span>
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
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Filter Records')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Filter size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Filter Records</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Combine Datasets')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <ArrowRightLeft size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Combine Datasets</span>
              </div>
              <div draggable onDragStart={(e) => onDragStart(e, 'default', 'Clean & Format')} className="flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] hover:border-[#6554C0] hover:shadow-sm rounded-md cursor-grab transition-all">
                <div className="p-1.5 bg-purple-50 text-[#6554C0] rounded">
                  <Settings size={16} />
                </div>
                <span className="text-sm font-medium text-gray-700">Clean & Format</span>
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
              <h3 className="text-base font-medium text-[#171717] mb-2">
                <input 
                  type="text" 
                  value={String(selectedNode.data?.label || '')} 
                  onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: e.target.value } })}
                  className="w-full bg-transparent border-none focus:outline-none focus:ring-0 p-0 font-medium text-lg placeholder-gray-400"
                  placeholder="Node Label"
                />
              </h3>
              
              {selectedNode.type === 'input' && typeof selectedNode.data?.config === 'object' && selectedNode.data.config !== null && (
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
                              column: e.target.value,
                              operator: (selectedNode.data.config as any)?.operator || '>'
                            } 
                          } 
                        };
                        setSelectedNode(updatedNode);
                        setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                      }}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                    >
                      <option value="">Select column...</option>
                      {(selectedNode.data.config as any)?.availableColumns?.map((col: string) => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                      {/* Fallbacks if not detected yet */}
                      {!((selectedNode.data.config as any)?.availableColumns) && (
                        <>
                          <option value="Revenue">Revenue (Default)</option>
                          <option value="Region">Region</option>
                        </>
                      )}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Condition</label>
                    <select 
                      value={String((selectedNode.data.config as Record<string, unknown>)?.operator || '>')}
                      onChange={(e) => {
                        const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), operator: e.target.value } } };
                        setSelectedNode(updatedNode);
                        setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                      }}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                    >
                      <option value=">">is greater than</option>
                      <option value="<">is less than</option>
                      <option value="=">is equal to</option>
                      <option value="contains">contains</option>
                    </select>
                  </div>
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
