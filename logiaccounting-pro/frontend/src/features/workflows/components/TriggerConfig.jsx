/**
 * Trigger Configuration Modal
 * Configure workflow trigger settings
 */

import React, { useState, useEffect } from 'react';
import { X, Zap, Calendar, MousePointer, Webhook, AlertCircle } from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const TriggerConfig = ({ trigger, onSave, onClose }) => {
  const [triggerType, setTriggerType] = useState(trigger?.type || 'manual');
  const [config, setConfig] = useState(trigger || {});
  const [events, setEvents] = useState({});
  const [cronPreview, setCronPreview] = useState([]);
  const [cronError, setCronError] = useState(null);

  useEffect(() => {
    loadTriggerMetadata();
  }, []);

  useEffect(() => {
    if (triggerType === 'schedule' && config.cron) {
      validateCron(config.cron);
    }
  }, [config.cron]);

  const loadTriggerMetadata = async () => {
    try {
      const response = await workflowAPI.getTriggers();
      setEvents(response.events || {});
    } catch (error) {
      console.error('Failed to load trigger metadata:', error);
    }
  };

  const validateCron = async (cron) => {
    try {
      const response = await workflowAPI.validateCron(cron);
      if (response.valid) {
        setCronPreview(response.next_runs || []);
        setCronError(null);
      } else {
        setCronError(response.message);
        setCronPreview([]);
      }
    } catch (error) {
      setCronError('Failed to validate');
    }
  };

  const handleSave = () => {
    onSave({
      type: triggerType,
      ...config,
    });
  };

  const triggerTypes = [
    { id: 'manual', name: 'Manual', icon: MousePointer, description: 'Trigger manually via button or API' },
    { id: 'event', name: 'Event', icon: Zap, description: 'Trigger when an event occurs' },
    { id: 'schedule', name: 'Schedule', icon: Calendar, description: 'Run on a schedule' },
    { id: 'webhook', name: 'Webhook', icon: Webhook, description: 'Trigger via external webhook' },
  ];

  const schedulePresets = [
    { label: 'Every hour', cron: '0 * * * *' },
    { label: 'Daily at 9 AM', cron: '0 9 * * *' },
    { label: 'Daily at 6 PM', cron: '0 18 * * *' },
    { label: 'Weekly Monday 9 AM', cron: '0 9 * * 1' },
    { label: 'Monthly on 1st', cron: '0 9 1 * *' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[80vh] overflow-auto">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">Configure Trigger</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Trigger Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trigger Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {triggerTypes.map(type => {
                const Icon = type.icon;
                const isSelected = triggerType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => {
                      setTriggerType(type.id);
                      setConfig({ type: type.id });
                    }}
                    className={`p-3 border rounded-lg text-left transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon size={18} className={isSelected ? 'text-blue-600' : 'text-gray-500'} />
                      <span className="font-medium text-sm">{type.name}</span>
                    </div>
                    <p className="text-xs text-gray-500">{type.description}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Event Configuration */}
          {triggerType === 'event' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Event
              </label>
              <select
                value={config.event || ''}
                onChange={(e) => setConfig({ ...config, event: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">Choose an event...</option>
                {Object.entries(events).map(([category, categoryEvents]) => (
                  <optgroup key={category} label={category.replace(/_/g, ' ').toUpperCase()}>
                    {categoryEvents.map(event => (
                      <option key={event.type} value={event.type}>
                        {event.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              {config.event && (
                <p className="text-xs text-gray-500 mt-2">
                  {Object.values(events).flat().find(e => e.type === config.event)?.description}
                </p>
              )}
            </div>
          )}

          {/* Schedule Configuration */}
          {triggerType === 'schedule' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schedule Presets
                </label>
                <div className="flex flex-wrap gap-2">
                  {schedulePresets.map(preset => (
                    <button
                      key={preset.cron}
                      onClick={() => setConfig({ ...config, cron: preset.cron })}
                      className={`px-3 py-1 text-sm rounded-full border ${
                        config.cron === preset.cron
                          ? 'bg-blue-100 border-blue-500 text-blue-700'
                          : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cron Expression
                </label>
                <input
                  type="text"
                  value={config.cron || ''}
                  onChange={(e) => setConfig({ ...config, cron: e.target.value })}
                  placeholder="0 9 * * *"
                  className="w-full px-3 py-2 border rounded-lg font-mono"
                />
                {cronError && (
                  <div className="flex items-center gap-1 text-red-600 text-xs mt-1">
                    <AlertCircle size={12} />
                    {cronError}
                  </div>
                )}
                {cronPreview.length > 0 && (
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                    <div className="font-medium mb-1">Next runs:</div>
                    {cronPreview.slice(0, 3).map((time, i) => (
                      <div key={i} className="text-gray-600">
                        {new Date(time).toLocaleString()}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Webhook Configuration */}
          {triggerType === 'webhook' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Webhook URL
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm break-all">
                  https://api.logiaccounting.com/webhooks/trigger/[workflow_id]
                </code>
                <p className="text-xs text-gray-500 mt-2">
                  The webhook URL will be generated after saving the workflow.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save Trigger
          </button>
        </div>
      </div>
    </div>
  );
};

export default TriggerConfig;
