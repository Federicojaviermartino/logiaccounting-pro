/**
 * Workflow Node Component
 * Individual node in the workflow canvas
 */

import React from 'react';
import {
  GitBranch,
  Repeat,
  Clock,
  Mail,
  MessageSquare,
  Bell,
  Database,
  Globe,
  Trash2,
  Settings,
  Play,
} from 'lucide-react';

const WorkflowNode = ({
  node,
  isSelected,
  onMouseDown,
  onStartConnection,
  onEndConnection,
  onSelect,
  onDelete,
}) => {
  const getNodeIcon = () => {
    switch (node.type) {
      case 'condition': return <GitBranch size={18} />;
      case 'loop': return <Repeat size={18} />;
      case 'delay': return <Clock size={18} />;
      case 'action':
        switch (node.action) {
          case 'send_email': return <Mail size={18} />;
          case 'send_slack': return <MessageSquare size={18} />;
          case 'send_notification': return <Bell size={18} />;
          case 'query_records':
          case 'create_record':
          case 'update_record': return <Database size={18} />;
          case 'http_request': return <Globe size={18} />;
          default: return <Play size={18} />;
        }
      default: return <Settings size={18} />;
    }
  };

  const getNodeColor = () => {
    switch (node.type) {
      case 'condition': return 'bg-yellow-500';
      case 'loop': return 'bg-purple-500';
      case 'delay': return 'bg-orange-500';
      case 'action': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getNodeTitle = () => {
    if (node.name) return node.name;

    switch (node.type) {
      case 'condition': return 'Condition';
      case 'loop': return 'Loop';
      case 'delay': return 'Delay';
      case 'action': return node.action?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Action';
      default: return 'Step';
    }
  };

  const getNodeSubtitle = () => {
    switch (node.type) {
      case 'condition':
        if (node.condition?.field) {
          return `If ${node.condition.field} ${node.condition.operator} ${node.condition.value}`;
        }
        return 'Configure condition';
      case 'loop':
        return node.collection ? `For each in ${node.collection}` : 'Configure loop';
      case 'delay':
        if (node.config?.duration) {
          return `Wait ${node.config.duration} ${node.config.unit || 'seconds'}`;
        }
        return 'Configure delay';
      case 'action':
        if (node.action === 'send_email' && node.config?.to) {
          return `To: ${node.config.to}`;
        }
        if (node.action === 'send_slack' && node.config?.channel) {
          return `Channel: ${node.config.channel}`;
        }
        return node.config?.description || 'Configure action';
      default:
        return '';
    }
  };

  return (
    <div
      className={`absolute cursor-move select-none ${isSelected ? 'z-10' : 'z-0'}`}
      style={{
        left: node.position?.x || 0,
        top: node.position?.y || 0,
        width: 200,
      }}
      onMouseDown={onMouseDown}
    >
      {/* Input port */}
      <div
        className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white cursor-crosshair z-10 hover:bg-blue-500 transition-colors"
        onMouseUp={(e) => {
          e.stopPropagation();
          onEndConnection();
        }}
      />

      {/* Node body */}
      <div
        className={`rounded-lg shadow-lg overflow-hidden transition-all ${
          isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''
        }`}
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
      >
        {/* Header */}
        <div className={`${getNodeColor()} text-white px-3 py-2 flex items-center gap-2`}>
          {getNodeIcon()}
          <span className="font-medium text-sm truncate flex-1">{getNodeTitle()}</span>
          {isSelected && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:bg-white/20 rounded"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="bg-white px-3 py-2">
          <div className="text-xs text-gray-500 truncate">
            {getNodeSubtitle()}
          </div>
        </div>

        {/* Condition branches */}
        {node.type === 'condition' && (
          <div className="bg-gray-50 px-3 py-1 flex justify-between text-xs border-t">
            <span className="text-green-600">True</span>
            <span className="text-red-600">False</span>
          </div>
        )}
      </div>

      {/* Output port(s) */}
      {node.type === 'condition' ? (
        <>
          {/* True branch output */}
          <div
            className="absolute -bottom-2 left-1/4 -translate-x-1/2 w-4 h-4 bg-green-500 rounded-full border-2 border-white cursor-crosshair z-10 hover:scale-110 transition-transform"
            onMouseDown={(e) => {
              e.stopPropagation();
              onStartConnection('true');
            }}
          />
          {/* False branch output */}
          <div
            className="absolute -bottom-2 left-3/4 -translate-x-1/2 w-4 h-4 bg-red-500 rounded-full border-2 border-white cursor-crosshair z-10 hover:scale-110 transition-transform"
            onMouseDown={(e) => {
              e.stopPropagation();
              onStartConnection('false');
            }}
          />
        </>
      ) : (
        <div
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white cursor-crosshair z-10 hover:bg-blue-500 transition-colors"
          onMouseDown={(e) => {
            e.stopPropagation();
            onStartConnection();
          }}
        />
      )}
    </div>
  );
};

export default WorkflowNode;
