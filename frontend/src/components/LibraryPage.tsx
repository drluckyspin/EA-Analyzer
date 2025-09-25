"use client";

import React, { useState, useEffect } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import {
  Trash2,
  Eye,
  Calendar,
  Database,
  GitBranch,
  Activity,
  BarChart3,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { Diagram, DiagramDetail } from "@/types";
import { nodeTypeColors, edgeTypeColors } from "@/lib/theme";

interface LibraryPageProps {
  onNavigateToReview?: (diagramId: string) => void;
  onNavigateToVisualize?: (diagramId: string) => void;
}

export const LibraryPage: React.FC<LibraryPageProps> = ({
  onNavigateToReview,
  onNavigateToVisualize,
}) => {
  const [diagrams, setDiagrams] = useState<Diagram[]>([]);
  const [diagramDetails, setDiagramDetails] = useState<
    Record<string, DiagramDetail>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadDiagrams();
  }, []);

  const loadDiagrams = async () => {
    try {
      setLoading(true);
      setError(null);
      const diagramsData = await apiClient.getDiagrams();
      setDiagrams(diagramsData);

      // Load detailed stats for each diagram
      const details: Record<string, DiagramDetail> = {};
      for (const diagram of diagramsData) {
        try {
          const detail = await apiClient.getDiagramSummary(diagram.diagram_id);
          details[diagram.diagram_id] = detail;
        } catch (err) {
          console.warn(
            `Failed to load details for diagram ${diagram.diagram_id}:`,
            err
          );
        }
      }
      setDiagramDetails(details);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load diagrams");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (diagramId: string, title: string) => {
    if (
      !confirm(
        `Are you sure you want to delete "${title}"? This action cannot be undone.`
      )
    ) {
      return;
    }

    try {
      setDeleting(diagramId);
      await apiClient.deleteDiagram(diagramId);
      // Reload the diagrams list
      await loadDiagrams();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete diagram");
    } finally {
      setDeleting(null);
    }
  };

  const getStorageDate = (diagramId: string) => {
    // Extract timestamp from diagram_id (format: name_YYYYMMDD_HHMMSS)
    const parts = diagramId.split("_");
    if (parts.length >= 3) {
      const datePart = parts[parts.length - 2]; // YYYYMMDD
      const timePart = parts[parts.length - 1]; // HHMMSS

      if (datePart.length === 8 && timePart.length === 6) {
        const year = datePart.substring(0, 4);
        const month = datePart.substring(4, 6);
        const day = datePart.substring(6, 8);
        const hour = timePart.substring(0, 2);
        const minute = timePart.substring(2, 4);
        const second = timePart.substring(4, 6);

        const date = new Date(
          `${year}-${month}-${day}T${hour}:${minute}:${second}`
        );
        return date.toLocaleString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        });
      }
    }
    return "Unknown";
  };

  const getTopNodeTypes = (nodeCounts: Record<string, number>) => {
    return Object.entries(nodeCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([type, count]) => ({ type, count }));
  };

  const getTopRelationshipTypes = (relCounts: Record<string, number>) => {
    return Object.entries(relCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([type, count]) => ({ type, count }));
  };

  const getNodeTypeColor = (nodeType: string) => {
    const colors = (nodeTypeColors as any)[nodeType] || nodeTypeColors.default;
    return {
      background: `bg-${colors.background}`,
      border: `border-${colors.border}`,
      text: `text-${colors.text}`,
    };
  };

  const getEdgeTypeColor = (edgeType: string) => {
    const color =
      edgeTypeColors[edgeType as keyof typeof edgeTypeColors] ||
      edgeTypeColors.default;
    return color;
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col bg-slate-100">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Library</h1>
          <p className="text-gray-600 mt-1">Manage your diagram collection</p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading diagrams...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col bg-slate-100">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Library</h1>
          <p className="text-gray-600 mt-1">Manage your diagram collection</p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <Card className="p-8 text-center max-w-md">
            <div className="text-red-500">
              <Database className="h-12 w-12 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">
                Error Loading Diagrams
              </h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={loadDiagrams} variant="outline">
                Try Again
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Library</h1>
            <p className="text-gray-600 mt-1">
              Manage your diagram collection ({diagrams.length} diagrams)
            </p>
          </div>
          <Button onClick={loadDiagrams} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {diagrams.length === 0 ? (
          <div className="max-w-2xl mx-auto">
            <Card className="p-8 text-center">
              <div className="text-gray-500">
                <Database className="h-12 w-12 mx-auto mb-4" />
                <h2 className="text-xl font-medium mb-2">No Diagrams Found</h2>
                <p className="text-gray-400">
                  Your diagram library is empty. Run the demo to add some
                  diagrams.
                </p>
              </div>
            </Card>
          </div>
        ) : (
          <div className="w-full">
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Diagram
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        Storage Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statistics
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Node Types
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Relationships
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {diagrams.map((diagram) => {
                      const details = diagramDetails[diagram.diagram_id];
                      return (
                        <tr
                          key={diagram.diagram_id}
                          className="hover:bg-gray-50"
                        >
                          <td className="px-4 py-3 w-80">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-8 w-8">
                                <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
                                  <Activity className="h-4 w-4 text-blue-600" />
                                </div>
                              </div>
                              <div className="ml-3 min-w-0 flex-1">
                                <div
                                  className="text-sm font-medium text-gray-900 truncate"
                                  title={diagram.title}
                                >
                                  {diagram.title}
                                </div>
                                <div className="text-xs text-gray-500 truncate">
                                  {diagram.diagram_id}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center text-sm text-gray-900">
                              <Calendar className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                              <span className="whitespace-nowrap">
                                {getStorageDate(diagram.diagram_id)}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            {details ? (
                              <div className="text-sm text-gray-900">
                                <div className="flex items-center">
                                  <Database className="h-4 w-4 text-gray-400 mr-1 flex-shrink-0" />
                                  <span className="font-medium">
                                    {details.total_nodes}
                                  </span>
                                  <span className="text-gray-500 ml-1">
                                    nodes
                                  </span>
                                </div>
                                <div className="flex items-center mt-1">
                                  <GitBranch className="h-4 w-4 text-gray-400 mr-1 flex-shrink-0" />
                                  <span className="font-medium">
                                    {details.total_relationships}
                                  </span>
                                  <span className="text-gray-500 ml-1">
                                    edges
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500">
                                Loading...
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {details ? (
                              <div className="max-w-xs">
                                <div className="space-y-1">
                                  {getTopNodeTypes(details.node_counts).map(
                                    ({ type, count }, index) => {
                                      const colors = getNodeTypeColor(type);
                                      return (
                                        <div
                                          key={index}
                                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap ${colors.background} ${colors.border} ${colors.text} mr-1 mb-1`}
                                        >
                                          {type} ({count})
                                        </div>
                                      );
                                    }
                                  )}
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500">
                                Loading...
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {details ? (
                              <div className="max-w-xs">
                                <div className="space-y-1">
                                  {getTopRelationshipTypes(
                                    details.relationship_counts
                                  ).map(({ type, count }, index) => {
                                    const color = getEdgeTypeColor(type);
                                    return (
                                      <div
                                        key={index}
                                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-white whitespace-nowrap mr-1 mb-1"
                                        style={{ backgroundColor: color }}
                                      >
                                        {type} ({count})
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500">
                                Loading...
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-center text-sm font-medium">
                            <div className="flex flex-col items-center space-y-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  onNavigateToReview?.(diagram.diagram_id)
                                }
                                className="h-8 px-2"
                                title="View diagram details"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  onNavigateToVisualize?.(diagram.diagram_id)
                                }
                                className="h-8 px-2"
                                title="Visualize diagram"
                              >
                                <BarChart3 className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  handleDelete(
                                    diagram.diagram_id,
                                    diagram.title
                                  )
                                }
                                disabled={deleting === diagram.diagram_id}
                                className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                                title="Delete diagram"
                              >
                                {deleting === diagram.diagram_id ? (
                                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
