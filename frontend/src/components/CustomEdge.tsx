"use client";

import React from "react";
import { EdgeProps, getBezierPath } from "@xyflow/react";
import { getEdgeTypeColor } from "@/lib/theme";

export const CustomEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeType = (data?.type as string) || "CONNECTS_TO";
  const strokeColor = getEdgeTypeColor(edgeType);

  return (
    <>
      <path
        id={id}
        style={{
          ...style,
          stroke: strokeColor,
          strokeWidth: 2,
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
      {data?.type && (
        <text>
          <textPath
            href={`#${id}`}
            style={{ fontSize: 12, fill: strokeColor }}
            startOffset="50%"
            textAnchor="middle"
          >
            {String(data.type)}
          </textPath>
        </text>
      )}
    </>
  );
};
