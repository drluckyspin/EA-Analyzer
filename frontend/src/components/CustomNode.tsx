"use client";

import React from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Color mapping for different node types using slate colors
const nodeTypeColors: Record<string, string> = {
  GridSource: "bg-slate-100 border-slate-300 text-slate-800",
  Transformer: "bg-slate-200 border-slate-400 text-slate-800",
  Breaker: "bg-slate-300 border-slate-500 text-slate-800",
  Busbar: "bg-slate-400 border-slate-600 text-slate-100",
  Motor: "bg-slate-500 border-slate-700 text-slate-100",
  RelayFunction: "bg-slate-600 border-slate-800 text-slate-100",
  Feeder: "bg-slate-700 border-slate-900 text-slate-100",
  CapacitorBank: "bg-slate-800 border-slate-900 text-slate-100",
  Battery: "bg-slate-900 border-slate-900 text-slate-100",
  Load: "bg-slate-50 border-slate-200 text-slate-800",
  // Additional node types found in the data
  CurrentTransformer: "bg-slate-100 border-slate-300 text-slate-800",
  Meter: "bg-slate-200 border-slate-400 text-slate-800",
  PotentialTransformer: "bg-slate-100 border-slate-300 text-slate-800",
  SurgeArrester: "bg-slate-300 border-slate-500 text-slate-800",
  VB1_vacuum: "bg-slate-300 border-slate-500 text-slate-800", // Same as Breaker
};

export const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeType = data.type || "default";
  const colorClass =
    nodeTypeColors[nodeType as keyof typeof nodeTypeColors] ||
    "bg-gray-100 border-gray-300 text-gray-800";

  return (
    <Card
      className={cn(
        "min-w-[120px] shadow-md transition-all duration-200",
        colorClass,
        selected && "ring-2 ring-primary ring-offset-2"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-primary"
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
        className="w-3 h-3 bg-primary"
      />
    </Card>
  );
};
