"use client";

import React, { useState, useEffect } from "react";
import { NavigationBar } from "./NavigationBar";
import { LeftSidebar } from "./LeftSidebar";
import { GraphVisualizer } from "./GraphVisualizer";
import { AnalyzePage } from "./AnalyzePage";
import { NewAnalyzePage } from "./NewAnalyzePage";
import { LibraryPage } from "./LibraryPage";

export const MainLayout: React.FC = () => {
  const [activeMenuItem, setActiveMenuItem] = useState<string>("Library");
  const [selectedDiagramId, setSelectedDiagramId] = useState<string | null>(
    null
  );

  // Version information state
  const [versionInfo, setVersionInfo] = useState({
    version: "1.0.0",
    commit: "unknown",
    buildTime: "unknown",
  });

  // Fetch version information from API
  useEffect(() => {
    const fetchVersionInfo = async () => {
      try {
        const response = await fetch("/api/version");
        const data = await response.json();
        setVersionInfo({
          version: data.version,
          commit: data.commit,
          buildTime: data.buildTime,
        });
      } catch (error) {
        console.warn("Failed to fetch version info:", error);
      }
    };

    fetchVersionInfo();
  }, []);

  const formatBuildTime = (dateString: string) => {
    if (dateString === "unknown") return "unknown";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "unknown";
    }
  };

  const handleMenuItemClick = (item: string) => {
    setActiveMenuItem(item);
    // Clear selected diagram when manually navigating to avoid confusion
    if (item !== "Review") {
      setSelectedDiagramId(null);
    }
  };

  const handleNavigateToReview = (diagramId: string) => {
    setSelectedDiagramId(diagramId);
    setActiveMenuItem("Review");
  };

  const handleNavigateToVisualize = (diagramId: string) => {
    setSelectedDiagramId(diagramId);
    setActiveMenuItem("Visualize");
  };

  const renderContent = () => {
    switch (activeMenuItem) {
      case "Library":
        return (
          <LibraryPage
            onNavigateToReview={handleNavigateToReview}
            onNavigateToVisualize={handleNavigateToVisualize}
          />
        );
      case "Review":
        return <AnalyzePage selectedDiagramId={selectedDiagramId} />;
      case "Visualize":
        return <GraphVisualizer selectedDiagramId={selectedDiagramId} />;
      default:
        return (
          <LibraryPage
            onNavigateToReview={handleNavigateToReview}
            onNavigateToVisualize={handleNavigateToVisualize}
          />
        );
    }
  };

  return (
    <div className="h-screen flex bg-slate-100">
      {/* Left Sidebar - Full Height */}
      <LeftSidebar
        activeMenuItem={activeMenuItem}
        onMenuItemClick={handleMenuItemClick}
      />

      {/* Right Side - Navigation Bar + Content + Footer */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <NavigationBar />

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">{renderContent()}</div>

        {/* Footer */}
        <div className="bg-white border-t border-gray-200 px-6 py-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div>© 2025 Bain & Company. All rights reserved.</div>
            <div className="flex items-center space-x-4">
              <span>v{versionInfo.version}</span>
              <span>•</span>
              <span>Commit: {versionInfo.commit}</span>
              <span>•</span>
              <span>Built: {formatBuildTime(versionInfo.buildTime)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
