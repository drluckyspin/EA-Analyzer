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

  const handleMenuItemClick = (item: string) => {
    setActiveMenuItem(item);
  };

  const renderContent = () => {
    switch (activeMenuItem) {
      case "Library":
        return <LibraryPage />;
      case "Review":
        return <AnalyzePage />;
      case "Visualize":
        return <GraphVisualizer />;
      default:
        return <LibraryPage />;
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
