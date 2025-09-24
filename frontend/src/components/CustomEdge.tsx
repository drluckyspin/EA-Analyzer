'use client'

import React from 'react'
import { EdgeProps, getBezierPath } from '@xyflow/react'

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
  })

  // Color mapping for different edge types
  const edgeTypeColors: Record<string, string> = {
    CONNECTS_TO: '#3b82f6', // blue
    PROTECTS: '#ef4444', // red
    CONTROLS: '#10b981', // green
    MONITORS: '#f59e0b', // yellow
    SUPPLIES: '#8b5cf6', // purple
  }

  const edgeType = data?.type || 'CONNECTS_TO'
  const strokeColor = edgeTypeColors[edgeType as keyof typeof edgeTypeColors] || '#6b7280'

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
  )
}
