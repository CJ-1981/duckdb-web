"use client";

import React, { useState, useEffect } from 'react';
import WorkspaceCanvas from '@/components/workflow/canvas';
import { SqlPreview } from '@/components/workflow/SqlPreview';
import { buildSql, getConditionSql } from '@/components/workflow/SqlHelpers';
import { WorkflowToolbar } from '@/components/workflow/WorkflowToolbar';
import { Database, Filter, ArrowRightLeft, Table, Settings, Play, Search, LayoutDashboard, SlidersHorizontal, FileText, FileDown, Save, FolderOpen, Sigma, Eye, ChevronRight, SortAsc, ListOrdered, Calculator, Code, Fingerprint, PenLine, GitBranch, BarChart3, Plus, Trash2, Wand2, Microscope, PanelLeftClose, PanelLeftOpen, PanelBottomClose, Copy, X, CheckCheck, AlertCircle, RefreshCw, Globe, Repeat, Dices, Braces, DatabaseBackup } from 'lucide-react';
import { Node, Edge, useReactFlow, ReactFlowProvider, useNodesState, useEdgesState, Panel } from '@xyflow/react';
import { useWorkflowState } from '@/hooks/useWorkflowState';
import { executeWorkflow, uploadFile, saveWorkflow, listSavedWorkflows, loadWorkflowGraph, generateReport, inspectNode, renameWorkflow, deleteWorkflow, validateSql, previewSql, getBackendUrl } from '@/lib/api-unified';
import DataInspectionPanel, { type ColumnTypeDef, type FullStats } from '@/components/panels/DataInspectionPanel';
import AiSqlBuilderPanel from '@/components/panels/AiSqlBuilderPanel';
import AiPipelineBuilderPanel from '@/components/panels/AiPipelineBuilderPanel';
import SettingsPanel from '@/components/panels/SettingsPanel';

interface WorkflowTab {
  id: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  nodeSamples: Record<string, any[]>;
  nodeTypes: Record<string, ColumnTypeDef[]>;
}

// ─── SQL Preview helpers ──────────────────────────────────────────────────────


