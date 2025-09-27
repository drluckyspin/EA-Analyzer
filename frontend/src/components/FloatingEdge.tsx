import React from "react";
import { getBezierPath, useInternalNode } from "@xyflow/react";
import { getEdgeParams } from "@/lib/getEdgeParams";
import { getEdgeTypeColor } from "@/lib/theme";

function FloatingEdge({
  id,
  source,
  target,
  markerEnd,
  style,
  data,
}: {
  id: string;
  source: string;
  target: string;
  markerEnd?: any;
  style?: any;
  data?: any;
}) {
  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);

  if (!sourceNode || !targetNode) {
    return null;
  }

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(
    sourceNode,
    targetNode
  );

  const [edgePath] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition: sourcePos,
    targetPosition: targetPos,
    targetX: tx,
    targetY: ty,
  });

  const edgeType = (data?.type as string) || "CONNECTS_TO";
  const strokeColor = getEdgeTypeColor(edgeType);

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: strokeColor,
          strokeWidth: 2,
        }}
      />
      {data?.type && (
        <text key={`${id}-label`}>
          <textPath
            key={`${id}-textpath`}
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
}

export default FloatingEdge;
