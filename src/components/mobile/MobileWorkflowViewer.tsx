"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Node, Edge } from '@xyflow/react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  X,
  Eye,
  CheckCheck,
  AlertCircle,
  SlidersHorizontal
} from 'lucide-react';

interface MobileWorkflowViewerProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (node: Node) => void;
  executionResult?: any;
  onBeautify?: () => void;
  nodeSamples?: Record<string, any[]>;
  nodeColumns?: Record<string, string[]>;
}

export function MobileWorkflowViewer({
  nodes,
  edges,
  onNodeClick,
  executionResult,
  onBeautify,
  nodeSamples,
  nodeColumns,
}: MobileWorkflowViewerProps) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [showDataPreview, setShowDataPreview] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Touch handling for pan and zoom
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      setDragStart({
        x: e.touches[0].clientX - position.x,
        y: e.touches[0].clientY - position.y,
      });
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isDragging && e.touches.length === 1) {
      setPosition({
        x: e.touches[0].clientX - dragStart.x,
        y: e.touches[0].clientY - dragStart.y,
      });
    }
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.2, 2));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleResetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleNodeTap = (node: Node, e: React.TouchEvent | React.MouseEvent) => {
    e.stopPropagation();
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  // Auto-show execution panel when results come in
  useEffect(() => {
    if (executionResult) {
      // Intentionally sync state with prop change - valid side effect pattern
      setShowExecutionPanel(true); // eslint-disable-line react-hooks/set-state-in-effect
    }
  }, [executionResult]);

  // Calculate node positions for mobile
  const renderNodes = () => {
    return nodes.map((node) => {
      const borderColor = node.type === 'input' ? '#0052CC' :
                         node.type === 'output' ? '#36B37E' :
                         node.type === 'note' ? '#FFAB00' : '#6554C0';

      const subtypeText = node.data.subtype ? String(node.data.subtype) : null;

      return (
        <div
          key={node.id}
          className="absolute bg-white border-2 rounded-lg shadow-lg p-3 min-w-[140px] max-w-[180px] transition-all"
          style={{
            left: `${node.position.x * scale + position.x}px`,
            top: `${node.position.y * scale + position.y}px`,
            borderColor,
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
            cursor: 'pointer',
            touchAction: 'manipulation',
          }}
          onTouchEnd={(e) => handleNodeTap(node, e)}
          onClick={(e) => handleNodeTap(node, e)}
        >
          <div className="flex flex-col space-y-1.5">
            <div className="flex items-center space-x-1.5">
              {node.type === 'input' && <span className="w-1 h-4 bg-[#0052CC] rounded-full" />}
              {node.type === 'output' && <span className="w-1 h-4 bg-[#36B37E] rounded-full" />}
              {node.type === 'note' && <span className="text-sm">📝</span>}
              <span className="text-xs font-bold text-[#172B4D] truncate">
                {String(node.data.label)}
              </span>
            </div>

            {node.data.rowCount !== null && node.data.rowCount !== undefined && node.type !== 'note' && (
              <div className="flex items-center space-x-1 bg-[#EAE6FF] text-[#403294] px-2 py-0.5 rounded text-[9px] font-semibold">
                <span>{(node.data.rowCount as number).toLocaleString()}</span>
                <span className="opacity-60">rows</span>
              </div>
            )}

            {subtypeText && (
              <div className="text-[9px] text-[#6B778C] uppercase tracking-wide font-medium">
                {subtypeText}
              </div>
            )}
          </div>
        </div>
      );
    });
  };

  // Render simplified edges with bezier curves
  const renderEdges = () => {
    return edges.map((edge) => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);

      if (!sourceNode || !targetNode) return null;

      const nodeWidth = 160; // Approximate node width
      const nodeHeight = 80; // Approximate node height

      const sourceX = sourceNode.position.x * scale + position.x + nodeWidth / 2;
      const sourceY = sourceNode.position.y * scale + position.y + nodeHeight / 2;
      const targetX = targetNode.position.x * scale + position.x + nodeWidth / 2;
      const targetY = targetNode.position.y * scale + position.y;

      // Calculate control points for smooth bezier curve
      const deltaY = Math.abs(targetY - sourceY);
      const controlOffset = Math.max(deltaY * 0.5, 50);

      const pathData = `M ${sourceX} ${sourceY} C ${sourceX} ${sourceY + controlOffset}, ${targetX} ${targetY - controlOffset}, ${targetX} ${targetY}`;

      return (
        <svg
          key={edge.id}
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
          style={{ overflow: 'visible' }}
        >
          <defs>
            <marker
              id={`arrowhead-${edge.id}`}
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#B1B1B7"
              />
            </marker>
          </defs>
          <path
            d={pathData}
            stroke="#B1B1B7"
            strokeWidth="2"
            fill="none"
            markerEnd={`url(#arrowhead-${edge.id})`}
            strokeDasharray={edge.animated ? "4" : "0"}
          />
        </svg>
      );
    });
  };

  return (
    <>
      {/* Main Viewer Container */}
      <div className="relative w-full h-full bg-[#FAFBFC] md:hidden" data-testid="mobile-workflow-viewer">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 bg-white border-b border-[#DFE1E6] px-4 py-3 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-sm font-bold text-[#172B4D]">Workflow Viewer</h1>
              <p className="text-[10px] text-[#6B778C]">
                {nodes.length} nodes • {edges.length} connections
              </p>
            </div>
            {onBeautify && (
              <button
                onClick={onBeautify}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-[#EAE6FF] text-[#0052CC] rounded-lg text-xs font-bold active:scale-95 transition-transform"
              >
                <SlidersHorizontal size={14} strokeWidth={2.5} />
                <span>Beautify</span>
              </button>
            )}
          </div>
        </div>

        {/* Canvas Area */}
        <div
          ref={containerRef}
          className="absolute inset-0 mt-16 mb-44 overflow-hidden"
          style={{ touchAction: 'none' }}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          {/* Zoom Controls - Floating bottom-right */}
          <div className="absolute bottom-48 right-4 z-10 flex flex-col items-center space-y-2">
            <button
              onClick={handleZoomIn}
              className="w-12 h-12 bg-white rounded-full shadow-lg border border-[#DFE1E6] text-[#0052CC] active:scale-95 transition-transform flex items-center justify-center"
              aria-label="Zoom in"
            >
              <ZoomIn size={20} strokeWidth={2.5} />
            </button>
            <button
              onClick={handleZoomOut}
              className="w-12 h-12 bg-white rounded-full shadow-lg border border-[#DFE1E6] text-[#0052CC] active:scale-95 transition-transform flex items-center justify-center"
              aria-label="Zoom out"
            >
              <ZoomOut size={20} strokeWidth={2.5} />
            </button>
            <button
              onClick={handleResetView}
              className="w-12 h-12 bg-white rounded-full shadow-lg border border-[#DFE1E6] text-[#6554C0] active:scale-95 transition-transform flex items-center justify-center"
              aria-label="Reset view"
            >
              <Maximize2 size={20} strokeWidth={2.5} />
            </button>
          </div>
          <div
            ref={contentRef}
            className="relative w-full h-full"
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
              transformOrigin: '0 0',
              transition: isDragging ? 'none' : 'transform 0.2s ease-out',
            }}
          >
            {renderEdges()}
            {renderNodes()}
          </div>
        </div>
      </div>

      {/* Bottom Sheets - Rendered as siblings outside main container */}
      {selectedNode && (() => {
        const subtypeText = selectedNode.data.subtype ? String(selectedNode.data.subtype) : null;
        return (
          <div className="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl border-t border-[#DFE1E6] animate-in slide-in-from-bottom duration-300 flex flex-col md:hidden" style={{ height: '70vh', touchAction: 'auto' }}>
            <div className="overflow-y-auto p-4 flex-1" style={{ WebkitOverflowScrolling: 'touch' }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-1 h-8 rounded-full"
                    style={{
                      backgroundColor:
                        selectedNode.type === 'input' ? '#0052CC' :
                        selectedNode.type === 'output' ? '#36B37E' :
                        selectedNode.type === 'note' ? '#FFAB00' : '#6554C0'
                    }}
                  />
                  <div>
                    <h3 className="text-sm font-bold text-[#172B4D]">
                      {String(selectedNode.data.label)}
                    </h3>
                    <p className="text-[10px] text-[#6B778C] uppercase tracking-wide">
                      {selectedNode.type}
                      {subtypeText && <span> • {subtypeText}</span>}
                    </p>
                  </div>
                </div>
                <div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-2 hover:bg-[#F4F5F7] rounded-lg transition-colors"
              >
                <X size={18} className="text-[#6B778C]" />
              </button>
              </div>
            </div>

            {/* Node Details */}
            <div className="space-y-3">
              {selectedNode.data.rowCount !== null && selectedNode.data.rowCount !== undefined && selectedNode.type !== 'note' && (
                <div className="flex items-center justify-between bg-[#EAE6FF] px-3 py-2 rounded-lg">
                  <span className="text-xs font-semibold text-[#403294]">Row Count</span>
                  <span className="text-sm font-bold text-[#0052CC]">
                    {(selectedNode.data.rowCount as number).toLocaleString()}
                  </span>
                </div>
              )}

              {selectedNode.data.config ? (
                <>
                <div className="bg-[#FAFBFC] rounded-lg p-3">
                  <h4 className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-2">
                    Configuration
                  </h4>
                  <div className="space-y-1">
                    {Object.entries(selectedNode.data.config as Record<string, any>).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-xs">
                        <span className="text-[#6B778C] font-medium">{key}</span>
                        <span className="text-[#172B4D] font-semibold">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '') as React.ReactNode}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                </>
              ) : null}
            </div>

            {/* Actions */}
            <div className="flex space-x-2 mt-4">
              <button
                onClick={() => setShowDataPreview(!showDataPreview)}
                className="flex-1 py-2.5 bg-[#0052CC] text-white rounded-lg text-xs font-bold active:scale-95 transition-transform"
              >
                <Eye size={14} className="inline mr-1" />
                {showDataPreview ? 'Hide Data' : 'Preview Data'}
              </button>
              <button
                onClick={() => setSelectedNode(null)}
                className="px-4 py-2.5 bg-[#F4F5F7] text-[#172B4D] rounded-lg text-xs font-bold active:scale-95 transition-transform"
              >
                Close
              </button>
            </div>

            {/* Data Preview Section */}
            {showDataPreview && nodeSamples && selectedNode && nodeSamples[selectedNode.id] && (
              <div className="mt-4 border-t border-[#DFE1E6] pt-4">
                <h4 className="text-[10px] font-bold text-[#6B778C] uppercase tracking-wider mb-2">
                  Data Preview
                </h4>
                <div className="overflow-x-auto">
                  <div className="max-h-48 overflow-y-auto bg-[#FAFBFC] rounded-lg p-2">
                    {(() => {
                      const sampleData = nodeSamples[selectedNode.id];
                      if (!sampleData || sampleData.length === 0) {
                        return <p className="text-xs text-[#6B778C]">No sample data available</p>;
                      }
                      const columns = nodeColumns?.[selectedNode.id] || Object.keys(sampleData[0] || {});
                      return (
                        <table className="w-full text-[10px]">
                          <thead>
                            <tr className="bg-[#EAE6FF]">
                              {columns.map((col: string) => (
                                <th key={col} className="px-2 py-1 text-left font-semibold text-[#403294]">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {sampleData.slice(0, 10).map((row: any, idx: number) => (
                              <tr key={idx} className="border-b border-[#DFE1E6]">
                                {columns.map((col: string) => (
                                  <td key={col} className="px-2 py-1 text-[#172B4D]">
                                    {String(row[col] ?? '')}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      );
                    })()}
                  </div>
                  {nodeSamples[selectedNode.id].length > 10 && (
                    <p className="text-[9px] text-[#6B778C] mt-1 text-center">
                      Showing 10 of {nodeSamples[selectedNode.id].length} rows
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
        );
      })()}

      {/* Execution Status Panel */}
      {showExecutionPanel && executionResult && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center md:hidden">
          <div
            className="absolute inset-0"
            onClick={() => setShowExecutionPanel(false)}
          />
          <div className="relative bg-white rounded-t-2xl w-full h-[70vh] flex flex-col animate-in slide-in-from-bottom duration-300" style={{ touchAction: 'auto' }}>
            <div className="overflow-y-auto p-4 flex-1" style={{ WebkitOverflowScrolling: 'touch' }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#172B4D]">Execution Results</h3>
                <button
                  onClick={() => setShowExecutionPanel(false)}
                  className="p-2 hover:bg-[#F4F5F7] rounded-lg active:scale-95 transition-transform"
                >
                  <X size={18} />
                </button>
              </div>

              {executionResult.success !== false ? (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 bg-[#E3FCEF] p-3 rounded-lg">
                    <CheckCheck size={16} className="text-[#36B37E]" />
                    <span className="text-sm font-bold text-[#36B37E]">Execution Successful</span>
                  </div>

                  {executionResult.row_count && (
                    <div className="bg-[#FAFBFC] p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-[#6B778C]">Total Rows Processed</span>
                        <span className="text-sm font-bold text-[#0052CC]">
                          {executionResult.row_count.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  )}

                  {executionResult.execution_time && (
                    <div className="bg-[#FAFBFC] p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-[#6B778C]">Execution Time</span>
                        <span className="text-sm font-bold text-[#172B4D]">
                          {(executionResult.execution_time / 1000).toFixed(2)}s
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 bg-[#FFEBE6] p-3 rounded-lg">
                    <AlertCircle size={16} className="text-[#FF5630]" />
                    <span className="text-sm font-bold text-[#FF5630]">Execution Failed</span>
                  </div>
                  {executionResult.error && (
                    <div className="bg-[#FAFBFC] p-3 rounded-lg">
                      <p className="text-xs text-[#172B4D]">{executionResult.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
