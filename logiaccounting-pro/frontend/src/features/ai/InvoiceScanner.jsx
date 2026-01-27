/**
 * Invoice Scanner Component
 * AI-powered OCR invoice scanning and extraction
 */

import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';

const API_BASE = '/api/v1/ai/invoice';

export default function InvoiceScanner() {
  const { t } = useTranslation();
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (file) => {
    if (!file) return;

    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF or image file (PNG, JPG)');
      return;
    }

    try {
      setScanning(true);
      setError(null);
      setScanResult(null);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('use_llm', 'true');

      const res = await fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!res.ok) throw new Error('Scan failed');

      const data = await res.json();
      setScanResult(data);
    } catch (err) {
      setError('Failed to scan invoice. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const approveAndCreate = async () => {
    if (!scanResult) return;

    try {
      await fetch(`${API_BASE}/scans/${scanResult.id}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      // In production, redirect to invoice creation with pre-filled data
      alert('Invoice approved! Ready to create.');
    } catch (err) {
      setError('Failed to approve invoice');
    }
  };

  return (
    <div className="ai-card invoice-scanner">
      <div className="ai-card-header">
        <span className="ai-icon">📄</span>
        <h3>Smart Invoice Scanner</h3>
      </div>

      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''} ${scanning ? 'scanning' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleInputChange}
          accept=".pdf,.png,.jpg,.jpeg"
          hidden
        />

        {scanning ? (
          <div className="scanning-state">
            <div className="scan-animation" />
            <p>Scanning invoice...</p>
          </div>
        ) : (
          <>
            <span className="upload-icon">📤</span>
            <p>Drop invoice here or click to upload</p>
            <span className="file-types">PDF, PNG, JPG</span>
          </>
        )}
      </div>

      {error && (
        <div className="scan-error">
          <span>⚠️</span>
          <p>{error}</p>
        </div>
      )}

      {scanResult && (
        <div className="scan-result">
          <div className="result-header">
            <h4>Extraction Results</h4>
            <span className={`confidence ${scanResult.ocr_confidence > 0.8 ? 'high' : 'medium'}`}>
              {(scanResult.ocr_confidence * 100).toFixed(0)}% confidence
            </span>
          </div>

          <div className="extracted-data">
            <div className="data-row">
              <span className="label">Vendor</span>
              <span className="value">{scanResult.extracted_data?.vendor_name || 'Not detected'}</span>
            </div>
            <div className="data-row">
              <span className="label">Invoice #</span>
              <span className="value">{scanResult.extracted_data?.invoice_number || 'Not detected'}</span>
            </div>
            <div className="data-row">
              <span className="label">Date</span>
              <span className="value">{scanResult.extracted_data?.invoice_date || 'Not detected'}</span>
            </div>
            <div className="data-row">
              <span className="label">Total</span>
              <span className="value highlight">
                ${scanResult.extracted_data?.total_amount?.toLocaleString() || 'Not detected'}
              </span>
            </div>
            <div className="data-row">
              <span className="label">Category</span>
              <span className="value">
                {scanResult.category || 'Uncategorized'}
                {scanResult.category_confidence && (
                  <span className="confidence-badge">
                    {(scanResult.category_confidence * 100).toFixed(0)}%
                  </span>
                )}
              </span>
            </div>
            <div className="data-row">
              <span className="label">GL Account</span>
              <span className="value">{scanResult.suggested_gl_account || 'Not assigned'}</span>
            </div>
          </div>

          {scanResult.validation_errors && scanResult.validation_errors.length > 0 && (
            <div className="validation-warnings">
              <h5>⚠️ Review Required</h5>
              <ul>
                {scanResult.validation_errors.map((err, idx) => (
                  <li key={idx} className={`severity-${err.severity}`}>
                    {err.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="result-actions">
            <button className="btn-secondary" onClick={() => setScanResult(null)}>
              Scan Another
            </button>
            <button className="btn-primary" onClick={approveAndCreate}>
              Approve & Create Invoice
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
