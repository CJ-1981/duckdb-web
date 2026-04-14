import { useState, useCallback } from 'react';
import { Node, Edge, useReactFlow, useNodesState, useEdgesState } from '@xyflow/react';

export function useWorkflowState(initialNodes: Node[] = [], initialEdges: Edge[] = []) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initialEdges);
  const { getNodes, getEdges } = useReactFlow();

  const [history, setHistory] = useState<{ nodes: Node[]; edges: Edge[] }[]>([]);
  const [redoStack, setRedoStack] = useState<{ nodes: Node[]; edges: Edge[] }[]>([]);

  const pushToHistory = useCallback((currentNodes: Node[], currentEdges: Edge[]) => {
    setHistory((prev) => [...prev.slice(-49), { nodes: currentNodes, edges: currentEdges }]);
    setRedoStack([]); // Clear redo stack on new action
  }, []);

  const undo = useCallback(() => {
    if (history.length === 0) return;
    const last = history[history.length - 1];
    setRedoStack((prev) => [...prev, { nodes, edges }]);
    setHistory((prev) => prev.slice(0, -1));
    setNodes(last.nodes);
    setEdges(last.edges);
  }, [history, nodes, edges, setNodes, setEdges]);

  const redo = useCallback(() => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setHistory((prev) => [...prev.slice(-49), { nodes, edges }]);
    setRedoStack((prev) => prev.slice(0, -1));
    setNodes(next.nodes);
    setEdges(next.edges);
  }, [redoStack, nodes, edges, setNodes, setEdges]);

  return {
    nodes,
    setNodes,
    onNodesChange,
    edges,
    setEdges,
    onEdgesChange,
    history,
    pushToHistory,
    undo,
    redo,
    getNodes,
    getEdges
  };
}
