/**
 * ReportPreview - Preview report with real data
 */

import React, { useState, useEffect } from 'react';
import { X, Download, Printer, FileText, Table, Presentation } from 'lucide-react';
import { reportsAPI } from '../../../services/api/reports';
import { LineChart, BarChart, PieChart, KPICard, DataTable } from './charts';

export default function ReportPreview({ reportId, onClose }) {
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportFormat, setExportFormat] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    loadReportData();
  }, [reportId]);

  const loadReportData = async () => {
    try {
      setIsLoading(true);
      const response = await reportsAPI.execute(reportId);
      setReportData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      setIsExporting(true);
      setExportFormat(format);

      const response = await reportsAPI.export(reportId, format);

      // Create download link
      const blob = new Blob([response.data], {
        type: getContentType(format)
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
      setExportFormat(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="preview-overlay">
        <div className="preview-loading">
          <div className="spinner" />
          <p>Loading report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="preview-overlay">
        <div className="preview-error">
          <p>Error loading report: {error}</p>
          <button onClick={loadReportData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="preview-overlay">
      <div className="preview-container">
        {/* Header */}
        <div className="preview-header">
          <div className="preview-title">
            <h2>{reportData?.report_name}</h2>
            <span className="preview-date">
              Generated: {new Date(reportData?.executed_at).toLocaleString()}
            </span>
          </div>

          <div className="preview-actions">
            <button
              className="export-btn"
              onClick={() => handleExport('pdf')}
              disabled={isExporting}
            >
              <FileText className="w-4 h-4" />
              PDF
            </button>
            <button
              className="export-btn"
              onClick={() => handleExport('xlsx')}
              disabled={isExporting}
            >
              <Table className="w-4 h-4" />
              Excel
            </button>
            <button
              className="export-btn"
              onClick={() => handleExport('pptx')}
              disabled={isExporting}
            >
              <Presentation className="w-4 h-4" />
              PowerPoint
            </button>
            <button className="export-btn" onClick={handlePrint}>
              <Printer className="w-4 h-4" />
              Print
            </button>
            <button className="close-btn" onClick={onClose}>
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Report Content */}
        <div className="preview-content">
          <div className="report-page">
            {reportData?.data?.components?.map((component, index) => (
              <div key={index} className="preview-component">
                {renderPreviewComponent(component)}
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        .preview-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .preview-container {
          width: 90vw;
          height: 90vh;
          background: var(--bg-primary);
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          border-bottom: 1px solid var(--border-color);
        }

        .preview-title h2 {
          margin: 0;
          font-size: 18px;
        }

        .preview-date {
          font-size: 12px;
          color: var(--text-muted);
        }

        .preview-actions {
          display: flex;
          gap: 8px;
        }

        .export-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
          transition: all 0.2s;
        }

        .export-btn:hover:not(:disabled) {
          background: var(--bg-secondary);
        }

        .export-btn:disabled {
          opacity: 0.5;
        }

        .close-btn {
          padding: 8px;
          border-radius: 6px;
          color: var(--text-muted);
          margin-left: 8px;
        }

        .close-btn:hover {
          background: var(--bg-secondary);
        }

        .preview-content {
          flex: 1;
          overflow: auto;
          padding: 40px;
          background: var(--bg-secondary);
        }

        .report-page {
          background: white;
          max-width: 900px;
          margin: 0 auto;
          padding: 40px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .preview-component {
          margin-bottom: 24px;
        }

        .preview-loading,
        .preview-error {
          text-align: center;
          color: var(--text-muted);
        }

        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--border-color);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @media print {
          .preview-header {
            display: none;
          }

          .preview-content {
            padding: 0;
            background: white;
          }

          .report-page {
            box-shadow: none;
          }
        }
      `}</style>
    </div>
  );
}

function renderPreviewComponent(component) {
  switch (component.type) {
    case 'chart':
      return renderChart(component);
    case 'kpi':
      return (
        <KPICard
          title={component.data?.title}
          value={component.data?.value}
          format={component.data?.format}
        />
      );
    case 'table':
      return (
        <DataTable
          title={component.data?.title}
          columns={component.data?.headers?.map(h => ({ key: h, label: h }))}
          data={component.data?.rows}
        />
      );
    default:
      return null;
  }
}

function renderChart(component) {
  const { chartType } = component.config || {};
  const props = {
    title: component.data?.title,
    data: component.data,
  };

  switch (chartType) {
    case 'line':
      return <LineChart {...props} />;
    case 'pie':
    case 'donut':
      return <PieChart {...props} config={{ donut: chartType === 'donut' }} />;
    default:
      return <BarChart {...props} />;
  }
}

function getContentType(format) {
  switch (format) {
    case 'pdf': return 'application/pdf';
    case 'xlsx': return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    case 'pptx': return 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    case 'csv': return 'text/csv';
    default: return 'application/octet-stream';
  }
}
