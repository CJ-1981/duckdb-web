"use client";

import React, { useState } from 'react';
import WorkspaceCanvas from '@/components/workflow/canvas';
import { WorkflowToolbar } from '@/components/workflow/WorkflowToolbar';
import { Play, SlidersHorizontal, FileText, FileDown, Save, Eye, ChevronRight, Code, PenLine, Plus, Trash2, Microscope, PanelBottomClose, Copy, X, CheckCheck, AlertCircle, Menu } from 'lucide-react';
import { Node, Edge, ReactFlowProvider, Panel } from '@xyflow/react';
import { useWorkflowState } from '@/hooks/useWorkflowState';
import { executeWorkflow, saveWorkflow, listSavedWorkflows, loadWorkflowGraph, inspectNode, renameWorkflow, deleteWorkflow, previewSql } from '@/lib/api-unified';
import { NodePalette, PropertiesPanel, SamplePipelines } from '@/components/workflow';
import DataInspectionPanel, { type ColumnTypeDef, type FullStats } from '@/components/panels/DataInspectionPanel';
import AiSqlBuilderPanel from '@/components/panels/AiSqlBuilderPanel';
import AiPipelineBuilderPanel from '@/components/panels/AiPipelineBuilderPanel';
import SettingsPanel from '@/components/panels/SettingsPanel';

// Mobile-specific components
import { MobileNavigation, MobileMenu } from '@/components/mobile/MobileNavigation';
import { MobileWorkflowViewer } from '@/components/mobile/MobileWorkflowViewer';
import { ExecutionStatusCard, MobileResultsCard } from '@/components/mobile/MobileResultsCard';

// Responsive utilities
import { useIsMobile, useIsTablet, useBreakpoint } from '@/lib/responsive';

interface WorkflowTab {
  id: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  nodeSamples: Record<string, any[]>;
  nodeTypes: Record<string, ColumnTypeDef[]>;
}

// ─── SQL Preview helpers ──────────────────────────────────────────────────────

interface MobileDataInspectionSectionProps {
  selectedNode: Node | null;
  nodeSamples: Record<string, any[]>;
  nodeTypes: Record<string, ColumnTypeDef[]>;
}

function MobileDataInspectionSection({ selectedNode, nodeSamples, nodeTypes }: MobileDataInspectionSectionProps): React.ReactElement | null {
  if (!selectedNode || nodeSamples[selectedNode.id] === undefined) {
    return null;
  }

  return (
    <MobileResultsCard
      title={`Data: ${selectedNode.data.label ? String(selectedNode.data.label) : 'Unknown'}`}
      data={nodeSamples[selectedNode.id] ?? []}
      columns={nodeTypes[selectedNode.id] ?? []}
      rowCount={selectedNode.data.rowCount as number | undefined}
      maxHeight="calc(100vh - 300px)"
    />
  );
}


