/**
 * Edge Line Component
 * Connection line between workflow nodes
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';

const EdgeLine = ({
  startX,
  startY,
  endX,
  endY,
  label,
  condition,
  onDelete,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Calculate control points for smooth curve
  const midY = (startY + endY) / 2;
  const controlPoint1Y = startY + Math.min(50, (endY - startY) / 2);
  const controlPoint2Y = endY - Math.min(50, (endY - startY) / 2);

  const path = `M ${startX} ${startY} C ${startX} ${controlPoint1Y}, ${endX} ${controlPoint2Y}, ${endX} ${endY}`;

  // Calculate label position
  const labelX = (startX + endX) / 2;
  const labelY = midY;

  const getConditionColor = () => {
    if (condition === 'true') return '#22c55e';
    if (condition === 'false') return '#ef4444';
    return '#6b7280';
  };

  return (
    <g
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ pointerEvents: 'stroke' }}
    >
      {/* Invisible wider path for easier hover */}
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth="20"
        style={{ cursor: 'pointer' }}
      />

      {/* Visible path */}
      <path
        d={path}
        fill="none"
        stroke={isHovered ? '#3b82f6' : getConditionColor()}
        strokeWidth={isHovered ? 3 : 2}
        markerEnd="url(#arrowhead)"
      />

      {/* Arrow marker definition */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill={isHovered ? '#3b82f6' : getConditionColor()}
          />
        </marker>
      </defs>

      {/* Label or condition indicator */}
      {(label || condition) && (
        <g transform={`translate(${labelX}, ${labelY})`}>
          <rect
            x="-20"
            y="-10"
            width="40"
            height="20"
            rx="4"
            fill="white"
            stroke={getConditionColor()}
            strokeWidth="1"
          />
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="10"
            fill={getConditionColor()}
            fontWeight="500"
          >
            {label || (condition === 'true' ? 'Yes' : condition === 'false' ? 'No' : '')}
          </text>
        </g>
      )}

      {/* Delete button on hover */}
      {isHovered && onDelete && (
        <g
          transform={`translate(${labelX + 30}, ${labelY})`}
          style={{ cursor: 'pointer', pointerEvents: 'all' }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <circle r="10" fill="#ef4444" />
          <foreignObject x="-6" y="-6" width="12" height="12">
            <X size={12} color="white" />
          </foreignObject>
        </g>
      )}
    </g>
  );
};

export default EdgeLine;
