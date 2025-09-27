"use client";

import React from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getNodeTypeClasses } from "@/lib/theme";

export const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeType = (data.type as string) || "default";
  const colorClass = getNodeTypeClasses(nodeType);

  return (
    <Card
      className={cn(
        "min-w-[120px] shadow-md transition-all duration-200",
        colorClass,
        selected && "ring-2 ring-primary ring-offset-2"
      )}
    >
      {/* Invisible handles for React Flow to connect edges - they provide connection points but aren't visible */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-0 h-0 opacity-0"
        style={{ visibility: "hidden" }}
      />

      <CardContent className="p-3">
        <div className="text-center">
          <div className="font-semibold text-sm mb-1">
            {String(data.label || data.id || "Unknown")}
          </div>
          <div className="text-xs opacity-75">{String(nodeType)}</div>
        </div>
      </CardContent>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-0 h-0 opacity-0"
        style={{ visibility: "hidden" }}
      />
    </Card>
  );
};
