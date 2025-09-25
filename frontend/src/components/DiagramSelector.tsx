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

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return dateString;
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
        return formatDate(date.toISOString());
      }
    }
    return "Unknown";
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
        <SelectTrigger className="w-96">
          <SelectValue placeholder="Select a diagram...">
            {selectedDiagram && (
              <div className="flex flex-col w-full text-left py-1">
                <span className="font-medium text-sm leading-tight truncate">
                  {selectedDiagram.title}
                </span>
                <span className="text-xs text-muted-foreground mt-1">
                  Stored: {getStorageDate(selectedDiagram.diagram_id)}
                </span>
              </div>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="w-96">
          {diagrams.map((diagram) => (
            <SelectItem
              key={diagram.diagram_id}
              value={diagram.diagram_id}
              className="py-3 data-[highlighted]:bg-blue-50 data-[highlighted]:text-blue-900"
            >
              <div className="flex flex-col w-full">
                <span className="font-medium text-sm leading-tight truncate">
                  {diagram.title}
                </span>
                <span className="text-xs text-muted-foreground mt-1">
                  Stored: {getStorageDate(diagram.diagram_id)}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
