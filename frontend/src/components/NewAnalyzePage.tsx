"use client";

import React from "react";
import { Card } from "./ui/card";

export const NewAnalyzePage: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">Analyze</h1>
        <p className="text-gray-600 mt-1">
          Advanced analysis tools and insights
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto">
          <Card className="p-8 text-center">
            <div className="text-gray-500">
              <h2 className="text-xl font-medium mb-2">
                Analysis Tools Coming Soon
              </h2>
              <p className="text-gray-400">
                Advanced analysis features will be available here.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
