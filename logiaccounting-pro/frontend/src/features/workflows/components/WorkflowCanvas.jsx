/**
 * Workflow Canvas Component
 * Visual canvas for workflow nodes and connections
 */

import React, { useRef, useState, useCallback, useEffect } from 'react';
import { Zap, Calendar, MousePointer, Webhook } from 'lucide-react';
import WorkflowNode from './WorkflowNode';
import EdgeLine from './EdgeLine';

const WorkflowCanvas = ({
  nodes,
  edges,
  trigger,
  selectedNode,
  zoom,
  onSelectNode,
  onUpdateNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
  onTriggerClick,
}) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragNode, setDragNode] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [connecting, setConnecting] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });

  const getTriggerIcon = () => {
    if (!trigger) return <MousePointer size={20} />;
    switch (trigger.type) {
      case 'event': return <Zap size={20} />;
      case 'schedule': return <Calendar size={20} />;
      case 'webhook': return <Webhook size={20} />;
      default: return <MousePointer size={20} />;
    }
  };

  const getTriggerLabel = () => {
    if (!trigger) return 'Manual Trigger';
    switch (trigger.type) {
      case 'event': return trigger.event || 'Event Trigger';
      case 'schedule': return trigger.cron || 'Schedule Trigger';
      case 'webhook': return 'Webhook Trigger';
      default: return 'Manual Trigger';
    }
  };

  const handleMouseDown = (e, nodeId) => {
    if (e.button !== 0) return;

    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;

    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    setDragNode(nodeId);
    setIsDragging(true);
    onSelectNode(nodeId);
  };

  const handleMouseMove = useCallback((e) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left - panOffset.x) / zoom;
    const y = (e.clientY - rect.top - panOffset.y) / zoom;
    setMousePos({ x, y });

    if (isDragging && dragNode) {
      onUpdateNode(dragNode, {
        position: {
          x: Math.max(0, x - dragOffset.x),
          y: Math.max(0, y - dragOffset.y),
        },
      });
    }
  }, [isDragging, dragNode, dragOffset, zoom, panOffset, onUpdateNode]);

  const handleMouseUp = useCallback(() => {
    if (connecting) {
      setConnecting(null);
    }
    setIsDragging(false);
    setDragNode(null);
  }, [connecting]);

  const handleStartConnection = (nodeId, port = 'output') => {
    setConnecting({ nodeId, port });
  };

  const handleEndConnection = (nodeId, port = 'input') => {
    if (connecting && connecting.nodeId !== nodeId) {
      onAddEdge(connecting.nodeId, nodeId);
    }
    setConnecting(null);
  };

  const getNodePosition = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    return node?.position || { x: 0, y: 0 };
  };

  // Trigger node position (fixed at top)
  const triggerPosition = { x: 400, y: 50 };

  return (
    <div
      ref={canvasRef}
      className="w-full h-full bg-gray-50 overflow-hidden relative"
      style={{
        backgroundImage: 'radial-gradient(circle, #ddd 1px, transparent 1px)',
        backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        style={{
          transform: `scale(${zoom}) translate(${panOffset.x}px, ${panOffset.y}px)`,
          transformOrigin: 'top left',
        }}
      >
        {/* SVG for edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: 'visible' }}>
          {/* Edge from trigger to first node */}
          {nodes.length > 0 && edges.some(e => e.source === 'trigger') && (
            edges.filter(e => e.source === 'trigger').map(edge => {
              const targetPos = getNodePosition(edge.target);
              return (
                <EdgeLine
                  key={edge.id}
                  startX={triggerPosition.x + 100}
                  startY={triggerPosition.y + 40}
                  endX={targetPos.x + 100}
                  endY={targetPos.y}
                  onDelete={() => onDeleteEdge(edge.id)}
                />
              );
            })
          )}

          {/* Edges between nodes */}
          {edges.filter(e => e.source !== 'trigger').map(edge => {
            const sourcePos = getNodePosition(edge.source);
            const targetPos = getNodePosition(edge.target);
            return (
              <EdgeLine
                key={edge.id}
                startX={sourcePos.x + 100}
                startY={sourcePos.y + 80}
                endX={targetPos.x + 100}
                endY={targetPos.y}
                label={edge.label}
                condition={edge.condition}
                onDelete={() => onDeleteEdge(edge.id)}
              />
            );
          })}

          {/* Connecting line */}
          {connecting && (
            <line
              x1={getNodePosition(connecting.nodeId).x + 100}
              y1={getNodePosition(connecting.nodeId).y + 80}
              x2={mousePos.x}
              y2={mousePos.y}
              stroke="#3b82f6"
              strokeWidth="2"
              strokeDasharray="5,5"
            />
          )}
        </svg>

        {/* Trigger Node */}
        <div
          className="absolute cursor-pointer"
          style={{
            left: triggerPosition.x,
            top: triggerPosition.y,
            width: 200,
          }}
          onClick={onTriggerClick}
        >
          <div className="bg-green-500 text-white rounded-lg p-4 shadow-lg hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-2 mb-1">
              {getTriggerIcon()}
              <span className="font-medium">Trigger</span>
            </div>
            <div className="text-sm text-green-100">{getTriggerLabel()}</div>

            {/* Output port */}
            <div
              className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-green-600 rounded-full border-2 border-white cursor-crosshair"
              onMouseDown={(e) => {
                e.stopPropagation();
                handleStartConnection('trigger');
              }}
            />
          </div>
        </div>

        {/* Workflow Nodes */}
        {nodes.map(node => (
          <WorkflowNode
            key={node.id}
            node={node}
            isSelected={selectedNode === node.id}
            onMouseDown={(e) => handleMouseDown(e, node.id)}
            onStartConnection={() => handleStartConnection(node.id)}
            onEndConnection={() => handleEndConnection(node.id)}
            onSelect={() => onSelectNode(node.id)}
            onDelete={() => onDeleteNode(node.id)}
          />
        ))}

        {/* Drop zone indicator */}
        {connecting && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="text-center mt-32 text-gray-400">
              Click on a node to connect
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowCanvas;
