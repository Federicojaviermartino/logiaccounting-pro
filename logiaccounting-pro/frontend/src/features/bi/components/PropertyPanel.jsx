/**
 * PropertyPanel - Configure selected component properties
 */

import React, { useState } from 'react';
import { Settings, Database, Palette, Layout } from 'lucide-react';
import { useReportDesigner } from '../context/ReportDesignerContext';

export default function PropertyPanel() {
  const { state, actions } = useReportDesigner();
  const { layout, designer } = state;

  const [activeTab, setActiveTab] = useState('config');

  const selectedComponent = layout.components.find(
    c => c.id === designer.selectedComponentId
  );

  if (!selectedComponent) {
    return (
      <div className="property-panel empty">
        <div className="empty-message">
          <Settings className="w-8 h-8" />
          <p>Select a component to edit its properties</p>
        </div>

        <style jsx>{`
          .property-panel.empty {
            width: 280px;
            background: var(--bg-primary);
            border-left: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .empty-message {
            text-align: center;
            color: var(--text-muted);
          }

          .empty-message p {
            margin-top: 12px;
            font-size: 13px;
          }
        `}</style>
      </div>
    );
  }

  const updateConfig = (updates) => {
    actions.updateComponent({
      id: selectedComponent.id,
      config: { ...selectedComponent.config, ...updates },
    });
  };

  const updatePosition = (updates) => {
    actions.updateComponent({
      id: selectedComponent.id,
      position: { ...selectedComponent.position, ...updates },
    });
  };

  return (
    <div className="property-panel">
      {/* Tabs */}
      <div className="panel-tabs">
        <button
          className={`tab ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Settings className="w-4 h-4" />
          Config
        </button>
        <button
          className={`tab ${activeTab === 'data' ? 'active' : ''}`}
          onClick={() => setActiveTab('data')}
        >
          <Database className="w-4 h-4" />
          Data
        </button>
        <button
          className={`tab ${activeTab === 'style' ? 'active' : ''}`}
          onClick={() => setActiveTab('style')}
        >
          <Palette className="w-4 h-4" />
          Style
        </button>
        <button
          className={`tab ${activeTab === 'layout' ? 'active' : ''}`}
          onClick={() => setActiveTab('layout')}
        >
          <Layout className="w-4 h-4" />
          Layout
        </button>
      </div>

      {/* Tab Content */}
      <div className="panel-content">
        {activeTab === 'config' && (
          <ConfigTab
            component={selectedComponent}
            onUpdate={updateConfig}
          />
        )}

        {activeTab === 'data' && (
          <DataBindingTab
            component={selectedComponent}
            availableFields={getAvailableFields(state)}
            onUpdate={(dataBinding) => actions.updateComponent({
              id: selectedComponent.id,
              dataBinding,
            })}
          />
        )}

        {activeTab === 'style' && (
          <StyleTab
            component={selectedComponent}
            onUpdate={updateConfig}
          />
        )}

        {activeTab === 'layout' && (
          <LayoutTab
            component={selectedComponent}
            onUpdate={updatePosition}
          />
        )}
      </div>

      <style jsx>{`
        .property-panel {
          width: 280px;
          background: var(--bg-primary);
          border-left: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
        }

        .panel-tabs {
          display: flex;
          border-bottom: 1px solid var(--border-color);
        }

        .tab {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 10px 8px;
          font-size: 12px;
          color: var(--text-muted);
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
        }

        .tab:hover {
          color: var(--text-primary);
          background: var(--bg-secondary);
        }

        .tab.active {
          color: var(--primary);
          border-bottom-color: var(--primary);
        }

        .panel-content {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
        }
      `}</style>
    </div>
  );
}

// Config Tab
function ConfigTab({ component, onUpdate }) {
  const renderConfigFields = () => {
    switch (component.type) {
      case 'chart':
        return (
          <>
            <PropertyField label="Title">
              <input
                type="text"
                value={component.config.title || ''}
                onChange={(e) => onUpdate({ title: e.target.value })}
                placeholder="Chart Title"
              />
            </PropertyField>

            <PropertyField label="Chart Type">
              <select
                value={component.config.chartType || 'bar'}
                onChange={(e) => onUpdate({ chartType: e.target.value })}
              >
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie Chart</option>
                <option value="donut">Donut Chart</option>
              </select>
            </PropertyField>

            <PropertyField label="Show Legend">
              <input
                type="checkbox"
                checked={component.config.showLegend !== false}
                onChange={(e) => onUpdate({ showLegend: e.target.checked })}
              />
            </PropertyField>
          </>
        );

      case 'kpi':
        return (
          <>
            <PropertyField label="Title">
              <input
                type="text"
                value={component.config.title || ''}
                onChange={(e) => onUpdate({ title: e.target.value })}
              />
            </PropertyField>

            <PropertyField label="Format">
              <select
                value={component.config.format || 'number'}
                onChange={(e) => onUpdate({ format: e.target.value })}
              >
                <option value="number">Number</option>
                <option value="currency">Currency</option>
                <option value="percent">Percentage</option>
              </select>
            </PropertyField>

            <PropertyField label="Show Trend">
              <input
                type="checkbox"
                checked={component.config.showTrend !== false}
                onChange={(e) => onUpdate({ showTrend: e.target.checked })}
              />
            </PropertyField>
          </>
        );

      case 'table':
        return (
          <>
            <PropertyField label="Title">
              <input
                type="text"
                value={component.config.title || ''}
                onChange={(e) => onUpdate({ title: e.target.value })}
              />
            </PropertyField>

            <PropertyField label="Page Size">
              <select
                value={component.config.pageSize || 10}
                onChange={(e) => onUpdate({ pageSize: parseInt(e.target.value) })}
              >
                <option value={5}>5 rows</option>
                <option value={10}>10 rows</option>
                <option value={20}>20 rows</option>
                <option value={50}>50 rows</option>
              </select>
            </PropertyField>

            <PropertyField label="Show Search">
              <input
                type="checkbox"
                checked={component.config.showSearch || false}
                onChange={(e) => onUpdate({ showSearch: e.target.checked })}
              />
            </PropertyField>
          </>
        );

      case 'text':
        return (
          <>
            <PropertyField label="Content">
              <textarea
                value={component.config.content || ''}
                onChange={(e) => onUpdate({ content: e.target.value })}
                rows={4}
              />
            </PropertyField>

            <PropertyField label="Font Size">
              <input
                type="number"
                value={component.config.fontSize || 14}
                onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value) })}
                min={8}
                max={72}
              />
            </PropertyField>
          </>
        );

      default:
        return <p>No configuration available</p>;
    }
  };

  return <div className="config-tab">{renderConfigFields()}</div>;
}

// Data Binding Tab
function DataBindingTab({ component, availableFields, onUpdate }) {
  return (
    <div className="data-binding-tab">
      <p className="section-hint">
        Drag fields from the left panel to bind data to this component
      </p>

      {component.type === 'kpi' && (
        <PropertyField label="Value Field">
          <select
            value={component.dataBinding?.valueField || ''}
            onChange={(e) => onUpdate({ ...component.dataBinding, valueField: e.target.value })}
          >
            <option value="">Select field...</option>
            {availableFields.map(f => (
              <option key={f.fullName} value={f.fullName}>{f.label}</option>
            ))}
          </select>
        </PropertyField>
      )}

      {component.type === 'chart' && (
        <>
          <PropertyField label="Category (X-Axis)">
            <select
              value={component.dataBinding?.categoryField || ''}
              onChange={(e) => onUpdate({ ...component.dataBinding, categoryField: e.target.value })}
            >
              <option value="">Select field...</option>
              {availableFields.filter(f => f.type === 'string' || f.type === 'date').map(f => (
                <option key={f.fullName} value={f.fullName}>{f.label}</option>
              ))}
            </select>
          </PropertyField>

          <PropertyField label="Value (Y-Axis)">
            <select
              value={component.dataBinding?.valueField || ''}
              onChange={(e) => onUpdate({ ...component.dataBinding, valueField: e.target.value })}
            >
              <option value="">Select field...</option>
              {availableFields.filter(f => f.type === 'number').map(f => (
                <option key={f.fullName} value={f.fullName}>{f.label}</option>
              ))}
            </select>
          </PropertyField>
        </>
      )}

      <style jsx>{`
        .section-hint {
          font-size: 12px;
          color: var(--text-muted);
          margin-bottom: 16px;
        }
      `}</style>
    </div>
  );
}

// Style Tab
function StyleTab({ component, onUpdate }) {
  return (
    <div className="style-tab">
      <PropertyField label="Background Color">
        <input
          type="color"
          value={component.config.backgroundColor || '#ffffff'}
          onChange={(e) => onUpdate({ backgroundColor: e.target.value })}
        />
      </PropertyField>

      <PropertyField label="Border">
        <select
          value={component.config.borderStyle || 'none'}
          onChange={(e) => onUpdate({ borderStyle: e.target.value })}
        >
          <option value="none">None</option>
          <option value="solid">Solid</option>
          <option value="dashed">Dashed</option>
        </select>
      </PropertyField>

      <PropertyField label="Border Radius">
        <input
          type="number"
          value={component.config.borderRadius || 8}
          onChange={(e) => onUpdate({ borderRadius: parseInt(e.target.value) })}
          min={0}
          max={50}
        />
      </PropertyField>
    </div>
  );
}

// Layout Tab
function LayoutTab({ component, onUpdate }) {
  return (
    <div className="layout-tab">
      <div className="position-grid">
        <PropertyField label="X">
          <input
            type="number"
            value={Math.round(component.position.x)}
            onChange={(e) => onUpdate({ x: parseInt(e.target.value) })}
          />
        </PropertyField>

        <PropertyField label="Y">
          <input
            type="number"
            value={Math.round(component.position.y)}
            onChange={(e) => onUpdate({ y: parseInt(e.target.value) })}
          />
        </PropertyField>

        <PropertyField label="Width">
          <input
            type="number"
            value={Math.round(component.position.width)}
            onChange={(e) => onUpdate({ width: parseInt(e.target.value) })}
          />
        </PropertyField>

        <PropertyField label="Height">
          <input
            type="number"
            value={Math.round(component.position.height)}
            onChange={(e) => onUpdate({ height: parseInt(e.target.value) })}
          />
        </PropertyField>
      </div>

      <style jsx>{`
        .position-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
      `}</style>
    </div>
  );
}

// Property Field Component
function PropertyField({ label, children }) {
  return (
    <div className="property-field">
      <label>{label}</label>
      {children}

      <style jsx>{`
        .property-field {
          margin-bottom: 16px;
        }

        .property-field label {
          display: block;
          font-size: 11px;
          font-weight: 500;
          color: var(--text-muted);
          margin-bottom: 6px;
          text-transform: uppercase;
        }

        .property-field :global(input[type="text"]),
        .property-field :global(input[type="number"]),
        .property-field :global(select),
        .property-field :global(textarea) {
          width: 100%;
          padding: 8px 10px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
        }

        .property-field :global(input[type="checkbox"]) {
          width: 16px;
          height: 16px;
        }

        .property-field :global(input[type="color"]) {
          width: 100%;
          height: 36px;
          padding: 2px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
        }
      `}</style>
    </div>
  );
}

// Helper function
function getAvailableFields(state) {
  return state.dataSource.tables.flatMap(table =>
    table.fields.map(field => ({
      ...field,
      fullName: `${table.name}.${field.name}`,
      tableName: table.name,
    }))
  );
}
