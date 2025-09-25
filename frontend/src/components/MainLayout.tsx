"use client";

import React, { useState } from "react";
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

      {/* Right Side - Navigation Bar + Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <NavigationBar />

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">{renderContent()}</div>
      </div>
    </div>
  );
};
