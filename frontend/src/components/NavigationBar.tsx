"use client";

import React, { useState, useRef, useEffect } from "react";
import { User, Settings, LogOut, ChevronDown } from "lucide-react";
import { getNavigationClasses } from "@/lib/theme";

export const NavigationBar: React.FC = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleProfileClick = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleSettingsClick = () => {
    console.log("Settings clicked");
    setIsDropdownOpen(false);
  };

  const handleLogoutClick = () => {
    console.log("Logout clicked");
    setIsDropdownOpen(false);
  };

  return (
    <div
      className={`h-16 ${getNavigationClasses.background} border-b ${getNavigationClasses.border} flex items-center justify-between px-6`}
    >
      {/* Left side - Empty for now */}
      <div className="flex items-center">
        {/* Title removed - logo is now in sidebar */}
      </div>

      {/* Right side - Profile Dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={handleProfileClick}
          className="flex items-center space-x-2 hover:bg-slate-600 rounded-lg px-3 py-2 transition-colors duration-200"
        >
          <div
            className={`w-8 h-8 ${getNavigationClasses.profileBackground} rounded-full flex items-center justify-center`}
          >
            <User className={`w-5 h-5 ${getNavigationClasses.profileIcon}`} />
          </div>
          <span
            className={`${getNavigationClasses.profileText} text-sm font-medium`}
          >
            Profile
          </span>
          <ChevronDown
            className={`w-4 h-4 ${
              getNavigationClasses.profileIcon
            } transition-transform duration-200 ${
              isDropdownOpen ? "rotate-180" : ""
            }`}
          />
        </button>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50">
            <button
              onClick={handleSettingsClick}
              className="w-full flex items-center space-x-3 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors duration-200"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
            <button
              onClick={handleLogoutClick}
              className="w-full flex items-center space-x-3 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors duration-200"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
