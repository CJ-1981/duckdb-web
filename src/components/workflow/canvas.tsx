"use client";

import React, { useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Panel,
  Node,
  OnSelectionChangeParams,
  useReactFlow,
  ReactFlowProvider,
  Handle,
  Position,
  SelectionMode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const CustomNode = ({ data, type, selected }: any) => {
  let borderColor = '#6554C0';
  if (type === 'input') borderColor = '#0052CC';
  if (type === 'output') borderColor = '#36B37E';

  return (
    <div 
      className={`bg-white border-2 rounded-md shadow-lg font-medium text-gray-800 text-sm transition-all duration-200 relative min-w-[200px] ${selected ? 'ring-2 ring-[#0052CC] ring-offset-2 shadow-xl border-[#0052CC]' : ''}`} 
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
      <Handle type="target" position={Position.Top} style={{ left: '50%', transform: 'translateX(-50%)' }} />
      <div className="flex items-center justify-between p-3 w-full">
        <div className="flex flex-col items-center space-y-1.5 p-1 w-full">
          <div className="flex items-center space-x-2">
            {type === 'input' && <span className="w-1.5 h-6 bg-[#0052CC] rounded-full"></span>}
            {type === 'output' && <span className="w-1.5 h-6 bg-[#36B37E] rounded-full"></span>}
            <span className="text-sm font-bold tracking-tight text-center">{data.label}</span>
          </div>
          {data.rowCount !== undefined && (
            <div className="flex items-center space-x-1.5 bg-[#EAE6FF] text-[#403294] px-3 py-1 rounded-full font-bold shadow-sm border border-[#D1CAFF]">
              <span className="text-[10px] uppercase opacity-60">Rows</span>
              <span className="text-xs">{data.rowCount.toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ left: '50%', transform: 'translateX(-50%)' }} />
    </div>
  );
};

const nodeTypes = {
  input: CustomNode,
  default: CustomNode,
  output: CustomNode,
};

const initialNodes: Node[] = [];

const initialEdges: Edge[] = [];

interface WorkspaceCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  setNodes: any;
  setEdges: any;
  onNodeSelect?: (node: Node | null) => void;
  layoutCounter?: number;
  isBottomPanelVisible?: boolean;
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
  layoutCounter = 0,
  isBottomPanelVisible = false,
  bottomPanelHeight = 0,
  children
}: WorkspaceCanvasProps) {
  const [history, setHistory] = useState<{ nodes: Node[]; edges: Edge[] }[]>([]);
  const [redoStack, setRedoStack] = useState<{ nodes: Node[]; edges: Edge[] }[]>([]);
  const reactFlowWrapper = React.useRef<HTMLDivElement>(null);
  const { fitView, screenToFlowPosition } = useReactFlow();

  const fitOptions = React.useMemo(() => {
    // We use ratios (0.1 = 10%) for padding.
    // For the bottom panel, we calculate the ratio based on its pixel height.
    const h = reactFlowWrapper.current?.offsetHeight || 800; // default to 800px if not yet rendered
    const bottomRatio = isBottomPanelVisible ? (bottomPanelHeight / h) + 0.1 : 0.1;

    const padding = {
      top: 0.1,
      right: 0.1,
      bottom: Math.min(bottomRatio, 0.8), // Cap at 80% to avoid disappearing
      left: 0.1,
    };
    
    console.log('[DEBUG] fitOptions updated:', { isBottomPanelVisible, bottomPanelHeight, h, padding });
    return {
      padding,
      duration: 600,
    };
  }, [isBottomPanelVisible, bottomPanelHeight]);

  // Refit view when layout changes (e.g. after beautify)
  React.useEffect(() => {
    if (layoutCounter > 0) {
      const timer = setTimeout(() => {
        fitView(fitOptions);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [layoutCounter, fitView, fitOptions]);

  const takeSnapshot = useCallback(() => {
    setHistory((prev) => [...prev.slice(-49), { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }]);
    setRedoStack([]);
  }, [nodes, edges]);

  const undo = useCallback(() => {
    if (history.length === 0) return;
    const last = history[history.length - 1];
    setRedoStack((prev) => [...prev, { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }]);
    setNodes(last.nodes);
    setEdges(last.edges);
    setHistory((prev) => prev.slice(0, -1));
  }, [history, nodes, edges, setNodes, setEdges]);

  const redo = useCallback(() => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setHistory((prev) => [...prev, { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }]);
    setNodes(next.nodes);
    setEdges(next.edges);
    setRedoStack((prev) => prev.slice(0, -1));
  }, [redoStack, nodes, edges, setNodes, setEdges]);

  // Handle Keyboard Shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.userAgent);
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      if (modifier && e.key.toLowerCase() === 'z') {
        if (e.shiftKey) {
          e.preventDefault();
          redo();
        } else {
          e.preventDefault();
          undo();
        }
      } else if (modifier && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        redo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo]);

  const onConnect = useCallback(
    (params: Connection | Edge) => {
      takeSnapshot();
      setEdges((eds: Edge[]) => addEdge({ ...params, animated: true } as Edge, eds));
    },
    [setEdges, takeSnapshot],
  );

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: OnSelectionChangeParams) => {
      if (onNodeSelect) {
        onNodeSelect(selectedNodes.length > 0 ? selectedNodes[0] : null);
      }
    },
    [onNodeSelect]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (onNodeSelect) {
      onNodeSelect(node);
    }
  }, [onNodeSelect]);


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
          style: { strokeWidth: 3, stroke: '#B1B1B7' } 
        }}
        fitView
        fitViewOptions={fitOptions}
        className="bg-[#FAFBFC]"
      >
        <Background gap={16} size={1} color="#DFE1E6" />
        {children}
        <Controls 
          position="top-left" 
          showInteractive={false} 
          fitViewOptions={fitOptions}
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
