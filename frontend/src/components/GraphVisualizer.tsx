"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  BackgroundVariant,
  NodeTypes,
  EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { apiClient } from "@/lib/api";
import { Diagram, GraphData } from "@/types";
import { DiagramSelector } from "./DiagramSelector";
import { CustomNode } from "./CustomNode";
import { CustomEdge } from "./CustomEdge";
import { saveNodePositions, loadNodePositions } from "@/lib/cookies";

// Define node and edge types
const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

const edgeTypes: EdgeTypes = {
  custom: CustomEdge,
};

// Layout algorithm for positioning nodes
const getLayoutedElements = (nodes: Node[], edges: Edge[], diagramId: string) => {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const edgeMap = new Map(edges.map((edge) => [edge.id, edge]));

  // Try to load saved positions first
  const savedPositions = loadNodePositions(diagramId);

  // Simple hierarchical layout
  const levels = new Map<string, number>();
  const visited = new Set<string>();

  // Find root nodes (nodes with no incoming edges)
  const rootNodes = nodes.filter(
    (node) => !edges.some((edge) => edge.target === node.id)
  );

  // BFS to assign levels
  const queue = rootNodes.map((node) => ({ node, level: 0 }));

  while (queue.length > 0) {
    const { node, level } = queue.shift()!;

    if (visited.has(node.id)) continue;
    visited.add(node.id);
    levels.set(node.id, level);

    // Add children to queue
    const children = edges
      .filter((edge) => edge.source === node.id)
      .map((edge) => nodeMap.get(edge.target))
      .filter(Boolean);

    children.forEach((child) => {
      if (child && !visited.has(child.id)) {
        queue.push({ node: child, level: level + 1 });
      }
    });
  }

  // Position nodes based on levels or saved positions
  const levelCounts = new Map<number, number>();
  const positionedNodes = nodes.map((node) => {
    // Use saved position if available, otherwise calculate layout position
    let position;
    if (savedPositions && savedPositions[node.id]) {
      position = savedPositions[node.id];
    } else {
      const level = levels.get(node.id) || 0;
      const count = levelCounts.get(level) || 0;
      levelCounts.set(level, count + 1);
      position = {
        x: count * 200 + 100,
        y: level * 150 + 100,
      };
    }

    return {
      ...node,
      type: "custom", // Ensure all nodes use the custom node type
      position,
    };
  });

  return { nodes: positionedNodes, edges };
};

export const GraphVisualizer: React.FC = () => {
  const [diagrams, setDiagrams] = useState<Diagram[]>([]);
  const [selectedDiagram, setSelectedDiagram] = useState<Diagram | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Load diagrams on component mount
  useEffect(() => {
    const loadDiagrams = async () => {
      try {
        setLoading(true);
        const diagramsData = await apiClient.getDiagrams();
        setDiagrams(diagramsData);

        // Auto-select first diagram if available
        if (diagramsData.length > 0) {
          setSelectedDiagram(diagramsData[0]);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load diagrams"
        );
      } finally {
        setLoading(false);
      }
    };

    loadDiagrams();
  }, []);

  // Load graph data when diagram is selected
  useEffect(() => {
    if (!selectedDiagram) return;

    const loadGraphData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getDiagramGraph(
          selectedDiagram.diagram_id
        );
        setGraphData(data);

        // Apply layout and set nodes/edges
        const { nodes: layoutedNodes, edges: layoutedEdges } =
          getLayoutedElements(data.nodes, data.edges, selectedDiagram.diagram_id);

        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load graph data"
        );
      } finally {
        setLoading(false);
      }
    };

    loadGraphData();
  }, [selectedDiagram, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Handle node changes and save positions when nodes are moved
  const handleNodesChange = useCallback(
    (changes: any[]) => {
      onNodesChange(changes);
      
      // Check if any changes are position changes
      const positionChanges = changes.filter(change => 
        change.type === 'position' && change.position
      );
      
      if (positionChanges.length > 0 && selectedDiagram) {
        // Get current node positions
        const currentPositions = nodes.reduce((acc, node) => {
          acc[node.id] = { x: node.position.x, y: node.position.y };
          return acc;
        }, {} as Record<string, { x: number; y: number }>);
        
        // Save positions to cookie
        saveNodePositions(selectedDiagram.diagram_id, currentPositions);
      }
    },
    [onNodesChange, nodes, selectedDiagram]
  );

  const handleDiagramSelect = (diagram: Diagram) => {
    setSelectedDiagram(diagram);
  };

  if (loading && diagrams.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading diagrams...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-500 text-lg">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full">
      {/* Header with diagram selector */}
      <div className="h-16 border-b bg-background flex items-center px-4">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-semibold">EA Analyzer</h1>
          <DiagramSelector
            diagrams={diagrams}
            selectedDiagram={selectedDiagram}
            onSelect={handleDiagramSelect}
            loading={loading}
          />
        </div>
      </div>

      {/* React Flow canvas */}
      <div className="h-[calc(100vh-4rem)]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};
