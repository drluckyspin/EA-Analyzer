"use client";

import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Diagram } from "@/types";
import { getFormClasses } from "@/lib/theme";

interface DiagramSelectorProps {
  diagrams: Diagram[];
  selectedDiagram: Diagram | null;
  onSelect: (diagram: Diagram) => void;
  loading: boolean;
}

export const DiagramSelector: React.FC<DiagramSelectorProps> = ({
  diagrams,
  selectedDiagram,
  onSelect,
  loading,
}) => {
  const handleValueChange = (value: string) => {
    const diagram = diagrams.find((d) => d.diagram_id === value);
    if (diagram) {
      onSelect(diagram);
    }
  };

  return (
    <div className="flex items-center space-x-3">
      <label
        htmlFor="diagram-select"
        className={`text-sm font-medium whitespace-nowrap ${getFormClasses.label}`}
      >
        Diagram:
      </label>
      <Select
        value={selectedDiagram?.diagram_id || ""}
        onValueChange={handleValueChange}
        disabled={loading || diagrams.length === 0}
      >
        <SelectTrigger className="w-auto min-w-[600px] max-w-[800px]">
          <SelectValue placeholder="Select a diagram..." />
        </SelectTrigger>
        <SelectContent className="w-auto min-w-[600px] max-w-[800px]">
          {diagrams.map((diagram) => (
            <SelectItem
              key={diagram.diagram_id}
              value={diagram.diagram_id}
              className="py-3"
            >
              <div className="flex flex-col w-full">
                <span className="font-medium text-sm leading-tight">
                  {diagram.title}
                </span>
                <span className="text-xs text-muted-foreground mt-1">
                  {diagram.extracted_at}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
