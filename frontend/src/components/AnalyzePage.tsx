"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { Diagram } from "@/types";
import { DiagramSelector } from "./DiagramSelector";
import { Card } from "./ui/card";
import { FileText, BarChart3, Network, GitBranch } from "lucide-react";

interface DiagramSummary {
  diagram_id: string;
  title: string;
  extracted_at: string;
  node_counts: Record<string, number>;
  relationship_counts: Record<string, number>;
  total_nodes: number;
  total_relationships: number;
  metadata: Record<string, any>;
}

export const AnalyzePage: React.FC = () => {
  const [diagrams, setDiagrams] = useState<Diagram[]>([]);
  const [selectedDiagramId, setSelectedDiagramId] = useState<string>("");
  const [summary, setSummary] = useState<DiagramSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isContentVisible, setIsContentVisible] = useState(false);

  // Load diagrams on component mount
  useEffect(() => {
    const loadDiagrams = async () => {
      try {
        const diagramsData = await apiClient.getDiagrams();
        setDiagrams(diagramsData);
        // Don't auto-select any diagram - start with blank tables
      } catch (err) {
        setError("Failed to load diagrams");
        console.error("Error loading diagrams:", err);
      }
    };

    loadDiagrams();
  }, []);

  // Load summary when diagram is selected
  useEffect(() => {
    if (selectedDiagramId) {
      loadSummary(selectedDiagramId);
    } else {
      // Clear summary when no diagram is selected
      setSummary(null);
      setError(null);
      setIsContentVisible(false);
    }
  }, [selectedDiagramId]);

  const loadSummary = async (diagramId: string) => {
    setLoading(true);
    setError(null);
    try {
      const summaryData = await apiClient.getDiagramSummary(diagramId);
      setSummary(summaryData);
      // Trigger fade-in animation after data is loaded
      setTimeout(() => {
        setIsContentVisible(true);
      }, 50);
    } catch (err) {
      setError("Failed to load diagram summary");
      console.error("Error loading summary:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDiagramChange = (diagramId: string) => {
    // Start fade-out animation
    setIsContentVisible(false);

    // After a brief delay, update the diagram and start fade-in
    setTimeout(() => {
      setSelectedDiagramId(diagramId);
      // Trigger fade-in after content is loaded
      setTimeout(() => {
        setIsContentVisible(true);
      }, 100);
    }, 150);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Diagram Review
            </h1>
            <p className="text-slate-600 mt-1">
              View detailed statistics and analysis of electrical diagrams
            </p>
          </div>
          <div className="flex items-center">
            <DiagramSelector
              diagrams={diagrams}
              selectedDiagram={
                diagrams.find((d) => d.diagram_id === selectedDiagramId) || null
              }
              onSelect={(diagram) => handleDiagramChange(diagram.diagram_id)}
              loading={loading}
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="text-slate-600 animate-pulse">
              Loading summary...
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 animate-in slide-in-from-top-2 duration-300">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {summary && !loading && (
          <div
            className={`space-y-6 transition-all duration-500 ease-in-out ${
              isContentVisible
                ? "opacity-100 transform translate-y-0"
                : "opacity-0 transform translate-y-4"
            }`}
          >
            {/* Metadata and Statistics Cards in Single Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Metadata Card */}
              <Card className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
                <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-slate-600" />
                  Diagram Metadata
                </h2>
                <div className="space-y-5">
                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                      Title
                    </label>
                    <div className="text-slate-900 font-medium text-sm leading-relaxed">
                      {summary.title}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                      Extracted At
                    </label>
                    <div className="text-slate-900 font-medium text-sm">
                      {formatDate(summary.extracted_at)}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                      Diagram ID
                    </label>
                    <div className="text-slate-900 font-mono text-xs bg-slate-50 px-3 py-2 rounded border border-slate-200 break-all">
                      {summary.diagram_id}
                    </div>
                  </div>

                  {summary.metadata.source_image && (
                    <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                      <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                        Source Image
                      </label>
                      <div className="text-slate-900 font-medium text-sm">
                        {summary.metadata.source_image}
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {/* Statistics Card */}
              <Card className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
                <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-slate-600" />
                  Diagram Statistics
                </h2>
                <div className="space-y-5">
                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600 font-medium text-sm">
                        Total Nodes
                      </span>
                      <span className="font-semibold text-slate-900 text-lg">
                        {summary.total_nodes}
                      </span>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600 font-medium text-sm">
                        Total Relationships
                      </span>
                      <span className="font-semibold text-slate-900 text-lg">
                        {summary.total_relationships}
                      </span>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600 font-medium text-sm">
                        Node Types
                      </span>
                      <span className="font-semibold text-slate-900 text-lg">
                        {Object.keys(summary.node_counts).length}
                      </span>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-600 font-medium text-sm">
                        Relationship Types
                      </span>
                      <span className="font-semibold text-slate-900 text-lg">
                        {Object.keys(summary.relationship_counts).length}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Node Types Card */}
            <Card className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                <Network className="w-5 h-5 text-slate-600" />
                Node Types
              </h2>
              <div className="overflow-x-auto bg-white rounded-lg border border-slate-200 shadow-sm">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Percentage
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {Object.entries(summary.node_counts)
                      .sort(([, a], [, b]) => b - a)
                      .map(([type, count]) => {
                        const percentage =
                          summary.total_nodes > 0
                            ? ((count / summary.total_nodes) * 100).toFixed(1)
                            : "0.0";
                        return (
                          <tr key={type}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                              {type}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                              {count}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                              {percentage}%
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Relationship Types Card */}
            <Card className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-slate-600" />
                Relationship Types
              </h2>
              <div className="overflow-x-auto bg-white rounded-lg border border-slate-200 shadow-sm">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                        Percentage
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {Object.entries(summary.relationship_counts)
                      .sort(([, a], [, b]) => b - a)
                      .map(([type, count]) => {
                        const percentage =
                          summary.total_relationships > 0
                            ? (
                                (count / summary.total_relationships) *
                                100
                              ).toFixed(1)
                            : "0.0";
                        return (
                          <tr key={type}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                              {type}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                              {count}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                              {percentage}%
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

        {!summary && !loading && !error && (
          <div className="flex items-center justify-center h-32">
            <div className="text-slate-600">
              Select a diagram to view analysis
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
