"use client";

import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  OnSelectionChangeParams,
  useReactFlow,
  Handle,
  Position,
  SelectionMode,
  Viewport,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const CustomNode = ({ data, type, selected }: any) => {
  let borderColor = '#6554C0';
  if (type === 'input') borderColor = '#0052CC';
  if (type === 'output') borderColor = '#36B37E';
  if (type === 'note') borderColor = '#FFAB00';

  const isNote = type === 'note';

  return (
    <div
      className={`react-flow__node-custom ${isNote ? 'bg-[#FFFAE6]' : 'bg-white'} border-2 rounded-md shadow-lg font-medium text-gray-800 text-sm transition-all duration-200 relative min-w-[200px] ${selected ? 'ring-2 ring-[#0052CC] ring-offset-2 shadow-xl border-[#0052CC]' : ''}`}
      style={{ borderColor }}
    >
      <style>{`
        .react-flow__node {
          background: none !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }
        .react-flow__handle {
          width: 14px !important;
          height: 14px !important;
          background: #B1B1B7 !important;
          border: 3px solid white !important;
          box-shadow: 0 1px 4px rgba(0,0,0,0.15);
          transition: background 0.2s, box-shadow 0.2s, border-color 0.2s;
          z-index: 10;
        }
        .react-flow__handle-top {
          top: -7px !important;
        }
        .react-flow__handle-bottom {
          bottom: -7px !important;
        }
        .react-flow__handle:hover {
          background: #0052CC !important;
          border-color: #E6EEFF !important;
          box-shadow: 0 0 10px rgba(0, 82, 204, 0.4);
          cursor: crosshair;
        }
        .react-flow__edge-path {
           stroke: #B1B1B7 !important;
           stroke-width: 2.5;
           transition: stroke 0.2s, stroke-width 0.2s;
        }
        .react-flow__edge.selected .react-flow__edge-path {
           stroke: #0052CC !important;
           stroke-width: 5 !important;
        }
        .react-flow__edge:hover .react-flow__edge-path {
           stroke: #0052CC !important;
           stroke-opacity: 0.6;
           stroke-width: 3.5;
        }
        .react-flow__edge.animated .react-flow__edge-path {
           stroke-dasharray: 6;
           animation: react-flow__dashdraw 0.5s linear infinite;
        }
      `}</style>
      {!isNote && <Handle type="target" position={Position.Top} style={{ left: '50%', transform: 'translateX(-50%)' }} />}
      <div className="flex items-center justify-between p-3 w-full">
        <div className="flex flex-col items-center space-y-1.5 p-1 w-full">
          <div className="flex items-center space-x-2">
            {type === 'input' && <span className="w-1.5 h-6 bg-[#0052CC] rounded-full"></span>}
            {type === 'output' && <span className="w-1.5 h-6 bg-[#36B37E] rounded-full"></span>}
            {isNote && <span className="text-lg">📝</span>}
            <span className="text-sm font-bold tracking-tight text-center">{data.label}</span>
          </div>
          {data.rowCount !== undefined && (
            <div className="flex items-center space-x-1.5 bg-[#EAE6FF] text-[#403294] px-3 py-1 rounded-full font-bold shadow-sm border border-[#D1CAFF]">
              <span className="text-[10px] uppercase opacity-60">Rows</span>
              <span className="text-xs">{data.rowCount.toLocaleString()}</span>
            </div>
          )}
          {data.description && (
            <div className={`mt-1 px-2 py-1 rounded border ${isNote ? 'text-gray-700 bg-white border-[#FFAB00]/40 text-sm leading-relaxed whitespace-pre-wrap w-full text-left font-normal' : 'text-xs text-gray-500 bg-gray-50 border-gray-200'}`}>
              {data.description}
            </div>
          )}
        </div>
      </div>
      {!isNote && <Handle type="source" position={Position.Bottom} style={{ left: '50%', transform: 'translateX(-50%)' }} />}
    </div>
  );
};

