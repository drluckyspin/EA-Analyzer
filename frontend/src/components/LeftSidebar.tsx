"use client";

import React from "react";
import Image from "next/image";
import { Zap, FileText, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { getSidebarClasses } from "@/lib/theme";

interface LeftSidebarProps {
  activeMenuItem?: string;
  onMenuItemClick?: (item: string) => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  activeMenuItem = "Analyze",
  onMenuItemClick,
}) => {
  const menuItems = [
    {
      id: "Analyze",
      label: "Analyze",
      icon: BarChart3,
    },
    {
      id: "Review",
      label: "Review",
      icon: FileText,
    },
    {
      id: "Visualize",
      label: "Visualize",
      icon: Zap,
    },
  ];

  return (
    <div
      className={`w-64 ${getSidebarClasses.background} h-full flex flex-col`}
    >
      {/* Product Logo */}
      <div
        className={`h-32 pt-6 flex items-center justify-center cursor-pointer group`}
      >
        <div className="flex items-center justify-center transition-all duration-300 ease-in-out group-hover:scale-110">
          <Image
            src="/ampy-logo.png"
            alt="AMPY Logo"
            width={112}
            height={112}
            className="w-28 h-28 object-contain transition-all duration-300 ease-in-out group-hover:drop-shadow-lg"
          />
        </div>
      </div>

      {/* Menu Items */}
      <div className="flex-1 py-4">
        <nav className="space-y-2 px-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeMenuItem === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onMenuItemClick?.(item.id)}
                className={cn(
                  "w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors",
                  isActive
                    ? getSidebarClasses.menuActive
                    : getSidebarClasses.menuInactive
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
