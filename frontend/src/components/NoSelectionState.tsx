"use client";

import React from "react";

interface NoSelectionStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
}

export const NoSelectionState: React.FC<NoSelectionStateProps> = ({
  title,
  description,
  icon,
}) => {
  return (
    <div className="flex items-center justify-center h-full bg-slate-100">
      <div className="text-center">
        <div className="text-gray-400 mb-4">
          {icon || (
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
          )}
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-500">{description}</p>
      </div>
    </div>
  );
};