interface WorkspaceCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  setNodes: any;
  setEdges: any;
  onNodeSelect?: (node: Node | null) => void;
  onAfterConnect?: (connection: Connection) => void;
  layoutCounter?: number;
  isBottomPanelVisible?: boolean;
  shortcutsEnabled?: boolean;
  undo?: () => void;
  redo?: () => void;
  pushToHistory?: (nodes: Node[], edges: Edge[]) => void;
  bottomPanelHeight?: number;
  children?: React.ReactNode;
}

function WorkspaceCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  setNodes,
  setEdges,
  onNodeSelect,
  onAfterConnect,
  layoutCounter = 0,
  isBottomPanelVisible = false,
  bottomPanelHeight = 0,
  shortcutsEnabled = true,
  undo = () => {},
  redo = () => {},
  pushToHistory = () => {},
  children
}: WorkspaceCanvasProps) {
  const reactFlowWrapper = React.useRef<HTMLDivElement>(null);
  const { screenToFlowPosition, setViewport } = useReactFlow();

  const nodeTypes = useMemo(() => ({
    input: CustomNode,
    default: CustomNode,
    output: CustomNode,
    note: CustomNode,
  }), []);

  // Custom fit-to-view function that accounts for bottom panel
  const fitViewWithPanel = useCallback(() => {
    const wrapper = reactFlowWrapper.current;
    if (!wrapper || nodes.length === 0) return;

    const wrapperWidth = wrapper.offsetWidth;
    const wrapperHeight = wrapper.offsetHeight;

    // Calculate available height (subtract bottom panel area)
    // When panel is visible, we only want to use the space above it
    const availableHeight = isBottomPanelVisible
      ? wrapperHeight - bottomPanelHeight
      : wrapperHeight;

    // Get node dimensions (standard node size is ~200x100)
    const nodeWidth = 220;
    const nodeHeight = 120;
    const padding = 80;

    // Find bounds of all nodes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(node => {
      const x = node.position.x;
      const y = node.position.y;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x + nodeWidth > maxX) maxX = x + nodeWidth;
      if (y + nodeHeight > maxY) maxY = y + nodeHeight;
    });

    const contentWidth = maxX - minX;
    const contentHeight = maxY - minY;

    // Calculate zoom to fit content in available area
    // When panel is visible, fit into the smaller available height
    const zoomX = (wrapperWidth - padding * 2) / contentWidth;
    const zoomY = (availableHeight - padding * 2) / contentHeight;
    const zoom = Math.min(zoomX, zoomY, 1); // Cap at 1.0

    // Calculate center point of content
    const centerX = minX + contentWidth / 2;
    const centerY = minY + contentHeight / 2;

    // Center the content in the available area
    // When panel is visible, center in the upper portion (above the panel)
    const centerYOffset = isBottomPanelVisible
      ? (availableHeight / 2) // Center in the available area
      : (wrapperHeight / 2);   // Center in full height

    const viewport: Viewport = {
      x: wrapperWidth / 2 - centerX * zoom,
      y: centerYOffset - centerY * zoom,
      zoom: Math.max(zoom, 0.1), // Minimum zoom
    };

    setViewport(viewport, { duration: (typeof process !== 'undefined' && process.env.CI) ? 0 : 600 });
  }, [nodes, isBottomPanelVisible, bottomPanelHeight, setViewport]);

  // Refit view when layout changes (e.g. after beautify)
  React.useEffect(() => {
    if (layoutCounter > 0) {
      const timer = setTimeout(() => {
        fitViewWithPanel();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [layoutCounter, fitViewWithPanel]);

  const takeSnapshot = useCallback(() => {
    pushToHistory?.(JSON.parse(JSON.stringify(nodes)), JSON.parse(JSON.stringify(edges)));
  }, [pushToHistory, nodes, edges]);


  const undoRef = React.useRef(undo);
  const redoRef = React.useRef(redo);

  React.useEffect(() => {
    undoRef.current = undo;
    redoRef.current = redo;
  }, [undo, redo]);

  // Handle Keyboard Shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!shortcutsEnabled) {
        return;
      }

      // Don't intercept if user is typing in an input or textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' || 
        target.tagName === 'TEXTAREA' || 
        target.tagName === 'SELECT' ||
        target.isContentEditable ||
        target.closest('input, textarea, [contenteditable="true"]')
      ) {
        return;
      }

      const modifier = e.metaKey || e.ctrlKey;

      if (modifier && e.code === 'KeyZ') {
        if (e.shiftKey) {
          e.preventDefault();
          redoRef.current();
        } else {
          e.preventDefault();
          undoRef.current();
        }
      } else if (modifier && e.code === 'KeyY') {
        e.preventDefault();
        redoRef.current();
      }
    };
    window.addEventListener('keydown', handleKeyDown, false);
    return () => window.removeEventListener('keydown', handleKeyDown, false);
  }, [shortcutsEnabled]);


  const onConnect = useCallback(
    (params: Connection | Edge) => {
      takeSnapshot();
      setEdges((eds: Edge[]) => addEdge({ ...params, animated: true } as Edge, eds));

      // Call the callback after connection is made for schema propagation
      if (onAfterConnect) {
        onAfterConnect(params as Connection);
      }
    },
    [setEdges, takeSnapshot, onAfterConnect],
  );

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: OnSelectionChangeParams) => {
      if (onNodeSelect) {
        onNodeSelect(selectedNodes.length > 0 ? selectedNodes[0] : null);
      }
    },
    [onNodeSelect]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    // Manually trigger selection for this node
    setNodes((nds: Node[]) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === node.id ? true : false
      }))
    );
  }, [setNodes]);


  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const payload = event.dataTransfer.getData('application/reactflow');

      if (!payload || !reactFlowBounds) {
        return;
      }

      const { type, label, subtype } = JSON.parse(payload);

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: { label, subtype, config: {} },
      };

      takeSnapshot();
      setNodes((nds: Node[]) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes, takeSnapshot]
  );

  const onNodesDelete = useCallback(() => {
    takeSnapshot();
  }, [takeSnapshot]);

  const onEdgesDelete = useCallback(() => {
    takeSnapshot();
  }, [takeSnapshot]);

  const onNodeDragStop = useCallback(() => {
    takeSnapshot();
  }, [takeSnapshot]);

  return (
    <div className="w-full h-full relative" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChange}
        onNodeClick={onNodeClick}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        selectionOnDrag
        selectionMode={SelectionMode.Partial}
        panOnDrag={[1, 2]}
        connectionRadius={40}
        defaultEdgeOptions={{
          animated: true,
          style: { strokeWidth: 3, stroke: '#B1B1B1' }
        }}
        className="bg-[#FAFBFC]"
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background gap={16} size={1} color="#DFE1E6" />
        {children}
        <Controls
          position="top-left"
          showInteractive={false}
          onFitView={fitViewWithPanel}
          className="bg-white shadow-lg border border-[#DFE1E6] rounded-md"
        />
        <MiniMap 
          position="top-right"
          pannable
          zoomable
          nodeStrokeColor={(n) => {
            if (n.type === 'input') return '#0052CC';
            if (n.type === 'output') return '#36B37E';
            return '#6554C0';
          }}
          nodeColor={() => '#ffffff'}
          nodeBorderRadius={4}
          className="bg-white shadow-lg border border-[#DFE1E6] rounded-md !m-4"
        />

        
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
            <div className="flex flex-col items-center justify-center p-12 text-center max-w-sm bg-white/50 backdrop-blur-[2px] rounded-3xl">
              <div className="w-20 h-20 bg-[#0052CC]/10 text-[#0052CC] rounded-full flex items-center justify-center mb-6 border border-[#0052CC]/10 shadow-inner">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              </div>
              <h3 className="text-2xl font-bold text-[#171717] mb-3 tracking-tight">Your canvas is empty</h3>
              <p className="text-[#6B778C] text-base leading-relaxed">
                Drag components from the <span className="font-bold text-[#0052CC]">left panel</span> to build your data pipeline.
              </p>
            </div>
          </div>
        )}
      </ReactFlow>
    </div>
  );
}

export default WorkspaceCanvas;