function Dashboard() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const { nodes, setNodes, onNodesChange, edges, setEdges, onEdgesChange, history, pushToHistory, undo, redo, getNodes, getEdges } = useWorkflowState([], []);
  const [layoutCounter, setLayoutCounter] = useState(0);

  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [isLoadModalOpen, setIsLoadModalOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState("");
  const [currentPipelineName, setCurrentPipelineName] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [availableWorkflows, setAvailableWorkflows] = useState<string[]>([]);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [renamingWorkflow, setRenamingWorkflow] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState<string>('');
  const [renameLoading, setRenameLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [executionSuccess, setExecutionSuccess] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<{ title: string; detail: string; type: 'success' | 'error' | 'info' } | null>(null);
  
  // Custom SQL Preview State
  const [customSqlPreviewResult, setCustomSqlPreviewResult] = useState<any>(null);
  const [isCustomSqlExecuting, setIsCustomSqlExecuting] = useState(false);

  useEffect(() => {
    setCustomSqlPreviewResult(null);
  }, [selectedNode?.id]);

  // AI SQL Sidebar State
  const [aiSqlInitialPrompt, setAiSqlInitialPrompt] = useState<string>('');
  const [previewHeight, setPreviewHeight] = useState(280);
  const [previewLimit, setPreviewLimit] = useState(50);
  const [nodeSamples, setNodeSamples] = useState<Record<string, any[]>>({});
  const [nodeTypes, setNodeTypes] = useState<Record<string, ColumnTypeDef[]>>({});
  const [activeBottomTab, setActiveBottomTab] = useState(0);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isAiPipelinePanelOpen, setIsAiPipelinePanelOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [tooltip, setTooltip] = useState<{ label: string; text: string; x: number; y: number } | null>(null);
  const [isBottomPanelVisible, setIsBottomPanelVisible] = useState(true);

  const [tabs, setTabs] = useState<WorkflowTab[]>([
    { id: 'initial-workflow', name: 'New Pipeline', nodes: [], edges: [], nodeSamples: {}, nodeTypes: {} }
  ]);
  const [activeTabId, setActiveTabId] = useState<string | null>('initial-workflow');

  const switchTab = (tabId: string) => {
    if (tabId === activeTabId) return;
    
    setTabs(prev => prev.map(t => t.id === activeTabId ? {
      ...t,
      nodes: getNodes(),
      edges: getEdges(),
      nodeSamples,
      nodeTypes,
      name: currentPipelineName || t.name
    } : t));

    const targetTab = tabs.find(t => t.id === tabId);
    if (targetTab) {
      setNodes(targetTab.nodes);
      setEdges(targetTab.edges);
      setNodeSamples(targetTab.nodeSamples);
      setNodeTypes(targetTab.nodeTypes);
      setCurrentPipelineName(targetTab.name === 'New Pipeline' ? null : targetTab.name);
      setActiveTabId(tabId);
      setSelectedNode(null);
    }
  };

  const addNewTab = () => {
    const newId = `wf-${Date.now()}`;
    const newTab: WorkflowTab = {
      id: newId,
      name: 'New Pipeline',
      nodes: [],
      edges: [],
      nodeSamples: {},
      nodeTypes: {}
    };

    if (activeTabId) {
      setTabs(prev => prev.map(t => t.id === activeTabId ? {
        ...t,
        nodes: getNodes(),
        edges: getEdges(),
        nodeSamples,
        nodeTypes,
        name: currentPipelineName || t.name
      } : t));
    }

    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newId);
    setNodes([]);
    setEdges([]);
    setNodeSamples({});
    setNodeTypes({});
    setCurrentPipelineName(null);
    setSelectedNode(null);
  };

  const closeTab = (tabId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (tabs.length <= 1) {
      setNodes([]);
      setEdges([]);
      setNodeSamples({});
      setNodeTypes({});
      setCurrentPipelineName(null);
      setTabs([{ id: 'initial-workflow', name: 'New Pipeline', nodes: [], edges: [], nodeSamples: {}, nodeTypes: {} }]);
      setActiveTabId('initial-workflow');
      return;
    }

    const tabIndex = tabs.findIndex(t => t.id === tabId);
    const newTabs = tabs.filter(t => t.id !== tabId);
    setTabs(newTabs);

    if (activeTabId === tabId) {
      const nextTab = newTabs[Math.max(0, tabIndex - 1)];
      setActiveTabId(nextTab.id);
      setNodes(nextTab.nodes);
      setEdges(nextTab.edges);
      setNodeSamples(nextTab.nodeSamples);
      setNodeTypes(nextTab.nodeTypes);
      setCurrentPipelineName(nextTab.name === 'New Pipeline' ? null : nextTab.name);
    }
  };

  const showTooltip = (e: React.MouseEvent, label: string, text: string) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const padding = 10;
    const tooltipWidth = 256;
    let x = rect.right + 10;
    if (x + tooltipWidth > window.innerWidth - padding) {
      x = rect.left - tooltipWidth - 10;
    }
    setTooltip({
      label,
      text,
      x: x,
      y: rect.top + rect.height / 2,
      isHeader: false
    } as any);
  };

  const showHeaderTooltip = (e: React.MouseEvent, label: string, text: string) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const padding = 20;
    const tooltipWidth = 256;
    const centerX = rect.left + rect.width / 2;

    let x = centerX;
    let arrowOffset = 0;

    if (x - tooltipWidth / 2 < padding) {
      const oldX = x;
      x = tooltipWidth / 2 + padding;
      arrowOffset = oldX - x;
    } else if (x + tooltipWidth / 2 > window.innerWidth - padding) {
      const oldX = x;
      x = window.innerWidth - tooltipWidth / 2 - padding;
      arrowOffset = oldX - x;
    }

    setTooltip({
      label,
      text,
      x: x,
      y: rect.bottom + 10,
      isHeader: true,
      arrowOffset: arrowOffset
    } as any);
  };

  const hideTooltip = () => setTooltip(null);

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

  const handleNewWorkflow = () => {
    if (confirm("Create a new pipeline? Current unsaved changes in this tab will be lost if you clear it, or we can open a new tab.")) {
      addNewTab();
    }
  };

  const handleRenameWorkflow = async () => {
    try {
      await renameWorkflow(currentPipelineName || "", newName);
      setCurrentPipelineName(newName);
      setNewName("");
      setIsRenameModalOpen(false);
      setExecutionMessage({ title: "Pipeline renamed!", detail: `Algorithm was renamed to ${newName}.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
    } catch (e: any) {
      setExecutionMessage({ title: "Rename failed.", detail: e.message || "Something went wrong.", type: 'error' });
      setExecutionSuccess(true);
    }
  };

  const handleSaveWorkflow = async () => {
    try {
      await saveWorkflow(workflowName, getNodes(), getEdges());
      setCurrentPipelineName(workflowName);
      setIsSaveModalOpen(false);
      setWorkflowName("");
      setExecutionMessage({ title: "Pipeline saved!", detail: `Workflow '${workflowName}' has been secured.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
    } catch (e: any) { 
      setExecutionMessage({ title: "Save failed.", detail: e.message || "Could not save workflow.", type: 'error' });
      setExecutionSuccess(true);
      console.error(e); 
    }
  };

  const handleLoadWorkflow = async (name: string) => {
    // Warn about unsaved changes before loading
    if (nodes && nodes.length > 0 && !confirm(`Load workflow '${name}'? Current unsaved changes will be lost.`)) {
      return;
    }

    try {
      const data = await loadWorkflowGraph(name);
      const sanitizedNodes = (data.nodes || []).map((n: any) => {
        const { className, ...rest } = n;
        return rest;
      });
      setNodes(sanitizedNodes);
      setEdges(data.edges || []);
      setCurrentPipelineName(name);
      setIsLoadModalOpen(false);
      setExecutionMessage({ title: "Pipeline loaded!", detail: `Fetched '${name}' and reconstructed 100% of the graph.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
    } catch (e: any) {
      setExecutionMessage({ title: "Load failed.", detail: e.message || "Could not load workflow.", type: 'error' });
      setExecutionSuccess(true);
      console.error(e);
    }
  };

  const openLoadModal = async () => {
    try {
      const { workflows } = await listSavedWorkflows();
      setAvailableWorkflows(workflows || []);
      setIsLoadModalOpen(true);
    } catch (e) { setExecutionMessage({ title: "Error", detail: "Could not fetch workflows.", type: 'error' }); setExecutionSuccess(true); }
  };

  const handleImportSelectedFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setImportError(null);
    setImportFile(f);
  };

  const handleImportConfirm = async () => {
    if (!importFile) { setImportError('No file selected'); return; }
    try {
      const text = await importFile.text();
      const parsed = JSON.parse(text);
      if (!parsed || (!parsed.nodes && !parsed.definition && !parsed.edges)) {
        setImportError('File does not contain a valid workflow JSON (nodes/edges).');
        return;
      }
      // Support both {nodes, edges} and {definition} shapes
      const nodes = parsed.nodes || parsed.definition?.nodes || [];
      const edges = parsed.edges || parsed.definition?.edges || [];
      const baseName = importFile.name.replace(/\.json$/i, '');

      // Ensure we do NOT overwrite existing workflow: generate unique name if needed
      const listResp = await listSavedWorkflows();
      const existing = listResp.workflows || [];
      let targetName = baseName;
      let i = 1;
      while (existing.includes(targetName)) {
        targetName = `${baseName}-copy${i === 1 ? '' : i}`;
        i += 1;
      }

      // Save to server under unique name
      await saveWorkflow(targetName, nodes, edges);
      // Refresh list
      const refreshed = await listSavedWorkflows();
      setAvailableWorkflows(refreshed.workflows || []);
      setImportFile(null);
      setIsLoadModalOpen(false);
      setExecutionMessage({ title: "Import successful", detail: `Imported and saved '${targetName}'.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 3000);
    } catch (err: any) {
      setImportError(err.message || 'Import failed');
    }
  };

  const handleDeleteWorkflow = async (name: string) => {
    if (!confirm(`Delete workflow '${name}'? This cannot be undone.`)) return;
    try {
      setDeleteLoading(name);
      await deleteWorkflow(name);
      const { workflows } = await listSavedWorkflows();
      setAvailableWorkflows(workflows || []);
      setExecutionMessage({ title: 'Deleted', detail: `Deleted '${name}'.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 3000);
    } catch (e: any) {
      setExecutionMessage({ title: 'Delete failed', detail: e.message || 'Could not delete workflow', type: 'error' });
      setExecutionSuccess(true);
    } finally {
      setDeleteLoading(null);
    }
  };

  const startRenameWorkflow = (name: string) => {
    setRenamingWorkflow(name);
    setRenameValue(name);
  };

  const cancelRename = () => {
    setRenamingWorkflow(null);
    setRenameValue('');
  };

  const confirmRenameWorkflow = async (oldName: string) => {
    const trimmed = renameValue.trim();
    if (!trimmed) {
      setExecutionMessage({ title: 'Rename failed', detail: 'New name cannot be empty', type: 'error' });
      setExecutionSuccess(true);
      return;
    }
    try {
      setRenameLoading(true);
      await renameWorkflow(oldName, trimmed);
      const { workflows } = await listSavedWorkflows();
      setAvailableWorkflows(workflows || []);
      setRenamingWorkflow(null);
      setRenameValue('');
      setExecutionMessage({ title: 'Renamed', detail: `Renamed '${oldName}' to '${trimmed}'.`, type: 'success' });
      setExecutionSuccess(true);
      setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 3000);
    } catch (e: any) {
      setExecutionMessage({ title: 'Rename failed', detail: e.message || 'Could not rename workflow', type: 'error' });
      setExecutionSuccess(true);
    } finally {
      setRenameLoading(false);
    }
  };

  const getUpstreamColumns = (nodeId: string): string[] => {
    const nodes = getNodes();
    const edges = getEdges();

    const getNodeOutputColumns = (nId: string, visited = new Set<string>()): string[] => {
      if (visited.has(nId)) return [];
      visited.add(nId);

      const node = nodes.find(n => n.id === nId);
      if (!node) return [];

      const config = node.data?.config as any;
      const subtype = node.data?.subtype;

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

      if (subtype === 'select') {
        const cols = (config?.columns || "").split(',').map((c: string) => c.trim()).filter((c: string) => c);
        if (cols.length > 0) return cols;
      }

      if (node.type === 'input') {
        if (Array.isArray(config?.availableColumns) && config.availableColumns.length > 0) return config.availableColumns;
        if (nodeTypes[nId]) return nodeTypes[nId].map(c => c.column_name);
        return config?.availableColumns || [];
      }

      const incoming = edges.filter(e => e.target === nId);
      const upstreamCols = new Set<string>();
      for (const edge of incoming) {
        getNodeOutputColumns(edge.source, visited).forEach(c => upstreamCols.add(c));
      }

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

  const getInputSchema = (nodeId: string): ColumnTypeDef[] => {
    const nodes = getNodes();
    const edges = getEdges();
    const incoming = edges.filter(e => e.target === nodeId);
    
    if (incoming.length === 0) return [];
    
    const allTypes: ColumnTypeDef[] = [];
    const seen = new Set<string>();
    
    for (const edge of incoming) {
      const types = nodeTypes[edge.source] || [];
      for (const t of types) {
        if (!seen.has(t.column_name)) {
          allTypes.push(t);
          seen.add(t.column_name);
        }
      }
    }
    return allTypes;
  };

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string, subtype?: string) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ type: nodeType, label, subtype }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const saveNodeChanges = () => {
    if (!selectedNode) return;
    setNodes((nds: Node[]) =>
      nds.map((node: Node) => {
        if (node.id === (selectedNode as Node).id) {
          return {
            ...node,
            data: { ...selectedNode.data }
          };
        }
        return node;
      })
    );
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
    }, 4000);
  };

  const getSourceSchemas = (): { nodeId: string; label: string; schema: ColumnTypeDef[] }[] => {
    // Return schemas from all input/source nodes with their metadata
    return nodes
      .filter(n => n.type === 'input')
      .map(n => ({
        nodeId: n.id,
        label: (n.data as any).label || 'Input Node',
        schema: nodeTypes[n.id] || []
      }))
      .filter(s => s.schema.length > 0);
  };

  const handleConnection = async (connection: any) => {
    const sourceNode = nodes.find(n => n.id === connection.source);
    const targetNode = nodes.find(n => n.id === connection.target);

    if (!sourceNode || !targetNode) return;

    // If source node has schema, propagate it to the target node
    const sourceSchema = nodeTypes[sourceNode.id];
    if (sourceSchema && sourceSchema.length > 0) {
      // Update target node's available columns
      setNodes((nds: Node[]) =>
        nds.map((node: Node) => {
          if (node.id === targetNode.id) {
            return {
              ...node,
              data: {
                ...node.data,
                config: {
                  ...(node.data.config as any || {}),
                  availableColumns: sourceSchema.map((t: ColumnTypeDef) => t.column_name)
                }
              }
            };
          }
          return node;
        })
      );
    }
  };

  const handleApplyPipeline = (newNodes: Node[], newEdges: Edge[]) => {
    const suffix = '_' + Math.random().toString(36).substring(2, 11);
    const existingNodeIds = new Set(getNodes().map(n => n.id));
    const idMap: Record<string, string> = {};
    
    const mappedNodes = newNodes.map(n => {
      if (!existingNodeIds.has(n.id)) {
        idMap[n.id] = n.id + suffix;
        return { ...n, id: n.id + suffix };
      }
      return n;
    }).filter(n => !existingNodeIds.has(n.id));
    
    const mappedEdges = newEdges.map(e => ({
      ...e,
      id: e.id + suffix,
      source: idMap[e.source] || e.source,
      target: idMap[e.target] || e.target
    }));

    setNodes((nds) => [...nds, ...mappedNodes]);
    setEdges((eds) => [...eds, ...mappedEdges]);
    setIsAiPipelinePanelOpen(false);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      const result = await executeWorkflow(getNodes(), getEdges(), previewLimit);
      setExecutionResult(result);

      // Debug logging
      console.log('[handleExecute] Workflow execution result:', {
        node_samples_keys: Object.keys(result.node_samples || {}),
        node_types_keys: Object.keys(result.node_types || {}),
        node_samples_sample: result.node_samples ? Object.entries(result.node_samples).slice(0, 2) : {},
        selectedNode_id: selectedNode?.id,
        selectedNode_id_type: typeof selectedNode?.id
      });

      if (result.node_samples) {
        setNodeSamples(result.node_samples);
      }
      if (result.node_types) {
        setNodeTypes(result.node_types);
      }

      setNodes((nds: Node[]) => nds.map((node: Node) => ({
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

      setExecutionSuccess(true);
      setTimeout(() => {
        setExecutionSuccess(false);
        setExecutionMessage(null);
      }, 4000);

    } catch (e: any) {
      setExecutionMessage({ title: "Execution failed.", detail: e.message || String(e), type: 'error' });
      setExecutionSuccess(true);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleBeautify = () => {
    const nodes = getNodes();
    const edges = getEdges();

    if (nodes.length === 0) return;

    const depths: Record<string, number> = {};
    const incoming = (nodeId: string) => edges.filter(e => e.target === nodeId);
    nodes.forEach(n => depths[n.id] = 0);
    let changed = true;
    for (let i = 0; i < nodes.length && changed; i++) {
      changed = false;
      nodes.forEach(node => {
        const predecessors = incoming(node.id);
        if (predecessors.length > 0) {
          const maxPrevDepth = Math.max(...predecessors.map(e => depths[e.source] ?? 0));
          if (!isNaN(maxPrevDepth) && depths[node.id] !== maxPrevDepth + 1) {
            depths[node.id] = maxPrevDepth + 1;
            changed = true;
          }
        }
      });
    }
    const depthGroups: Record<number, string[]> = {};
    Object.entries(depths).forEach(([id, depth]) => {
      const d = isNaN(depth) ? 0 : depth;
      if (!depthGroups[d]) depthGroups[d] = [];
      depthGroups[d].push(id);
    });
    const HORIZONTAL_GAP = 280, VERTICAL_GAP = 180, CANVAS_CENTER_X = 250;
    const newNodes = nodes.map(node => {
      const depth = depths[node.id] ?? 0;
      const cleanDepth = isNaN(depth) ? 0 : depth;
      const group = depthGroups[cleanDepth] || [node.id];
      const indexInGroup = group.indexOf(node.id);
      const totalInGroup = group.length;
      const xOffset = (indexInGroup - (totalInGroup - 1) / 2) * HORIZONTAL_GAP;

      return {
        ...node,
        position: {
          x: CANVAS_CENTER_X + (isNaN(xOffset) ? 0 : xOffset),
          y: 100 + cleanDepth * VERTICAL_GAP
        }
      };
    });
    setNodes(newNodes);

    // Increment layout counter to trigger fitView in WorkspaceCanvas
    // The canvas will automatically zoom to fit all nodes considering bottom panel size
    setLayoutCounter(c => c + 1);
  };

  const handleInsertSql = (sql: string) => {
    const currentNodes = getNodes();
    const x = currentNodes.length > 0 
      ? Math.max(...currentNodes.filter(n => !isNaN(n.position.x)).map(n => n.position.x), 100) + 300 
      : 400;
    const y = currentNodes.length > 0 
      ? Math.min(...currentNodes.filter(n => !isNaN(n.position.y)).map(n => n.position.y), 100) 
      : 100;
    const newNode = {
      id: `raw_sql_${Date.now()}`,
      type: 'default',
      position: { x, y },
      data: { label: 'AI SQL Query', subtype: 'raw_sql', config: { sql } },
    };
    setNodes((nds: Node[]) => [...nds, newNode]);
  };

  const handleFetchFullStats = async (nodeId: string): Promise<FullStats> => {
    const rawNodes = getNodes();
    const rawEdges = getEdges();
    const nodes = rawNodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data }));
    const edges = rawEdges.map(e => ({ id: e.id, source: e.source, target: e.target }));
    const result = await inspectNode(nodes, edges, nodeId, previewLimit);
    return result as FullStats;
  };

  const isMac = typeof window !== 'undefined' && /Mac|iPod|iPhone|iPad|Macintosh/.test(navigator.userAgent);
  const mod = isMac ? '⌘' : 'Ctrl+';

  // Use refs for handlers to keep the keydown listener stable
  const executeRef = React.useRef(handleExecute);
  const openLoadRef = React.useRef(openLoadModal);
  const beautifyRef = React.useRef(handleBeautify);
  const newWorkflowRef = React.useRef(handleNewWorkflow);
  const saveWorkflowRef = React.useRef(() => {
    setWorkflowName(currentPipelineName || "");
    setIsSaveModalOpen(true);
  });

  React.useEffect(() => {
    executeRef.current = handleExecute;
    openLoadRef.current = openLoadModal;
    beautifyRef.current = handleBeautify;
    newWorkflowRef.current = handleNewWorkflow;
    saveWorkflowRef.current = () => {
      setWorkflowName(currentPipelineName || "");
      setIsSaveModalOpen(true);
    };
  }, [handleExecute, openLoadModal, handleBeautify, handleNewWorkflow, currentPipelineName]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if a modal or dialog is open
      const dialogElement = document.querySelector(
        '[role="dialog"], [aria-modal="true"], .modal, .overlay, [data-dialog-open]'
      );
      if (dialogElement && (dialogElement as HTMLElement).offsetParent !== null) {
        return; // Don't process shortcuts when modal is open
      }

      const activeElement = document.activeElement;
      if (
        activeElement instanceof HTMLInputElement ||
        activeElement instanceof HTMLTextAreaElement ||
        activeElement instanceof HTMLSelectElement ||
        (activeElement as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      const modifier = e.metaKey || e.ctrlKey;
      
      if (modifier) {
        if (e.code === 'KeyN' && e.shiftKey) { 
          e.preventDefault();
          newWorkflowRef.current();
        } else if (e.code === 'Enter') {
          e.preventDefault();
          e.stopPropagation();
          executeRef.current();
        } else if (e.code === 'KeyO' && e.shiftKey) {
          e.preventDefault();
          e.stopPropagation();
          openLoadRef.current();
        } else if (e.code === 'KeyS' && e.shiftKey) {
          e.preventDefault();
          e.stopPropagation();
          saveWorkflowRef.current();
        } else if (e.code === 'KeyB') {
          e.preventDefault();
          beautifyRef.current();
        } else if (e.code === 'BracketLeft') {
          e.preventDefault();
          setIsSidebarCollapsed(prev => !prev);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, false); 
    return () => window.removeEventListener('keydown', handleKeyDown, false);
  }, [isMac]);

  return (
    <div className="flex flex-col h-screen bg-[#FAFBFC] overflow-hidden text-[#171717]">
      <WorkflowToolbar
        workflowName={currentPipelineName || ''}
        onOpenLoadModal={openLoadModal}
        onOpenSaveModal={() => { setWorkflowName(currentPipelineName || ''); setIsSaveModalOpen(true); }}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onExecute={handleExecute}
        isExecuting={isExecuting}
        onRenameClick={() => { setNewName(currentPipelineName || ''); setIsRenameModalOpen(true); }}
        isSidebarCollapsed={isSidebarCollapsed}
        setIsSidebarCollapsed={setIsSidebarCollapsed}
        showHeaderTooltip={showHeaderTooltip}
        hideTooltip={hideTooltip}
        isMac={isMac}
        setIsAiPipelinePanelOpen={setIsAiPipelinePanelOpen}
        handleBeautify={handleBeautify}
        mod={mod}
      />

      <div className="flex items-center px-2 bg-[#F4F5F7] border-b border-[#DFE1E6] h-9 shrink-0 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const isActive = activeTabId === tab.id;
          const displayName = isActive ? (currentPipelineName || tab.name) : tab.name;
          return (
            <div
              key={tab.id}
              onClick={() => switchTab(tab.id)}
              className={`flex items-center gap-2 px-3 h-full text-[11px] font-bold cursor-pointer border-r border-[#DFE1E6] transition-all min-w-[100px] max-w-[180px] group relative ${
                isActive 
                  ? 'bg-white text-[#0052CC] shadow-[inset_0_-2px_0_#0052CC]' 
                  : 'text-[#6B778C] hover:bg-[#EBECF0]'
              }`}
            >
              <FileText size={12} className={isActive ? 'text-[#0052CC]' : 'text-[#6B778C]'} />
              <span className="truncate flex-1 tracking-tight">{displayName}</span>
              <button
                onClick={(e) => closeTab(tab.id, e)}
                className="p-0.5 rounded-full hover:bg-gray-200 text-[#6B778C] opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={10} />
              </button>
            </div>
          );
        })}
        <button
          onClick={addNewTab}
          className="p-1.5 ml-1 text-[#6B778C] hover:text-[#0052CC] hover:bg-[#EBECF0] rounded-md transition-colors"
          title="New Tab"
        >
          <Plus size={14} />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <aside
          className={`${isSidebarCollapsed ? 'w-0 opacity-0 -translate-x-full border-none overflow-hidden' : 'w-64 opacity-100 translate-x-0 border-r overflow-y-auto'} bg-white border-[#DFE1E6] flex flex-col transition-all duration-300 ease-in-out shrink-0`}
        >
          <div className="p-4 border-b border-[#DFE1E6]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-[#6B778C]" size={16} />
              <input
                type="text"
                placeholder="Search components..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-10 py-2 text-sm border border-[#DFE1E6] rounded-md focus:outline-none focus:ring-2 focus:ring-[#0052CC] focus:border-[#0052CC]"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-2.5 text-[#6B778C] hover:text-[#172B4D] transition-colors p-0.5 rounded-full hover:bg-gray-100"
                  aria-label="Clear search"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 p-4">
            {(() => {
              const shouldShow = (label: string, desc?: string) => {
                const q = searchQuery.toLowerCase();
                return label.toLowerCase().includes(q) || (desc && desc.toLowerCase().includes(q));
              };

              const categories = [
                {
                  title: 'Data Sources',
                  items: [
                    { type: 'input', label: 'Database Table', icon: <Database size={16} />, tooltip: 'Source data directly from project-level DuckDB tables.' },
                    { type: 'input', label: 'Data Files', icon: <Table size={16} />, tooltip: 'Upload or select local data files (CSV, Excel, JSON, Parquet) to analyze.' },
                    { type: 'input', subtype: 'remote_file', label: 'Remote File / S3', icon: <Globe size={16} />, tooltip: 'Load data from an external HTTP URL or S3 Bucket.' }
                  ]
                },
                {
                  title: 'Transformations',
                  items: [
                    { type: 'default', subtype: 'filter', label: 'Filter Records', icon: <Filter size={16} />, tooltip: 'Keep only records that match specific conditions (e.g. amount > 1000).' },
                    { type: 'default', subtype: 'combine', label: 'Combine Datasets', icon: <ArrowRightLeft size={16} />, tooltip: 'Join two separate tables together using common keys (Inner, Left, UNION, etc).' },
                    { type: 'default', subtype: 'clean', label: 'Clean & Format', icon: <Settings size={16} />, tooltip: 'Standardize data quality: trim spaces, change case, or fix null values.' },
                    { type: 'default', subtype: 'aggregate', label: 'Aggregate Data', icon: <Sigma size={16} />, tooltip: 'Summarize your data: calculate counts, averages, or totals grouped by categories.' },
                    { type: 'default', subtype: 'sort', label: 'Sort Data', icon: <SortAsc size={16} />, tooltip: 'Reorder your records based on one or more column values.' },
                    { type: 'default', subtype: 'limit', label: 'Limit Data', icon: <ListOrdered size={16} />, tooltip: 'Restrict the output to the first N rows of your dataset.' },
                    { type: 'default', subtype: 'select', label: 'Select Columns', icon: <Table size={16} />, tooltip: 'Choose which columns to keep and which to discard from the dataset.' },
                    { type: 'default', subtype: 'computed', label: 'Add Column', icon: <Calculator size={16} />, tooltip: 'Create new columns using arithmetic or SQL expressions (e.g. price * 1.1).' },
                    { type: 'default', subtype: 'rename', label: 'Rename Columns', icon: <PenLine size={16} />, tooltip: 'Modify column headers to make them more descriptive and readable.' },
                    { type: 'default', subtype: 'distinct', label: 'Remove Duplicates', icon: <Fingerprint size={16} />, tooltip: 'Filter out identical rows to ensure data uniqueness.' },
                    { type: 'default', subtype: 'case_when', label: 'Conditional Logic', icon: <GitBranch size={16} />, tooltip: 'Apply CASE-WHEN logic to create sophisticated branching rules.' },
                    { type: 'default', subtype: 'window', label: 'Window Function', icon: <BarChart3 size={16} />, tooltip: 'Perform calculations across related rows (ranks, moving averages).' },
                    { type: 'default', subtype: 'pivot', label: 'Pivot Data', icon: <Repeat size={16} />, tooltip: 'Reshape long data into wide format (rows to columns).' },
                    { type: 'default', subtype: 'unpivot', label: 'Unpivot Data', icon: <Repeat size={16} />, tooltip: 'Reshape wide data into long format (columns to rows).' },
                    { type: 'default', subtype: 'sample', label: 'Sample Data', icon: <Dices size={16} />, tooltip: 'Extract a random sample or specific percentage of the dataset.' },
                    { type: 'default', subtype: 'unnest', label: 'Unnest / JSON', icon: <Braces size={16} />, tooltip: 'Unnest arrays or extract fields from JSON columns.' },
                    { type: 'default', subtype: 'raw_sql', label: 'Custom SQL', icon: <Code size={16} />, tooltip: 'Maximum power: write your own DuckDB SQL to transform data.' }
                  ]
                },
                {
                  title: 'Outputs',
                  items: [
                    { type: 'output', subtype: 'report', label: 'Report Builder', icon: <FileText size={16} />, tooltip: 'Design a customized report (PDF/Markdown) from your pipeline results.' },
                    { type: 'output', subtype: 'export', label: 'Export File', icon: <FileDown size={16} />, tooltip: 'Save your processed data to a CSV or Excel file for external use.' },
                    { type: 'output', subtype: 'db_write', label: 'Write to DB', icon: <DatabaseBackup size={16} />, tooltip: 'Save your processed data directly as a table in the local database.' }
                  ]
                }
              ];

              let totalShowing = 0;
              const renderedCategories = categories.map((cat, catIdx) => {
                const filteredItems = cat.items.filter(item => shouldShow(item.label, item.tooltip));
                totalShowing += filteredItems.length;
                if (filteredItems.length === 0) return null;

                return (
                  <div key={catIdx} className="mb-6">
                    <h3 className="text-xs font-semibold text-[#6B778C] uppercase tracking-wider mb-3">{cat.title}</h3>
                    <div className="space-y-2">
                      {filteredItems.map((item, itemIdx) => (
                        <div
                          key={itemIdx}
                          draggable
                          onDragStart={(e) => onDragStart(e, item.type, item.label, (item as any).subtype)}
                          onMouseEnter={(e) => showTooltip(e, item.label, item.tooltip)}
                          onMouseLeave={hideTooltip}
                          className={`flex items-center space-x-3 p-3 bg-white border border-[#DFE1E6] rounded-md cursor-grab transition-all hover:shadow-sm ${item.type === 'input' ? 'hover:border-[#0052CC]' : item.type === 'output' ? 'hover:border-[#36B37E]' : 'hover:border-[#6554C0]'}`}
                        >
                          <div className={`p-1.5 rounded ${item.type === 'input' ? 'bg-blue-50 text-[#0052CC]' : item.type === 'output' ? 'bg-green-50 text-[#36B37E]' : 'bg-purple-50 text-[#6554C0]'}`}>
                            {item.icon}
                          </div>
                          <span className="text-sm font-medium text-gray-700">{item.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              });

              if (totalShowing === 0) {
                return (
                  <div className="flex flex-col items-center justify-center p-8 text-center bg-[#FAFBFC] rounded-lg border border-dashed border-[#DFE1E6]">
                    <Search className="text-[#6B778C] mb-2 opacity-20" size={32} />
                    <p className="text-sm font-medium text-[#171717]">No components found</p>
                    <p className="text-xs text-[#6B778C] mt-1">Try another search term</p>
                  </div>
                );
              }

              return renderedCategories;
            })()}
          </div>
        </aside>

        <main className="flex-1 relative flex flex-col h-[calc(100vh-4rem)]">
          {isAiPipelinePanelOpen && (
            <div className="absolute right-0 top-0 bottom-0 z-50">
              <AiPipelineBuilderPanel
                sourceSchemas={getSourceSchemas()}
                onApplyPipeline={handleApplyPipeline}
                onClose={() => setIsAiPipelinePanelOpen(false)}
              />
            </div>
          )}
          <WorkspaceCanvas
            key={activeTabId}
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            setNodes={setNodes}
            setEdges={setEdges}
            undo={undo}
            redo={redo}
            pushToHistory={pushToHistory}
            onNodeSelect={(node) => {
              if (node?.id !== selectedNode?.id) {
                setSelectedNode(node);
              }
              // Always show panel when a node is selected, even if it's the same node
              // This allows reopening the panel after it was closed
              if (node) setIsBottomPanelVisible(true);
            }}
            onAfterConnect={handleConnection}
            layoutCounter={layoutCounter}
            isBottomPanelVisible={isBottomPanelVisible && !!selectedNode}
            bottomPanelHeight={previewHeight}
            shortcutsEnabled={!isSaveModalOpen && !isLoadModalOpen && !isRenameModalOpen && !isSettingsOpen}
          >
            {selectedNode && isBottomPanelVisible && (
              <Panel position="bottom-left" style={{ width: '100%', margin: 0 }}>
                <div
                  data-testid="data-inspection-panel"
                  style={{ height: `${previewHeight}px` }}
                  className="bg-white border-t border-[#DFE1E6] flex flex-col relative z-[60] shadow-[0_-4px_12px_rgba(0,0,0,0.05)] transition-all duration-300"
                  onPointerDown={(e) => e.stopPropagation()}
                >
                  <div 
                    className="absolute -top-1.5 left-0 right-0 h-3 cursor-row-resize z-50 flex items-center justify-center group"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      document.body.classList.add('resizing');
                      const startY = e.clientY;
                      const startHeight = previewHeight;
                      const onMouseMove = (moveEvent: MouseEvent) => {
                        const deltaY = startY - moveEvent.clientY;
                        setPreviewHeight(Math.max(150, Math.min(800, startHeight + deltaY)));
                      };
                      const onMouseUp = () => {
                        document.body.classList.remove('resizing');
                        document.removeEventListener('mousemove', onMouseMove);
                        document.removeEventListener('mouseup', onMouseUp);
                      };
                      document.addEventListener('mousemove', onMouseMove);
                      document.addEventListener('mouseup', onMouseUp);
                    }}
                  >
                    <div className="w-16 h-1 bg-[#DFE1E6] rounded-full group-hover:bg-[#0052CC] transition-colors" />
                  </div>
                  
                  <div className="flex items-center justify-between px-4 py-2 bg-[#FAFBFC] border-b border-[#DFE1E6] h-12 select-none">
                    <div className="flex items-center space-x-1">
                      {[
                        { icon: <Microscope size={14} />, label: 'Data Inspection' },
                        { icon: <Code size={14} />, label: 'AI SQL Builder' }
                      ].map((tab, idx) => (
                        <button
                          key={idx}
                          onClick={() => setActiveBottomTab(idx)}
                          className={`flex items-center space-x-2 px-4 py-2 rounded-md font-bold text-xs transition-all ${
                            activeBottomTab === idx 
                              ? 'bg-white text-[#0052CC] shadow-sm ring-1 ring-[#DFE1E6] scale-105 z-10' 
                              : 'text-[#6B778C] hover:bg-gray-100 hover:text-[#172B4D]'
                          }`}
                        >
                          <span className={activeBottomTab === idx ? 'text-[#0052CC]' : 'text-[#6B778C]'}>{tab.icon}</span>
                          <span>{tab.label}</span>
                        </button>
                      ))}
                    </div>
                    
                    <div className="flex items-center gap-4 pr-2">
                       <div className="flex items-center !space-x-1.5 px-2.5 py-1 rounded-md border border-[#DFE1E6] bg-white/50 hover:bg-white transition-colors">
                        <span className="text-[10px] font-bold text-[#6B778C] uppercase tracking-tighter">rows:</span>
                        <select
                          value={previewLimit}
                          onChange={(e) => setPreviewLimit(Number(e.target.value))}
                          className="bg-transparent text-[10px] font-bold text-[#171717] focus:outline-none border-none cursor-pointer pr-1"
                        >
                          <option value={50}>50</option>
                          <option value={100}>100</option>
                          <option value={200}>200</option>
                          <option value={500}>500</option>
                          <option value={1000}>1000</option>
                        </select>
                      </div>
                      <span className="text-xs font-semibold text-[#172B4D] bg-[#F4F5F7] px-2 py-0.5 rounded border border-[#DFE1E6] whitespace-nowrap">{String(selectedNode.data.label)}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          setIsBottomPanelVisible(false);
                        }}
                        className="p-1.5 text-[#6B778C] hover:bg-gray-200 hover:text-[#171717] rounded-md transition-all border border-transparent hover:border-[#DFE1E6] bg-white shadow-sm cursor-pointer"
                        title="Close Panel"
                      >
                        <PanelBottomClose size={18} />
                      </button>
                    </div>
                  </div>

                  <div className="flex-1 overflow-hidden bg-white flex flex-col">
                    {activeBottomTab === 0 && (
                      <DataInspectionPanel
                        nodeId={String(selectedNode.id)}
                        nodeLabel={String(selectedNode.data.label)}
                        nodeSamples={nodeSamples}
                        nodeTypes={nodeTypes}
                        onFetchFullStats={handleFetchFullStats}
                      />
                    )}

                    {activeBottomTab === 1 && (
                      <div className="h-full min-h-0 flex flex-col overflow-hidden">
                        <AiSqlBuilderPanel
                          schema={getInputSchema(selectedNode.id)}
                          onInsertSql={handleInsertSql}
                          initialPrompt={aiSqlInitialPrompt}
                          nodes={nodes}
                          edges={edges}
                          nodeId={selectedNode.id}
                          onPreviewSql={previewSql}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            )}

            {/* Reopen Bottom Panel Button - Now inside Panel */}
            {selectedNode && !isBottomPanelVisible && (
              <Panel position="bottom-center">
                <div className="mb-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      setIsBottomPanelVisible(true);
                    }}
                    className="flex items-center space-x-2 px-5 py-3 bg-[#0052CC] text-white font-bold text-sm rounded-full shadow-[0_4px_20px_rgba(0,82,204,0.4)] hover:bg-[#0047B3] transition-all group scale-110 active:scale-105 cursor-pointer"
                  >
                    <Eye size={16} className="group-hover:scale-110 transition-transform" />
                    <span>Show Preview: {String(selectedNode.data.label)}</span>
                    <ChevronRight size={16} className="-rotate-90 ml-1" />
                  </button>
                </div>
              </Panel>
            )}
          </WorkspaceCanvas>
        </main>

        {/* Right Sidebar - Properties Panel */}
        {selectedNode && (
          <aside className="w-80 bg-white border-l border-[#DFE1E6] flex flex-col overflow-y-auto">
            <div className="p-4 border-b border-[#DFE1E6] bg-[#FAFBFC] flex items-center space-x-2">
              <SlidersHorizontal size={18} className="text-[#6B778C]" />
              <h2 className="text-sm font-semibold text-gray-800">Node Properties</h2>
            </div>
            <div className="p-4 flex-1">
              <h3 className="text-base font-medium text-[#171717] mb-2 flex items-center justify-between group">
                <div className="flex items-center flex-1 mr-2 border-b border-transparent hover:border-[#DFE1E6] focus-within:border-[#0052CC] transition-colors pb-0.5">
                  <input
                    type="text"
                    value={String(selectedNode.data?.label || '')}
                    onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: e.target.value } })}
                    className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 p-0 font-semibold text-lg placeholder-gray-400"
                    placeholder="Node Label"
                  />
                  <PenLine size={14} className="text-[#6B778C] ml-1 opacity-40 group-hover:opacity-100 transition-opacity" />
                </div>
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
                        accept=".csv,.xlsx,.xls,.json,.jsonl,.parquet"
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
                                    availableColumns: uploadResult.available_columns,
                                    format: uploadResult.detected_format,
                                    detectedFormat: uploadResult.detected_format,
                                    sheetNames: uploadResult.sheet_names,
                                    selectedSheet: uploadResult.sheet_names?.[0] || null
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
                                
                                if (uploadResult.column_types && selectedNode) {
                                  setNodeTypes(prev => ({
                                    ...prev,
                                    [selectedNode.id]: uploadResult.column_types
                                  }));
                                }

                                // Fetch sample data for the uploaded CSV using inspect endpoint
                                try {
                                  const inspectResult = await inspectNode(
                                    nodes.map(n => n.id === selectedNode.id ? updatedNode : n),
                                    edges,
                                    selectedNode.id,
                                    previewLimit
                                  );

                                  if (inspectResult.node_samples && inspectResult.node_samples[selectedNode.id]) {
                                    setNodeSamples(prev => ({
                                      ...prev,
                                      [selectedNode.id]: inspectResult.node_samples[selectedNode.id]
                                    }));
                                  }
                                } catch (error) {
                                  console.error('Failed to fetch sample data after upload:', error);
                                }

                                setExecutionMessage({ title: "File uploaded!", detail: `${file.name} ready for analysis. Discovered ${uploadResult.available_columns?.length || 0} columns and ${uploadResult.total_rows?.toLocaleString() || 0} rows.`, type: 'success' });
                                setExecutionSuccess(true);
                                setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);

                              } catch (err) {
                                setExecutionMessage({ title: "File upload failed!", detail: String(err), type: 'error' });
                                setExecutionSuccess(true);
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
                        <p className="text-xs text-gray-500">CSV/Excel/JSON/Parquet up to 1GB</p>
                      </div>
                    </label>
                  </div>

                  {/* Sheet selector for Excel files */}
                  {(selectedNode.data.config as any)?.sheetNames && (selectedNode.data.config as any)?.sheetNames.length > 1 && (
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-1">Select Sheet</label>
                      <select
                        value={(selectedNode.data.config as any)?.selectedSheet || ''}
                        onChange={(e) => {
                          const newSheet = e.target.value;
                          const updatedNode = {
                            ...selectedNode,
                            data: {
                              ...selectedNode.data,
                              config: {
                                ...(selectedNode.data.config as any),
                                selectedSheet: newSheet
                              }
                            }
                          };
                          setSelectedNode(updatedNode);
                          setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                        }}
                        className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                      >
                        {(selectedNode.data.config as any)?.sheetNames?.map((sheet: string) => (
                          <option key={sheet} value={sheet}>{sheet}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-xs font-semibold text-[#6B778C]">Server Upload Path</label>
                      <button
                        onClick={async () => {
                          if (selectedNode) {
                            try {
                              setExecutionMessage({ title: "Connecting to server...", detail: `Fetching schema and samples for ${selectedNode.data?.label || 'node'}.`, type: 'info' });
                              setExecutionSuccess(true);
                              
                              // Trigger inspection
                              const res = await inspectNode(getNodes(), getEdges(), selectedNode.id, previewLimit);
                              
                              // Populate samples if returned
                              if (res.node_samples) {
                                setNodeSamples(prev => ({ ...prev, [selectedNode.id]: res.node_samples }));
                              }
                              
                              // Populate types if returned (Crucial for DataInspectionPanel to show anything!)
                              if (res.columns) {
                                setNodeTypes(prev => ({ ...prev, [selectedNode.id]: res.columns }));
                              }
                              
                              setActiveBottomTab(0); // Data Inspection
                              setIsBottomPanelVisible(true);
                              setExecutionMessage({ title: "Ready for Inspection", detail: `Successfully loaded ${res.total_rows?.toLocaleString() || 0} rows and ${res.total_columns || 0} columns.`, type: 'success' });
                              setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                            } catch (e: any) {
                              setExecutionMessage({ title: "Inspection failed.", detail: e.message || "Could not fetch data sample.", type: 'error' });
                              setExecutionSuccess(true);
                            }
                          }
                        }}
                        className="text-[10px] font-bold text-[#0052CC] hover:text-white hover:bg-[#0052CC] flex items-center gap-1 bg-[#0052CC]/5 px-2.5 py-1 rounded transition-all shadow-sm active:scale-95 border border-[#0052CC]/10 hover:border-[#0052CC] hover:shadow-md focus:outline-none focus:ring-1 focus:ring-[#0052CC]/30"
                      >
                        <Microscope size={12} />
                        INSPECT
                      </button>
                    </div>
                    <input type="text" data-testid="file-path-input" readOnly value={String((selectedNode.data.config as any)?.file_path || "None uploaded")} className="w-full bg-gray-50 border border-[#DFE1E6] rounded-md px-3 py-2 text-xs text-[#6B778C] font-mono" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Parsing Format</label>
                    <div className="flex flex-col gap-2">
                       <select
                         name="format"
                         data-testid="format-select"
                         value={String((selectedNode.data.config as any)?.format || 'flat')}
                         onChange={(e) => {
                           const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), format: e.target.value } } };
                           setSelectedNode(updatedNode);
                           setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                         }}
                         className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                       >
                         <option value="flat">Standard Flat CSV (Rows & Columns)</option>
                         <option value="kv">Key-Value Pairs (id, key:val, timestamp)</option>
                       </select>
                       {(selectedNode.data.config as any)?.detectedFormat && (
                         <div className="flex items-center gap-1.5 px-2 py-1 bg-amber-50 border border-amber-200 rounded text-[10px] text-amber-700 font-medium animate-in fade-in zoom-in duration-300">
                           <Microscope size={12} />
                           Auto-detected: <span className="font-bold uppercase">{(selectedNode.data.config as any).detectedFormat}</span>
                         </div>
                       )}
                    </div>
                  </div>
                </div>
              )}

              {selectedNode.type === 'default' && typeof selectedNode.data?.config === 'object' && selectedNode.data.config !== null && (
                <div className="space-y-4">
                  {/* Filter Records UI */}
                  {selectedNode.data.subtype === 'filter' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                        <label className="text-[10px] uppercase font-bold text-[#6B778C]">Filter Configuration</label>
                        <button
                          onClick={() => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), isAdvanced: !(selectedNode.data.config as any)?.isAdvanced } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className={`text-[9px] px-2 py-0.5 rounded font-bold transition-all border shadow-sm flex items-center gap-1 ${(selectedNode.data.config as any)?.isAdvanced
                              ? 'bg-[#0052CC] text-white border-[#0052CC] hover:bg-[#0065FF] hover:border-[#0065FF]'
                              : 'bg-white text-[#6B778C] border-[#DFE1E6] hover:bg-gray-50 hover:text-[#171717] hover:border-[#C1C7D0]'
                            }`}
                        >
                          <SlidersHorizontal size={8} />
                          {(selectedNode.data.config as any)?.isAdvanced ? 'SQL MODE' : 'SIMPLE'}
                        </button>
                      </div>

                      {(selectedNode.data.config as any)?.isAdvanced ? (
                        <div>
                          <label className="block text-xs font-semibold text-[#6B778C] mb-1">Raw WHERE Clause</label>
                          <textarea
                            rows={3}
                            placeholder="e.g. status = 'active' OR priority = 'high'"
                            value={String((selectedNode.data.config as any)?.customWhere || '')}
                            onChange={(e) => {
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), customWhere: e.target.value } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }}
                            className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-[#0052CC]"
                          />
                          <p className="text-[10px] text-[#6B778C] mt-1 italic">Write the condition after the WHERE keyword.</p>
                        </div>
                      ) : (
                        <>
                          <div>
                            <label className="block text-xs font-semibold text-[#6B778C] mb-1">Column to Filter</label>
                            <select
                              name="column"
                              data-testid="column-select"
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
                              name="operator"
                              data-testid="operator-select"
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
                                name="value"
                                data-testid="value-input"
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
                      <SqlPreview sql={buildSql('filter', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Combine Datasets UI */}
                  {selectedNode.data.subtype === 'combine' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Merge Type</label>
                        <select
                          name="joinType"
                          data-testid="join-type-select"
                          value={String((selectedNode.data.config as Record<string, unknown>)?.joinType || 'inner')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), joinType: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <optgroup label="Join (Combine Columns)">
                            <option value="inner">Inner Join (Matched rows only)</option>
                            <option value="left">Left Join (All from first input)</option>
                            <option value="right">Right Join (All from second input)</option>
                            <option value="full">Full Outer Join (All rows)</option>
                          </optgroup>
                          <optgroup label="Append (Combine Rows)">
                            <option value="union">Union (Merge unique rows)</option>
                            <option value="union_all">Union All (Merge all rows)</option>
                          </optgroup>
                        </select>
                      </div>

                      {/* Columns settings ONLY shown for Joins, not Unions */}
                      {!['union', 'union_all', 'append'].includes(String((selectedNode.data.config as any)?.joinType || 'inner')) && (
                        <div className="bg-[#F4F5F7] p-3 rounded-md space-y-3">
                          <h4 className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">Join Conditions</h4>
                          <div className="grid grid-cols-2 gap-3 items-center">
                            <div>
                              <label className="block text-[9px] font-bold text-[#6B778C] mb-1 tracking-tighter uppercase">Left Input Key</label>
                              <select
                                name="leftColumn"
                                data-testid="left-column-select"
                                value={String((selectedNode.data.config as any)?.leftColumn || '')}
                                onChange={(e) => {
                                  const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), leftColumn: e.target.value } } };
                                  setSelectedNode(updatedNode);
                                  setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                                className="w-full border border-[#DFE1E6] rounded-md px-2 py-1.5 text-xs text-[#171717]"
                              >
                                <option value="">Select col...</option>
                                {getUpstreamColumns(getEdges().filter(e => e.target === selectedNode.id)[0]?.source).map((col: string) => (
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
                                name="rightColumn"
                                data-testid="right-column-select"
                                value={String((selectedNode.data.config as any)?.rightColumn || '')}
                                onChange={(e) => {
                                  const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), rightColumn: e.target.value } } };
                                  setSelectedNode(updatedNode);
                                  setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                                className="w-full border border-[#DFE1E6] rounded-md px-2 py-1.5 text-xs text-[#171717]"
                              >
                                <option value="">Select col...</option>
                                {getUpstreamColumns(getEdges().filter(e => e.target === selectedNode.id)[1]?.source).map((col: string) => (
                                  <option key={col} value={col}>{col}</option>
                                ))}
                              </select>
                            </div>
                          </div>
                        </div>
                      )}

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
                                  name="groupBy"
                                  data-testid="groupby-checkbox"
                                  className="w-4 h-4 rounded border-[#DFE1E6] text-[#0052CC]"
                                  checked={isChecked}
                                  onChange={(e) => {
                                    const currentList = String((selectedNode.data.config as any)?.groupBy || '').split(',').map(s => s.trim()).filter(s => s);
                                    const newList = e.target.checked ? [...currentList, col] : currentList.filter(s => s !== col);
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
                              name="agg-column"
                              data-testid="agg-column-select"
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
                                name="agg-operation"
                                data-testid="agg-operation-select"
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
                                name="agg-alias"
                                data-testid="agg-alias-input"
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
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
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
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
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
                                  const newList = e.target.checked ? [...currentList, col] : currentList.filter(s => s !== col);
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

                  {/* Pivot Data UI */}
                  {selectedNode.data.subtype === 'pivot' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">On (Column to Pivot)</label>
                        <select
                          value={String((selectedNode.data.config as any)?.on || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), on: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="">Select column to become headers...</option>
                          {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Using (Aggregation)</label>
                        <input
                          value={String((selectedNode.data.config as any)?.using || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), using: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. sum(amount)"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Group By</label>
                        <input
                          value={String((selectedNode.data.config as any)?.groupBy || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), groupBy: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. department, date"
                        />
                      </div>
                      <SqlPreview sql={buildSql('pivot', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Unpivot Data UI */}
                  {selectedNode.data.subtype === 'unpivot' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">On (Columns to Unpivot)</label>
                        <input
                          value={String((selectedNode.data.config as any)?.on || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), on: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. Q1, Q2, Q3, Q4"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Into Name (Header Column)</label>
                        <input
                          value={String((selectedNode.data.config as any)?.intoName || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), intoName: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. quarter"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Into Value (Value Column)</label>
                        <input
                          value={String((selectedNode.data.config as any)?.intoValue || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), intoValue: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. revenue"
                        />
                      </div>
                      <SqlPreview sql={buildSql('unpivot', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Sample Data UI */}
                  {selectedNode.data.subtype === 'sample' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Method</label>
                        <select
                          value={String((selectedNode.data.config as any)?.method || 'PERCENT')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), method: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        >
                          <option value="PERCENT">PERCENT (%)</option>
                          <option value="ROWS">ROWS (Count)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Value</label>
                        <input
                          type="number"
                          value={Number((selectedNode.data.config as any)?.value || 10)}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), value: Number(e.target.value) } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                        />
                      </div>
                      <SqlPreview sql={buildSql('sample', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Unnest / JSON UI */}
                  {selectedNode.data.subtype === 'unnest' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Column to Unnest</label>
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
                          {getUpstreamColumns(selectedNode.id).map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Output Alias</label>
                        <input
                          value={String((selectedNode.data.config as any)?.alias || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), alias: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. unnested_value"
                        />
                      </div>
                      <SqlPreview sql={buildSql('unnest', selectedNode.data.config as any)} />
                    </div>
                  )}

                  {/* Remote File / S3 UI */}
                  {selectedNode.data.subtype === 'remote_file' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Remote URL (HTTP / S3)</label>
                        <input
                          value={String((selectedNode.data.config as any)?.url || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), url: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="https://... or s3://..."
                        />
                      </div>
                    </div>
                  )}

                  {/* Write to DB UI */}
                  {selectedNode.data.subtype === 'db_write' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-[#6B778C] mb-1">Target Table Name</label>
                        <input
                          value={String((selectedNode.data.config as any)?.tableName || '')}
                          onChange={(e) => {
                            const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), tableName: e.target.value } } };
                            setSelectedNode(updatedNode);
                            setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                          }}
                          className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                          placeholder="e.g. my_processed_data"
                        />
                      </div>
                    </div>
                  )}

                  {/* Custom SQL UI */}
                  {selectedNode.data.subtype === 'raw_sql' && (
                    <div className="space-y-3">
                      <div>
                        <div className="mb-2">
                          <label className="block text-[10px] uppercase font-bold text-[#6B778C] tracking-wider mb-2">Direct DuckDB SQL</label>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <button
                              onClick={async () => {
                                try {
                                  const sql = (selectedNode.data.config as any)?.sql || '';
                                  const columns = getUpstreamColumns(selectedNode.id);
                                  const incoming = getEdges().find(e => e.target === selectedNode.id);
                                  const sourceId = incoming?.source;
                                  const schema = sourceId ? nodeTypes[sourceId] : null;
                                  const preparedColumns = schema ? schema.map(c => JSON.stringify(c)) : columns;
                                  
                                  const result = await validateSql(sql, 'input_table', preparedColumns);
                                  if (result.status === 'success') {
                                    setExecutionMessage({ title: "SQL Valid", detail: "Query structure is correct.", type: 'success' });
                                    setExecutionSuccess(true);
                                    setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                                  } else {
                                    let message = result.message;
                                    if (message.includes('sum(VARCHAR)') || message.includes('No function matches the given name and argument types')) {
                                      message += '\n\nTIP: Try RUNNING the pipeline first to update the schema metadata, or use explicit casting: SUM(TRY_CAST(col AS DOUBLE)).';
                                    }
                                    setExecutionMessage({ title: "SQL Error", detail: message, type: 'error' });
                                    setExecutionSuccess(true);
                                    setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 8000); 
                                  }
                                } catch (e: any) {
                                  setExecutionMessage({ title: "Validation Error", detail: e.message, type: 'error' });
                                  setExecutionSuccess(true);
                                  setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 6000);
                                }
                              }}
                              className="text-[10px] bg-[#F4F5F7] hover:bg-[#EBECF0] text-[#42526E] px-2 py-1 rounded font-bold transition-all flex items-center gap-1.5"
                            >
                              <Search size={12} className="text-[#6B778C]" />
                              VALIDATE
                            </button>
                            
                            {/* EXECUTE BUTTON - NEW */}
                            <button
                              onClick={async () => {
                                try {
                                  const sql = (selectedNode.data.config as any)?.sql || '';
                                  setIsCustomSqlExecuting(true);
                                  setCustomSqlPreviewResult(null);
                                  const result = await previewSql(nodes, edges, selectedNode.id, sql);
                                  if (result.status === 'error') {
                                    setExecutionMessage({ title: "SQL Preview Error", detail: result.message, type: 'error' });
                                    setExecutionSuccess(true);
                                    setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 6000);
                                  } else {
                                    setCustomSqlPreviewResult(result);
                                  }
                                } catch (e: any) {
                                  setExecutionMessage({ title: "SQL Preview Error", detail: e.message, type: 'error' });
                                  setExecutionSuccess(true);
                                  setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 6000);
                                } finally {
                                  setIsCustomSqlExecuting(false);
                                }
                              }}
                              className="text-[10px] bg-[#6554C0]/10 hover:bg-[#6554C0]/20 text-[#6554C0] px-2 py-1 rounded font-bold transition-all flex items-center gap-1.5"
                            >
                              {isCustomSqlExecuting ? <RefreshCw size={12} className="animate-spin" /> : <Play size={12} />}
                              EXECUTE
                            </button>
                            
                            {/* FIX WITH AI BUTTON */}
                            <button
                              onClick={async () => {
                                const currentSql = (selectedNode.data.config as any)?.sql || '';
                                if (!currentSql) return;
                                
                                setExecutionMessage({ title: "AI Fixing...", detail: "Asking AI to fix your SQL query structure.", type: 'info' });
                                setExecutionSuccess(true);

                                try {
                                  // Reuse AI credentials from localStorage (matching AiSqlBuilderPanel logic)
                                  const providerId = localStorage.getItem('ai_sql_provider') || 'google';
                                  const apiKey = localStorage.getItem(`ai_sql_key_${providerId}`);
                                  if (!apiKey) throw new Error("No AI API key found. Please set one in the AI SQL Builder sidebar.");
                                  
                                  const cols = getUpstreamColumns(selectedNode.id);
                                  const promptText = `My DuckDB SQL query is failing with an error. 
Current SQL: ${currentSql}
Schema: ${cols.join(', ')}
Please fix the SQL. Return ONLY the raw SQL query.`;

                                  setAiSqlInitialPrompt(promptText);
                                  setActiveBottomTab(1); // AI SQL Builder
                                  setIsBottomPanelVisible(true);
                                  
                                  setExecutionMessage({ title: "Focusing AI Builder", detail: "SQL and context description moved to AI SQL Builder sidebar.", type: 'success' });
                                  setExecutionSuccess(true);
                                  setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                                } catch (e: any) {
                                  setExecutionMessage({ title: "Fix Failed", detail: e.message, type: 'error' });
                                  setExecutionSuccess(true);
                                }
                              }}
                              className="text-[10px] bg-[#EBF4FF] hover:bg-[#B3D4FF] text-[#0052CC] px-2 py-1 rounded font-bold transition-all flex items-center gap-1.5"
                            >
                              <Wand2 size={12} className="text-[#0052CC]" />
                              AI FIX
                            </button>
                            <button
                              onClick={() => {
                                const sql = (selectedNode.data.config as any)?.sql || '';
                                navigator.clipboard.writeText(sql);
                                setExecutionMessage({ title: "Copied!", detail: "SQL query copied to clipboard.", type: 'success' });
                                setExecutionSuccess(true);
                                setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                              }}
                              className="text-[10px] bg-[#F4F5F7] hover:bg-[#EBECF0] text-[#42526E] px-2 py-1 rounded font-bold transition-all flex items-center gap-1.5"
                            >
                              <Copy size={12} className="text-[#6B778C]" />
                              COPY
                            </button>
                            <button
                              onClick={() => {
                                const sql = (selectedNode.data.config as any)?.sql || '';
                                
                                // Improved beautifier that respects strings and comments
                                const tokens = sql.split(/('(?:''|[^'])*'|--.*(?:\n|$))/g);
                                const beautified = tokens.map((token: string) => {
                                  if (!token) return '';
                                  if (token.startsWith("'") || token.startsWith("--")) return token;
                                  
                                  // Format keywords and commas in code parts
                                  return token
                                    .replace(/\s+/g, ' ')
                                    .replace(/\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|UNION|WITH|SET|VALUES|CASE|WHEN|THEN|ELSE|END|AS)\b/gi, (match: string) => `\n${match.toUpperCase()}`)
                                    .replace(/,/g, ',\n  ');
                                }).join('')
                                  .replace(/\n\s*\n/g, '\n') // Remove extra empty lines
                                  .replace(/^\s*\n/g, '') // Remove leading newline
                                  .trim();
                                
                                const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sql: beautified } } };
                                setSelectedNode(updatedNode);
                                setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                setExecutionMessage({ title: "Beautified!", detail: "SQL query has been formatted.", type: 'success' });
                                setExecutionSuccess(true);
                                setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                              }}
                              className="text-[10px] bg-[#F4F5F7] hover:bg-[#EBECF0] text-[#42526E] px-2 py-1 rounded font-bold transition-all flex items-center gap-1.5"
                            >
                              <SlidersHorizontal size={12} className="text-[#6B778C]" />
                              BEAUTIFY
                            </button>
                          </div>
                        </div>
                        <div className="p-2 mb-2 bg-[#EBF4FF] text-[10px] text-[#0052CC] rounded leading-relaxed border border-[#B3D4FF]">
                          Use <b>{"{{input}}"}</b> to reference the incoming dataset table name.
                        </div>
                        <textarea
                          rows={12}
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

                      {/* Preview Results Table */}
                      {customSqlPreviewResult && (
                        <div className="border border-[#DFE1E6] rounded-md overflow-hidden transition-all animate-in fade-in slide-in-from-top-2">
                          <div className="bg-[#FAFBFC] border-b border-[#DFE1E6] px-3 py-2 flex items-center justify-between">
                            <span className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">Result Preview ({customSqlPreviewResult.row_count} rows)</span>
                            <button onClick={() => setCustomSqlPreviewResult(null)} className="text-[#6B778C] hover:text-[#171717]">
                              <X size={14} />
                            </button>
                          </div>
                          <div className="overflow-x-auto max-h-80 custom-scrollbar">
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="bg-gray-50 sticky top-0 z-10 shadow-sm">
                                  {customSqlPreviewResult.columns.map((col: string) => (
                                    <th key={col} className="px-3 py-2 text-[10px] font-bold text-[#6B778C] uppercase tracking-wider border-b border-[#DFE1E6] whitespace-nowrap">{col}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-[#DFE1E6]">
                                {customSqlPreviewResult.preview.map((row: any, i: number) => (
                                  <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                                    {customSqlPreviewResult.columns.map((col: string) => (
                                      <td key={col} className="px-3 py-1.5 text-[11px] text-[#171717] font-mono whitespace-nowrap">{String(row[col])}</td>
                                    ))}
                                  </tr>
                                ))}
                                {customSqlPreviewResult.preview.length === 0 && (
                                  <tr>
                                    <td colSpan={customSqlPreviewResult.columns.length} className="px-3 py-8 text-center text-xs text-[#6B778C]">No results returned.</td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

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
                        <div key={idx} className="p-3 bg-gray-50 border rounded-md space-y-3 relative overflow-hidden">
                          <div className="flex items-center justify-between border-b border-gray-200 pb-2 mb-1">
                            <span className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider">Step {idx + 1}</span>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  const conds = [...(selectedNode.data.config as any).conditions];
                                  conds[idx].isAdvanced = !conds[idx].isAdvanced;
                                  const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                  setSelectedNode(updatedNode);
                                  setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                                className={`text-[9px] px-2 py-0.5 rounded font-bold transition-all border shadow-sm flex items-center gap-1 ${c.isAdvanced
                                    ? 'bg-[#0052CC] text-white border-[#0052CC] hover:bg-[#0065FF] hover:border-[#0065FF]'
                                    : 'bg-white text-[#6B778C] border-[#DFE1E6] hover:bg-gray-50 hover:text-[#171717] hover:border-[#C1C7D0]'
                                  }`}
                              >
                                <SlidersHorizontal size={8} />
                                {c.isAdvanced ? 'SQL MODE' : 'SIMPLE'}
                              </button>
                              <button className="p-1 text-red-400 hover:bg-red-50 rounded" onClick={() => {
                                const conds = [...(selectedNode.data.config as any).conditions];
                                conds.splice(idx, 1);
                                const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                setSelectedNode(updatedNode);
                                setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                              }}><Trash2 size={12} /></button>
                            </div>
                          </div>

                          {(c.isAdvanced || (c.isAdvanced === undefined && c.when)) ? (
                            <div>
                              <label className="text-[9px] uppercase font-bold text-[#6B778C]">When (SQL Condition)</label>
                              <input
                                value={c.when}
                                onChange={(e) => {
                                  const conds = [...(selectedNode.data.config as any).conditions];
                                  conds[idx].when = e.target.value;
                                  const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                  setSelectedNode(updatedNode);
                                  setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                }}
                                className="w-full text-xs p-1.5 border rounded font-mono bg-white"
                                placeholder="age > 20"
                              />
                            </div>
                          ) : (
                            <div className="space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <div>
                                  <label className="text-[9px] uppercase font-bold text-[#6B778C]">Column</label>
                                  <select
                                    value={c.column || ''}
                                    onChange={(e) => {
                                      const conds = [...(selectedNode.data.config as any).conditions];
                                      conds[idx].column = e.target.value;
                                      conds[idx].when = getConditionSql(conds[idx].column, conds[idx].operator || '==', conds[idx].value || '');
                                      const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                      setSelectedNode(updatedNode);
                                      setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                    }}
                                    className="w-full text-xs p-1 border rounded bg-white"
                                  >
                                    <option value="">Select...</option>
                                    {getUpstreamColumns(selectedNode.id).map(col => <option key={col} value={col}>{col}</option>)}
                                  </select>
                                </div>
                                <div>
                                  <label className="text-[9px] uppercase font-bold text-[#6B778C]">Operator</label>
                                  <select
                                    value={c.operator || '=='}
                                    onChange={(e) => {
                                      const conds = [...(selectedNode.data.config as any).conditions];
                                      conds[idx].operator = e.target.value;
                                      conds[idx].when = getConditionSql(conds[idx].column || '', conds[idx].operator, conds[idx].value || '');
                                      const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                      setSelectedNode(updatedNode);
                                      setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                    }}
                                    className="w-full text-xs p-1 border rounded bg-white"
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
                              </div>
                              {!['is_null', 'is_not_null'].includes(c.operator) && (
                                <div>
                                  <label className="text-[9px] uppercase font-bold text-[#6B778C]">Value</label>
                                  <input
                                    value={c.value || ''}
                                    onChange={(e) => {
                                      const conds = [...(selectedNode.data.config as any).conditions];
                                      conds[idx].value = e.target.value;
                                      conds[idx].when = getConditionSql(conds[idx].column || '', conds[idx].operator || '==', conds[idx].value);
                                      const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                                      setSelectedNode(updatedNode);
                                      setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                                    }}
                                    className="w-full text-xs p-1.5 border rounded bg-white"
                                    placeholder="Value..."
                                  />
                                </div>
                              )}
                            </div>
                          )}

                          <div>
                            <label className="text-[9px] uppercase font-bold text-[#6B778C]">Then (Result)</label>
                            <input value={c.then} onChange={(e) => {
                              const conds = [...(selectedNode.data.config as any).conditions];
                              conds[idx].then = e.target.value;
                              const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                              setSelectedNode(updatedNode);
                              setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
                            }} className="w-full text-xs p-1.5 border rounded bg-white" placeholder="'Adult' or 100" />
                          </div>
                        </div>
                      ))}
                      <button onClick={() => {
                        const conds = [...((selectedNode.data.config as any)?.conditions || [])];
                        conds.push({ when: '', then: '', column: '', operator: '==', value: '', isAdvanced: false });
                        const updatedNode = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), conditions: conds } } };
                        setSelectedNode(updatedNode);
                        setNodes((nds) => nds.map((n) => n.id === updatedNode.id ? updatedNode : n));
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
                                  className={`px-3 py-2 text-xs font-bold transition-colors ${isActive
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
                          name="column"
                          data-testid="sort-column-select"
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
                          name="direction"
                          data-testid="sort-direction-select"
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
                        name="count"
                        data-testid="limit-input"
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
                      name="format"
                      data-testid="output-format-select"
                      value={String((selectedNode.data.config as Record<string, unknown>)?.format || 'CSV')}
                      onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), format: e.target.value } } })}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC]"
                    >
                      <option value="CSV">CSV Document (.csv)</option>
                      <option value="Excel">Excel Document (.xlsx)</option>
                      <option value="JSON">JSON Data (.json)</option>
                      <option value="Parquet">Parquet File (.parquet)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">File Name</label>
                    <input
                      type="text"
                      name="filename"
                      data-testid="output-filename-input"
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

              {selectedNode.type === 'output' && selectedNode.data?.subtype === 'report' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Report Title</label>
                    <input
                      type="text"
                      value={String((selectedNode.data.config as any)?.title || 'Data Analysis Report')}
                      onChange={(e) => {
                        const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), title: e.target.value } } };
                        setSelectedNode(updated);
                        setNodes((nds) => nds.map((n) => n.id === updated.id ? updated : n));
                      }}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#6B778C] mb-1">Description</label>
                    <textarea
                      rows={2}
                      value={String((selectedNode.data.config as any)?.description || '')}
                      onChange={(e) => {
                        const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), description: e.target.value } } };
                        setSelectedNode(updated);
                        setNodes((nds) => nds.map((n) => n.id === updated.id ? updated : n));
                      }}
                      className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-[#6B778C] uppercase mb-2">Sections</label>
                    <div className="space-y-3">
                      {((selectedNode.data.config as any)?.sections || []).map((sec: any, idx: number) => (
                        <div key={idx} className="p-3 bg-gray-50 border border-[#DFE1E6] rounded-md relative group">
                          <button
                            onClick={() => {
                              const sections = [...((selectedNode.data.config as any).sections)];
                              sections.splice(idx, 1);
                              const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sections } } };
                              setSelectedNode(updated);
                              setNodes((nds) => nds.map((n) => n.id === updated.id ? updated : n));
                            }}
                            className="absolute -top-1.5 -right-1.5 p-1 bg-white border border-red-200 text-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                          ><Trash2 size={10} /></button>

                          <input
                            placeholder="Section Heading"
                            className="w-full text-xs font-bold border-none bg-transparent mb-2 focus:ring-0 p-0"
                            value={sec.heading}
                            onChange={(e) => {
                              const sections = [...((selectedNode.data.config as any).sections)];
                              sections[idx].heading = e.target.value;
                              const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sections } } };
                              setSelectedNode(updated);
                            }}
                          />

                          <select
                            className="w-full text-[10px] border rounded p-1 mb-2"
                            value={sec.type}
                            onChange={(e) => {
                              const sections = [...((selectedNode.data.config as any).sections)];
                              sections[idx].type = e.target.value;
                              const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sections } } };
                              setSelectedNode(updated);
                            }}
                          >
                            <option value="table">Data Table</option>
                            <option value="stats">Summary Statistics</option>
                            <option value="text">Custom Remarks</option>
                          </select>

                          {sec.type === 'text' && (
                            <textarea
                              placeholder="Example: Total records processed: {{row_count}}"
                              className="w-full text-[10px] border rounded p-2 italic"
                              rows={2}
                              value={sec.content}
                              onChange={(e) => {
                                const sections = [...((selectedNode.data.config as any).sections)];
                                sections[idx].content = e.target.value;
                                const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sections } } };
                                setSelectedNode(updated);
                              }}
                            />
                          )}
                        </div>
                      ))}
                      <button
                        onClick={() => {
                          const sections = [...((selectedNode.data.config as any)?.sections || [])];
                          sections.push({ heading: 'New Section', type: 'table', content: '' });
                          const updated = { ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), sections } } };
                          setSelectedNode(updated);
                          setNodes((nds) => nds.map((n) => n.id === updated.id ? updated : n));
                        }}
                        className="w-full py-1.5 border border-dashed text-[10px] uppercase font-bold text-[#0052CC] hover:bg-blue-50 border-[#0052CC] rounded"
                      >+ Add Section</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-1">Format</label>
                      <select
                        value={String((selectedNode.data.config as any)?.format || 'PDF')}
                        onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), format: e.target.value } } })}
                        className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs"
                      >
                        <option value="PDF">PDF Report</option>
                        <option value="Markdown">Markdown</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-[#6B778C] mb-1">Font</label>
                      <select
                        value={String((selectedNode.data.config as any)?.font || 'NanumGothic')}
                        onChange={(e) => setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: { ...(selectedNode.data.config as any), font: e.target.value } } })}
                        className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-xs"
                      >
                        <option value="NanumGothic">NanumGothic (KR)</option>
                        <option value="Helvetica">Helvetica (EN)</option>
                      </select>
                    </div>
                  </div>

                  <button
                    onClick={async () => {
                      try {
                        const res = await generateReport(getNodes(), getEdges(), selectedNode.data.config);
                        if (res.report_url) {
                          const link = document.createElement('a');
                          const baseUrl = getBackendUrl().replace(/\/$/, '');
                          link.href = res.report_url.startsWith('http') ? res.report_url : `${baseUrl}${res.report_url}`;
                          link.setAttribute('download', '');
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }
                        setExecutionMessage({ title: "Report Generated", detail: "The file is being downloaded.", type: 'success' });
                        setExecutionSuccess(true);
                        setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
                      } catch (err) {
                        setExecutionMessage({ title: "Report Failed", detail: (err as any).message || "Report generation failed!", type: 'error' });
                        setExecutionSuccess(true);
                        setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 6000);
                        console.error(err);
                      }
                    }}
                    className="w-full py-2 bg-[#36B37E] text-white font-bold rounded shadow-sm hover:bg-[#36B37E]/90 flex items-center justify-center gap-2"
                  >
                    <FileText size={14} />
                    Generate Report
                  </button>
                </div>
              )}
            </div>
            <div className="p-4 border-t border-[#DFE1E6]">
              <button
                onClick={saveNodeChanges}
                disabled={saveSuccess}
                className={`w-full px-4 py-2 text-white text-sm font-medium rounded-md transition-all shadow-sm flex items-center justify-center space-x-2 ${saveSuccess ? 'bg-[#36B37E]' : 'bg-[#0052CC] hover:bg-[#0065FF]'}`}
              >
                {saveSuccess ? (
                  <>
                    <Fingerprint size={16} />
                    <span>Saved to Canvas!</span>
                  </>
                ) : (
                  <span>Save Changes</span>
                )}
              </button>
            </div>
          </aside>
        )}
      </div>

      {/* Modals & Global Overlays - Still inside the root div */}



      {/* Rename Modal */}
      {isRenameModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 border border-[#DFE1E6] animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-bold text-[#172B4D] mb-4">Rename Pipeline</h3>
            <p className="text-sm text-[#6B778C] mb-4">Update the name of your data processing pipeline.</p>
            <input
              autoFocus
              type="text"
              className="w-full border border-[#DFE1E6] rounded-md px-3 py-2 text-sm text-[#171717] focus:ring-[#0052CC] focus:border-[#0052CC] mb-6 outline-none"
              placeholder="e.g., New Pipeline Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleRenameWorkflow(); }}
            />
            <div className="flex justify-end space-x-3">
              <button 
                onClick={() => {
                  setIsRenameModalOpen(false);
                  setNewName("");
                }} 
                className="px-4 py-2 text-sm text-[#6B778C] hover:bg-gray-100 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRenameWorkflow}
                disabled={!newName || newName === currentPipelineName}
                className="px-4 py-2 text-sm bg-[#0052CC] text-white font-medium rounded-md hover:bg-[#0065FF] disabled:opacity-50 transition-colors shadow-sm"
              >
                Rename Pipeline
              </button>
            </div>
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
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg border border-[#DFE1E6] animate-in fade-in zoom-in duration-200 flex flex-col max-h-[calc(100vh-2rem)]">
            <div className="p-6 pb-2 flex-shrink-0 flex items-center justify-between">
              <h3 className="text-lg font-bold text-[#172B4D] font-inter">Open Pipeline</h3>
              <div className="flex items-center gap-2">
                <input id="workflow-import-input" type="file" accept=".json,application/json" onChange={handleImportSelectedFile} className="hidden" />
                <label htmlFor="workflow-import-input" className="px-3 py-2 bg-[#FAFBFC] border border-[#DFE1E6] rounded-md text-sm text-[#42526E] cursor-pointer">Choose file</label>
                <button
                  onClick={handleImportConfirm}
                  disabled={!importFile}
                  className="px-3 py-2 bg-[#0052CC] text-white rounded-md text-sm font-medium disabled:opacity-50"
                >
                  Import
                </button>
              </div>
            </div>
            {importError && (
              <div className="px-6 pb-2">
                <p className="text-sm text-red-600">{importError}</p>
              </div>
            )}
            {availableWorkflows.length === 0 ? (
              <div className="px-6 pb-6 flex-shrink-0">
                <p className="text-sm text-[#6B778C]">No saved pipelines found on server.</p>
              </div>
            ) : (
              <div className="px-6 pb-4 flex-1 overflow-y-auto min-h-0">
                <div className="space-y-2 pr-1">
                  {availableWorkflows.map(name => (
                    <div key={name} className="flex items-center justify-between space-x-3">
                      {renamingWorkflow === name ? (
                        <div className="flex-1 flex items-center gap-2">
                          <input
                            autoFocus
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); confirmRenameWorkflow(name); } if (e.key === 'Escape') { cancelRename(); } }}
                            className="flex-1 px-3 py-2 border border-[#DFE1E6] rounded-md text-sm"
                          />
                          <button onClick={(e) => { e.stopPropagation(); confirmRenameWorkflow(name); }} disabled={renameLoading} className="px-3 py-2 bg-[#0052CC] text-white rounded-md text-sm">{renameLoading ? '...' : 'OK'}</button>
                          <button onClick={(e) => { e.stopPropagation(); cancelRename(); }} className="px-3 py-2 bg-white border border-[#DFE1E6] rounded-md text-sm">Cancel</button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleLoadWorkflow(name)}
                          className="flex-1 text-left px-4 py-3 text-sm text-[#172B4D] hover:bg-[#F4F5F7] border border-[#DFE1E6] rounded-md transition-all flex items-center group hover:border-[#0052CC]"
                        >
                          <span className="font-medium">{name}</span>
                        </button>
                      )}

                      <div className="flex items-center gap-2">
                        <button
                          onClick={async (e) => { e.stopPropagation(); try { const data = await loadWorkflowGraph(name); const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${name}.json`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); } catch (err) { setExecutionMessage({ title: 'Export failed', detail: (err as any).message || 'Could not export workflow', type: 'error' }); setExecutionSuccess(true); } }}
                          className="px-3 py-2 bg-[#EDEFFF] text-[#0052CC] rounded-md text-sm border border-[#DFE1E6]"
                          title="Download JSON"
                        >
                          <FileDown size={14} />
                        </button>

                        <button
                          onClick={(e) => { e.stopPropagation(); startRenameWorkflow(name); }}
                          className="px-3 py-2 bg-white border border-[#DFE1E6] rounded-md text-sm"
                          title="Rename"
                        >
                          <PenLine size={14} />
                        </button>

                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteWorkflow(name); }}
                          disabled={deleteLoading === name}
                          className="px-3 py-2 bg-white border border-[#FEE2E2] text-red-600 rounded-md text-sm"
                          title="Delete"
                        >
                          {deleteLoading === name ? '...' : <Trash2 size={14} />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="p-6 pt-4 border-t border-[#DFE1E6] flex justify-end flex-shrink-0">
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

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 border border-[#DFE1E6] animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
            <SettingsPanel onClose={() => setIsSettingsOpen(false)} />
          </div>
        </div>
      )}

      {/* Global Tooltip */}
      {tooltip && (
        <div
          className="fixed z-[9999] pointer-events-none tooltip-animate"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: (tooltip as any).isHeader ? 'translateX(-50%)' : 'translate(0, -50%)'
          }}
        >
            <div className="relative bg-[#1E1E2E] text-white p-3 rounded-lg shadow-2xl border border-[#313244] w-64 font-inter">
              {/* Arrow */}
              <div className={`absolute border-[8px] border-transparent ${(tooltip as any).isHeader
                  ? 'border-b-[#1E1E2E] -top-[16px] left-1/2'
                  : 'border-r-[#1E1E2E] -left-[16px] top-1/2 -translate-y-1/2'
                }`}
                style={(tooltip as any).isHeader ? { transform: `translateX(calc(-50% + ${(tooltip as any).arrowOffset || 0}px))` } : {}}
              />

              <div className="text-[10px] font-bold text-[#89DCEB] mb-1 uppercase tracking-wider">{tooltip.label}</div>
              <div className="text-[11px] leading-relaxed text-[#CDD6F4]">{tooltip.text}</div>
            </div>
        </div>
      )}


      {/* Success Notification for Query Execution */}
      {executionSuccess && (
        <div data-testid="execution-success" className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-bottom-4 duration-300">
          <div className={`${executionMessage?.type === 'error' ? 'bg-[#FF5630]' : 'bg-[#36B37E]'} text-white px-6 py-3 rounded-full shadow-2xl flex items-center space-x-3 border-2 border-white/20 backdrop-blur-md`}>
            <div className="bg-white/20 p-1.5 rounded-full">
              {(() => {
                const title = executionMessage?.title || "";
                if (executionMessage?.type === 'error') return <AlertCircle size={16} />;
                if (title.includes('Copied')) return <Copy size={16} />;
                if (title.includes('SQL Valid')) return <CheckCheck size={16} />;
                if (title.includes('Beautified')) return <SlidersHorizontal size={16} />;
                if (title.includes('Saved')) return <Save size={16} />;
                if (title.includes('Report')) return <FileText size={16} />;
                return <Play size={16} fill="white" />;
              })()}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold leading-none mb-0.5 uppercase tracking-wider">
                {executionMessage?.title || (executionMessage?.type === 'error' ? 'Execution Error' : 'Query Successful')}
              </span>
              <span className={`text-[10px] opacity-90 text-white/80 ${executionMessage?.type === 'error' ? 'max-w-md line-clamp-2' : 'max-w-xs truncate'}`}>
                {executionMessage?.detail || (executionMessage?.type === 'error' ? 'Something went wrong.' : `Processed ${executionResult?.row_count?.toLocaleString()} rows successfully`)}
              </span>
            </div>
            {executionMessage?.type === 'error' && (
               <div className="flex items-center gap-1 ml-2">
                 <button 
                  onClick={() => {
                    navigator.clipboard.writeText(executionMessage.detail);
                    setExecutionMessage({ ...executionMessage, title: "Copied to clipboard!", type: 'success' });
                    setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 2000);
                  }}
                  className="hover:bg-white/20 p-1.5 rounded transition-colors group relative"
                  title="Copy full error message"
                 >
                   <Copy size={14} />
                 </button>
                 <button onClick={() => { setExecutionSuccess(false); setExecutionMessage(null); }} className="hover:bg-white/20 p-1.5 rounded transition-colors">
                   <X size={14} />
                 </button>
               </div>
            )}
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