function Dashboard() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const { nodes, setNodes, onNodesChange, edges, setEdges, onEdgesChange, history, pushToHistory, undo, redo, getNodes, getEdges } = useWorkflowState([], []);
  const [layoutCounter, setLayoutCounter] = useState(0);

  // Mobile detection and state
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const breakpoint = useBreakpoint();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [mobileResultsVisible, setMobileResultsVisible] = useState(false);

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
  const [executionSuccess, setExecutionSuccess] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<{ title: string; detail: string; type: 'success' | 'error' | 'info' } | null>(null);


  // AI SQL Sidebar State
  const [aiSqlInitialPrompt, setAiSqlInitialPrompt] = useState<string>('');
  const [previewHeight, setPreviewHeight] = useState(280);
  const [previewLimit, setPreviewLimit] = useState(50);
  const [nodeSamples, setNodeSamples] = useState<Record<string, any[]>>({});
  const [nodeColumns, setNodeColumns] = useState<Record<string, string[]>>({});
  const [nodeTypes, setNodeTypes] = useState<Record<string, ColumnTypeDef[]>>({});
  const [activeBottomTab, setActiveBottomTab] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<'nodes' | 'samples'>('nodes');
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
      // Check if this is a sample workflow
      const samplePipeline = allSamplePipelines.find((s: any) => s.name === name);
      if (samplePipeline) {
        // Load sample from public/examples directory
        const response = await fetch(samplePipeline.file);
        if (!response.ok) {
          throw new Error('Failed to load sample pipeline');
        }
        const sampleData = await response.json();

        const sanitizedNodes = (sampleData.nodes || []).map((n: any) => {
          const { className, ...rest } = n;
          return rest;
        });
        setNodes(sanitizedNodes);
        setEdges(sampleData.edges || []);
        setCurrentPipelineName(name);
        setIsLoadModalOpen(false);
        setExecutionMessage({ title: "Sample Pipeline loaded!", detail: `Loaded '${name}' sample workflow with ${sanitizedNodes.length} nodes.`, type: 'success' });
        setExecutionSuccess(true);
        setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
        return;
      }

      // Check if this is a sample workflow loaded from public/examples (legacy check)
      const sampleData = (window as any).sampleWorkflowData;
      if (sampleData) {
        // Clear the stored sample data after using it
        delete (window as any).sampleWorkflowData;

        const sanitizedNodes = (sampleData.nodes || []).map((n: any) => {
          const { className, ...rest } = n;
          return rest;
        });
        setNodes(sanitizedNodes);
        setEdges(sampleData.edges || []);
        setCurrentPipelineName(name);
        setIsLoadModalOpen(false);
        setExecutionMessage({ title: "Sample Pipeline loaded!", detail: `Loaded '${name}' sample workflow with ${sanitizedNodes.length} nodes.`, type: 'success' });
        setExecutionSuccess(true);
        setTimeout(() => { setExecutionSuccess(false); setExecutionMessage(null); }, 4000);
        return;
      }

      // Otherwise load from backend
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

  const [loadModalTab, setLoadModalTab] = useState<'workflows' | 'samples'>('workflows');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['⭐ Popular Samples']));

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const SAMPLE_CATEGORIES = {
    '👥 HR & People': [
      { name: "Employee Retention Risk", file: "/examples/hr/Employee_Retention_Risk.json", description: "Join employees with reviews to identify high-risk retention cases" }
    ],
    '🛡️ SQL Server': [
      { name: "SQL Server Sales Analysis", file: "/examples/sql-server/SQL_Server_Sales_Analysis.json", description: "Complete ETL from SQL Server to PDF report (AdventureWorks schema)" },
      { name: "Cross-DB Join (MSSQL + CSV)", file: "/examples/sql-server/Cross_DB_Join_Sample.json", description: "Join remote SQL Server data with a local CSV transaction log" }
    ],
    '🐬 MySQL': [
      { name: "MySQL E-commerce Sales", file: "/examples/mysql/MySQL_Ecommerce_Sales.json", description: "Join orders and products from MySQL for category sales analysis" }
    ],
    '📈 Finance': [
      { name: "Portfolio Rolling Returns", file: "/examples/analytics/window_functions_pipeline.json", description: "Calculate 30-day rolling averages and volatility for stock portfolios" },
      { name: "Fraud Pattern Detection", file: "/examples/comparison/cdc_diff_pipeline.json", description: "Identify suspicious transaction patterns using multi-source comparisons" }
    ],
    '📥 Data Ingestion': [
      { name: "CSV Auto-Detection Import", file: "/examples/ingestion/csv_auto_detect_pipeline.json", description: "Intelligent CSV import with schema detection and type inference" },
      { name: "PostgreSQL Bulk Export", file: "/examples/ingestion/postgres_export_pipeline.json", description: "Export PostgreSQL table to DuckDB with batch processing" },
      { name: "REST API with Pagination", file: "/examples/ingestion/api_pagination_pipeline.json", description: "Fetch data from REST API with automatic pagination and rate limiting" },
      { name: "Kafka Stream Consumer", file: "/examples/ingestion/kafka_stream_pipeline.json", description: "Consume Kafka stream with windowing and real-time aggregation" }
    ],
    '🔄 Data Transformation': [
      { name: "Data Cleaning Pipeline", file: "/examples/transformation/data_cleaning_pipeline.json", description: "Remove duplicates, handle missing values, standardize formats" },
      { name: "PIVOT Table Generator", file: "/examples/transformation/pivot_table_pipeline.json", description: "Transform long-format data into wide pivot tables" },
      { name: "Schema Evolution Migration", file: "/examples/transformation/schema_evolution_pipeline.json", description: "Handle schema changes with backward compatibility" }
    ],
    '🎯 Data Enrichment': [
      { name: "Multi-Source Join Enrichment", file: "/examples/enrichment/multi_source_join_pipeline.json", description: "Join data from database, API, and files" },
      { name: "Geocoding Enrichment", file: "/examples/enrichment/geocoding_enrichment_pipeline.json", description: "Add location-based data using geocoding API" },
      { name: "ML Model Inference", file: "/examples/enrichment/ml_inference_pipeline.json", description: "Apply machine learning model predictions to batch data" }
    ],
    '✅ Data Quality': [
      { name: "Data Validation Rules", file: "/examples/quality/data_validation_pipeline.json", description: "Validate data against business rules" },
      { name: "Data Profiling & Statistics", file: "/examples/quality/data_profiling_pipeline.json", description: "Generate profile statistics and detect anomalies" }
    ],
    '📊 Analytics & Reporting': [
      { name: "Time-Series Rollup", file: "/examples/analytics/timeseries_rollup_pipeline.json", description: "Aggregate time-series data into multiple granularities" },
      { name: "Funnel Analysis", file: "/examples/analytics/funnel_analysis_pipeline.json", description: "Track conversion through multi-step funnel" },
      { name: "A/B Test Analysis", file: "/examples/analytics/ab_test_analysis_pipeline.json", description: "Compare metrics between control and variant groups" }
    ],
    '⚡ Batch Processing': [
      { name: "Slowly Changing Dimension Type 2", file: "/examples/batch/scd_type2_pipeline.json", description: "Track historical changes with effective dates" },
      { name: "Incremental Data Sync", file: "/examples/batch/incremental_sync_pipeline.json", description: "Sync only changed records using CDC timestamps" },
      { name: "Large Dataset Parallel Processing", file: "/examples/batch/parallel_processing_pipeline.json", description: "Process large dataset in parallel chunks" }
    ],
    '🔗 API Integration': [
      { name: "Multi-Channel Attribution", file: "/examples/marketing/Multi_Channel_Attribution.json", description: "Enrich ad spend with conversion data from REST APIs" },
      { name: "JSONPlaceholder - Complete User Data", file: "/examples/api-integration/jsonplaceholder_full_pipeline.json", description: "Fetch user profiles, posts, albums, todos, and comments from JSONPlaceholder API" },
      { name: "RandomUser - Profile Generation", file: "/examples/api-integration/random_user_profiles_pipeline.json", description: "Generate random user profiles with demographics and location data" },
      { name: "REST Countries - Regional Analysis", file: "/examples/api-integration/restcountries_regions_pipeline.json", description: "Fetch country data by region with field filtering capabilities" },
      { name: "CoinGecko - Portfolio Tracker", file: "/examples/api-integration/coingecko_portfolio_pipeline.json", description: "Track cryptocurrency portfolio values with price API integration" },
      { name: "IP API - Batch Geolocation", file: "/examples/api-integration/ip_geolocation_batch_pipeline.json", description: "Process multiple IP addresses for geolocation and ISP information" },
      { name: "Cat Facts - Collection Builder", file: "/examples/api-integration/cat_facts_collection_pipeline.json", description: "Build random cat facts collection with dynamic parameters" },
      { name: "GitHub - Repository Analysis", file: "/examples/api-integration/github_repositories_pipeline.json", description: "Analyze GitHub repositories with rate limit awareness" },
      { name: "PokeAPI - Pokemon Evolution", file: "/examples/api-integration/pokeapi_pokemon_evolution_pipeline.json", description: "Fetch Pokemon evolution chains with multi-endpoint data" },
      { name: "OAuth2 Authenticated API", file: "/examples/api-integration/oauth2_api_pipeline.json", description: "Connect to OAuth2-protected API with token refresh" },
      { name: "GraphQL Query", file: "/examples/api-integration/graphql_query_pipeline.json", description: "Query GraphQL API and extract nested fields" }
    ],
    '💾 Data Export': [
      { name: "Multi-Format Export", file: "/examples/export/multi_format_export_pipeline.json", description: "Export dataset to CSV, JSON, Parquet, Excel" },
      { name: "Database Bulk Load", file: "/examples/export/database_bulk_load_pipeline.json", description: "Bulk load data into target database" }
    ],
    '🔔 Notifications': [
      { name: "Pipeline Failure Alerting", file: "/examples/notifications/pipeline_failure_alerting_pipeline.json", description: "Monitor execution and send alerts on failure" }
    ],
    '🎮 Orchestration': [
      { name: "Conditional Branching", file: "/examples/orchestration/conditional_branching_pipeline.json", description: "Route data processing based on quality checks" },
      { name: "Dynamic Parallel Tasks", file: "/examples/orchestration/dynamic_parallel_tasks_pipeline.json", description: "Generate tasks dynamically and execute in parallel" }
    ],
    '🔄 Data Comparison': [
      { name: "Data Reconciliation", file: "/examples/comparison/data_reconciliation_pipeline.json", description: "Compare two data sources and identify discrepancies" },
      { name: "CDC Diff Detection", file: "/examples/comparison/cdc_diff_pipeline.json", description: "Detect and capture changed records between snapshots" }
    ],
    '📋 Flattening': [
      { name: "Nested JSON to Table", file: "/examples/flattening/nested_json_flatten_pipeline.json", description: "Flatten complex nested JSON into tabular format" },
      { name: "XML Hierarchical Flattening", file: "/examples/flattening/xml_hierarchical_flatten_pipeline.json", description: "Flatten XML hierarchical structures" }
    ],
    '⭐ Popular Samples': [
      { name: "User Profile Enrichment", file: "/examples/sample_user_enrichment_pipeline.json", description: "Fetch user profiles from JSONPlaceholder API" },
      { name: "E-Commerce Product Scraper", file: "/examples/ecommerce_product_pipeline.json", description: "Multi-variable product scraping with filtering" },
      { name: "Social Media Analytics", file: "/examples/social_media_pipeline.json", description: "Multi-variable URL substitution and analytics" }
    ]
  };

  const allSamplePipelines = Object.values(SAMPLE_CATEGORIES).flat();

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
      if (result.node_columns) {
        setNodeColumns(result.node_columns);
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
      {/* Desktop Header - Hide on Mobile */}
      <div className="hidden md:block">
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
      </div>

      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-[#DFE1E6]">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 hover:bg-[#F4F5F7] rounded-lg"
          >
            <Menu size={20} className="text-[#0052CC]" />
          </button>
          <div>
            <h1 className="text-sm font-bold text-[#172B4D]">
              {currentPipelineName || 'New Pipeline'}
            </h1>
            <p className="text-[10px] text-[#6B778C]">{nodes.length} nodes</p>
          </div>
        </div>
      </div>

      {/* Tab Bar - Responsive */}
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
        {/* Left Sidebar - Responsive */}
        <aside className={`hidden md:flex flex-col bg-white border-r border-[#DFE1E6] transition-all duration-300 ${isSidebarCollapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-64'}`}>
          {/* Tab Switcher */}
          <div className="flex border-b border-[#DFE1E6]">
            <button
              onClick={() => setSidebarTab('nodes')}
              className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider transition-all border-b-2 ${
                sidebarTab === 'nodes'
                  ? 'border-[#0052CC] text-[#0052CC] bg-blue-50/30'
                  : 'border-transparent text-[#6B778C] hover:bg-gray-50'
              }`}
            >
              Nodes
            </button>
            <button
              onClick={() => setSidebarTab('samples')}
              className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider transition-all border-b-2 ${
                sidebarTab === 'samples'
                  ? 'border-[#0052CC] text-[#0052CC] bg-blue-50/30'
                  : 'border-transparent text-[#6B778C] hover:bg-gray-50'
              }`}
            >
              Samples
            </button>
          </div>

          <div className="flex-1 overflow-hidden flex flex-col">
            {sidebarTab === 'nodes' ? (
              <NodePalette
                isCollapsed={false}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onShowTooltip={showTooltip}
                onHideTooltip={hideTooltip}
              />
            ) : (
              <SamplePipelines
                isCollapsed={false}
                categories={SAMPLE_CATEGORIES}
                onLoadSample={handleLoadWorkflow}
              />
            )}
          </div>
        </aside>

        <main className="flex-1 relative flex flex-col h-[calc(100vh-4rem)] md:h-[calc(100vh-4rem)]">
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
              // Always show panel when a node is selected (except for notes)
              if (node && node.type !== 'note') setIsBottomPanelVisible(true);
            }}
            onAfterConnect={handleConnection}
            layoutCounter={layoutCounter}
            isBottomPanelVisible={isBottomPanelVisible && !!selectedNode}
            bottomPanelHeight={previewHeight}
            shortcutsEnabled={!isSaveModalOpen && !isLoadModalOpen && !isRenameModalOpen && !isSettingsOpen}
          >
            {selectedNode && selectedNode.type !== 'note' && isBottomPanelVisible && (
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
            {selectedNode && selectedNode.type !== 'note' && !isBottomPanelVisible && (
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

        {/* Right Sidebar - Properties Panel - Hide on Mobile */}
        <div className="hidden lg:block">
          <PropertiesPanel
          selectedNode={selectedNode}
          setSelectedNode={setSelectedNode}
          nodes={nodes}
          setNodes={setNodes}
          edges={edges}
          setNodeSamples={setNodeSamples}
          setNodeTypes={setNodeTypes}
          setExecutionMessage={setExecutionMessage}
          setExecutionSuccess={setExecutionSuccess}
          setActiveBottomTab={setActiveBottomTab}
          setIsBottomPanelVisible={setIsBottomPanelVisible}
          previewLimit={previewLimit}
          getUpstreamColumns={getUpstreamColumns}
        />
        </div>

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
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl border border-[#DFE1E6] animate-in fade-in zoom-in duration-200 flex flex-col max-h-[calc(100vh-2rem)]">
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

            {/* Tabs */}
            <div className="px-6 pt-4 flex-shrink-0">
              <div className="flex gap-2 border-b border-[#DFE1E6]">
                <button
                  onClick={() => setLoadModalTab('workflows')}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${loadModalTab === 'workflows' ? 'border-[#0052CC] text-[#0052CC]' : 'border-transparent text-[#6B778C] hover:text-[#172B4D]'}`}
                >
                  Your Workflows
                </button>
                <button
                  onClick={() => setLoadModalTab('samples')}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${loadModalTab === 'samples' ? 'border-[#0052CC] text-[#0052CC]' : 'border-transparent text-[#6B778C] hover:text-[#172B4D]'}`}
                >
                  Sample Pipelines
                </button>
              </div>
            </div>

            <div className="px-6 pb-4 flex-1 overflow-y-auto min-h-0">
              {loadModalTab === 'workflows' ? (
                /* Workflows Tab Content */
                availableWorkflows.length === 0 ? (
                  <div className="py-12 text-center">
                    <p className="text-sm text-[#6B778C]">No saved workflows found on server.</p>
                  </div>
                ) : (
                  <div className="space-y-2 mt-4">
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
                            className="px-3 py-2 bg-white border border-[#DFE1E2] text-red-600 rounded-md text-sm"
                            title="Delete"
                          >
                            {deleteLoading === name ? '...' : <Trash2 size={14} />}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              ) : (
                /* Samples Tab Content */
                <div className="space-y-4 mt-4">
                  {Object.entries(SAMPLE_CATEGORIES).map(([category, samples]) => (
                    <div key={category} className="border border-[#DFE1E6] rounded-md overflow-hidden">
                      <button
                        onClick={() => toggleCategory(category)}
                        className="w-full px-4 py-3 bg-[#FAFBFC] flex items-center justify-between hover:bg-[#F4F5F7] transition-colors"
                      >
                        <span className="text-sm font-semibold text-[#172B4D]">{category}</span>
                        <span className="text-xs text-[#6B778C] bg-white px-2 py-1 rounded-full border border-[#DFE1E6]">
                          {samples.length} samples
                        </span>
                      </button>
                      {expandedCategories.has(category) && (
                        <div className="p-2 space-y-2 bg-white">
                          {samples.map((sample: any) => (
                            <div key={sample.name} className="flex items-center justify-between space-x-3">
                              <button
                                onClick={() => handleLoadWorkflow(sample.name)}
                                className="flex-1 text-left px-4 py-3 text-sm text-[#172B4D] hover:bg-[#F4F5F7] border border-[#DFE1E6] rounded-md transition-all flex flex-col group hover:border-[#0052CC]"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{sample.name}</span>
                                  <span className="px-2 py-0.5 bg-[#EDEFFF] text-[#0052CC] text-[10px] font-bold rounded-full uppercase">Sample</span>
                                </div>
                                <span className="text-xs text-[#6B778C] mt-1">{sample.description}</span>
                              </button>
                              <button
                                onClick={async (e) => { e.stopPropagation(); try { const response = await fetch(sample.file); const data = await response.json(); const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${sample.name}.json`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); } catch (err) { setExecutionMessage({ title: 'Export failed', detail: (err as any).message || 'Could not export sample', type: 'error' }); setExecutionSuccess(true); } }}
                                className="px-3 py-2 bg-[#EDEFFF] text-[#0052CC] rounded-md text-sm border border-[#DFE1E6]"
                                title="Download JSON"
                              >
                                <FileDown size={14} />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="p-6 pt-4 border-t border-[#DFE1E6] flex justify-between items-center flex-shrink-0">
              <span className="text-xs text-[#6B778C]">
                {loadModalTab === 'workflows'
                  ? `${availableWorkflows.length} workflows`
                  : `${allSamplePipelines.length} sample pipelines in ${Object.keys(SAMPLE_CATEGORIES).length} categories`
                }
              </span>
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

      {/* Mobile-Specific Components */}
      {isMobile && (
        <>
          {/* Mobile Bottom Navigation */}
          <MobileNavigation
            onExecute={handleExecute}
            onLoad={openLoadModal}
            currentWorkflowName={currentPipelineName || undefined}
          />

          {/* Mobile Menu */}
          <MobileMenu
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
            onNewWorkflow={handleNewWorkflow}
            onLoad={openLoadModal}
          />

          {/* Mobile Workflow Viewer (Read-Only Mode) */}
          {isMobile && (
            <div className="fixed inset-0 z-40 md:hidden">
              <MobileWorkflowViewer
                nodes={nodes}
                edges={edges}
                executionResult={executionResult}
                onNodeClick={(node) => {
                  setSelectedNode(node);
                  setMobileResultsVisible(true);
                }}
                onBeautify={handleBeautify}
                nodeSamples={nodeSamples}
                nodeColumns={nodeColumns}
              />
            </div>
          )}

          {/* Mobile Results Display */}
          {mobileResultsVisible && selectedNode && (
            <div className="fixed inset-0 z-50 md:hidden">
              <div className="h-full overflow-y-auto bg-[#FAFBFC] p-4 safe-area-inset-bottom">
                <div className="mb-4">
                  <button
                    onClick={() => setMobileResultsVisible(false)}
                    className="flex items-center space-x-2 text-[#0052CC] mb-4"
                  >
                    <ChevronRight size={16} className="-rotate-180" />
                    <span className="text-sm font-bold">Back to Workflow</span>
                  </button>

                  {isExecuting ? (
                    <div className="mb-4 bg-white rounded-lg shadow-md border border-[#DFE1E6] p-4 animate-pulse">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 border-2 border-[#0052CC] border-t-transparent rounded-full animate-spin" />
                        <div>
                          <p className="text-sm font-bold text-[#172B4D]">Executing Workflow...</p>
                          <p className="text-xs text-[#6B778C]">Please wait</p>
                        </div>
                      </div>
                    </div>
                  ) : executionResult?.error ? (
                    <div className="mb-4 bg-white rounded-lg shadow-md border border-[#FF5630] p-4">
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 bg-[#FFEBE6] rounded-full flex items-center justify-center flex-shrink-0">
                          <AlertCircle size={16} className="text-[#FF5630]" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-bold text-[#172B4D] mb-1">Execution Failed</p>
                          <p className="text-xs text-[#6B778C] mb-3">{executionMessage?.detail || 'An error occurred'}</p>
                          <button
                            onClick={handleExecute}
                            className="w-full py-2 bg-[#0052CC] text-white text-xs font-bold rounded-md active:scale-95 transition-transform"
                          >
                            Retry
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : executionResult ? (
                    <div className="mb-4 bg-white rounded-lg shadow-md border border-[#36B37E] p-4">
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 bg-[#E3FCEF] rounded-full flex items-center justify-center flex-shrink-0">
                          <CheckCheck size={16} className="text-[#36B37E]" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-bold text-[#172B4D] mb-1">Execution Successful</p>
                          <div className="space-y-1 mb-3">
                            {executionResult.row_count && (
                              <p className="text-xs text-[#6B778C]">
                                Processed <span className="font-bold text-[#0052CC]">{executionResult.row_count.toLocaleString()}</span> rows
                              </p>
                            )}
                            {executionResult.execution_time && (
                              <p className="text-xs text-[#6B778C]">
                                Completed in <span className="font-bold text-[#172B4D]">{(executionResult.execution_time / 1000).toFixed(2)}s</span>
                              </p>
                            )}
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setMobileResultsVisible(false)}
                              className="flex-1 py-2 bg-[#0052CC] text-white text-xs font-bold rounded-md active:scale-95 transition-transform"
                            >
                              View Results
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}


                  {selectedNode && selectedNode.data.config && (
                    <div className="mt-4 bg-white rounded-lg shadow-md border border-[#DFE1E6] p-4">
                      <h3 className="text-sm font-bold text-[#172B4D] mb-3">Configuration</h3>
                      <div className="space-y-2">
                        {Object.entries(selectedNode.data.config).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between">
                            <span className="text-[10px] font-medium text-[#6B778C] uppercase tracking-wide">
                              {key}
                            </span>
                            <span className="text-xs font-semibold text-[#172B4D]">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
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
