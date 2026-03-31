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
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const CustomNode = ({ data, type, selected }: any) => {
  let borderColor = '#6554C0';
  if (type === 'input') borderColor = '#0052CC';
  if (type === 'output') borderColor = '#36B37E';

  return (
    <div 
      className={`bg-white border-2 rounded-md p-3 shadow-lg font-medium text-gray-800 text-sm flex items-center justify-between min-w-[200px] transition-all duration-200 ${selected ? 'ring-2 ring-[#0052CC] ring-offset-2 shadow-xl border-[#0052CC]' : ''}`} 
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
          box-shadow: 0 1px 4px rgba(0,0,0,0.1);
          transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          z-index: 10;
        }
        .react-flow__handle:hover {
          background: #0052CC !important;
          transform: scale(1.3);
          box-shadow: 0 0 8px rgba(0, 82, 204, 0.4);
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
      <Handle type="target" position={Position.Top} className="!-top-2" />
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
      <Handle type="source" position={Position.Bottom} className="!-bottom-2" />
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
  onNodeSelect?: (node: Node | null) => void;
}

function WorkspaceCanvas({ onNodeSelect }: WorkspaceCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge({ ...params, animated: true } as Edge, eds)),
    [setEdges],
  );

  const onSelectionChange = useCallback(
    ({ nodes }: OnSelectionChangeParams) => {
      if (onNodeSelect) {
        onNodeSelect(nodes.length > 0 ? nodes[0] : null);
      }
    },
    [onNodeSelect]
  );

  const reactFlowWrapper = React.useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

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

      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  return (
    <div className="w-full h-full relative" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSelectionChange={onSelectionChange}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        fitView
        className="bg-[#FAFBFC]"
      >
        <Background gap={16} size={1} color="#DFE1E6" />
        <Controls showInteractive={false} className="bg-white shadow-lg border border-[#DFE1E6] rounded-md" />
        <MiniMap 
          nodeStrokeColor={(n) => {
            if (n.type === 'input') return '#0052CC';
            if (n.type === 'output') return '#36B37E';
            return '#6554C0';
          }}
          nodeColor={() => '#ffffff'}
          nodeBorderRadius={4}
          className="bg-white shadow-lg border border-[#DFE1E6] rounded-md"
        />
        <Panel position="top-right" className="bg-white p-3 rounded-md shadow-md border border-[#DFE1E6] flex items-center space-x-2 m-4">
           <div className="w-3 h-3 rounded-full bg-[#36B37E] animate-pulse"></div>
           <span className="text-sm font-semibold text-gray-700">Execution Engine Ready</span>
        </Panel>
        
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
