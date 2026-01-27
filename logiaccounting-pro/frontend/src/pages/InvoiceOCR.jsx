import { useState, useRef, useEffect } from 'react';
import { ocrAPI, transactionsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function InvoiceOCR() {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [ocrStatus, setOcrStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOcrStatus();
  }, []);

  const loadOcrStatus = async () => {
    try {
      const res = await ocrAPI.getStatus();
      setOcrStatus(res.data);
    } catch (err) {
      console.error('Failed to load OCR status:', err);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);

      // Create preview for images
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result);
        reader.readAsDataURL(selectedFile);
      } else {
        setPreview(null);
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setResult(null);
      setError(null);

      if (droppedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result);
        reader.readAsDataURL(droppedFile);
      } else {
        setPreview(null);
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const processInvoice = async (autoCreate = false) => {
    if (!file) return;

    setProcessing(true);
    setError(null);

    try {
      const res = await ocrAPI.processInvoice(file, autoCreate);
      setResult(res.data);
      if (autoCreate && res.data.auto_created) {
        alert('Transaction created successfully!');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const createTransaction = async () => {
    if (!result?.extracted_data) return;

    const data = result.extracted_data;

    try {
      await ocrAPI.createFromExtracted({
        vendor_name: data.vendor_name,
        invoice_number: data.invoice_number,
        invoice_date: data.invoice_date,
        due_date: data.due_date,
        subtotal: data.subtotal,
        tax_amount: data.tax_amount || 0,
        total_amount: data.total_amount,
        category_id: data.suggested_category_id,
        project_id: data.suggested_project_id,
        description: `Invoice from ${data.vendor_name || 'Unknown'}`,
        create_payment: !!data.due_date
      });
      alert('Transaction created successfully!');
    } catch (err) {
      alert('Failed to create transaction: ' + (err.response?.data?.detail || err.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#22c55e';
    if (confidence >= 0.5) return '#eab308';
    return '#ef4444';
  };

  return (
    <>
      <div className="info-banner mb-6">
        📄 Upload invoices (PDF, JPG, PNG) to automatically extract data and create transactions.
        {ocrStatus && (
          <span className="ml-2">
            | Tesseract: {ocrStatus.tesseract_available ? '✅' : '❌'}
            | OpenAI Vision: {ocrStatus.openai_vision_available ? '✅' : '❌'}
            | PDF Support: {ocrStatus.pdf_support ? '✅' : '❌'}
          </span>
        )}
      </div>

      <div className="grid-2">
        {/* Upload Section */}
        <div className="section">
          <h3 className="section-title">Upload Invoice</h3>

          <div
            className="upload-zone"
            style={{
              border: '2px dashed var(--gray-300)',
              borderRadius: '12px',
              padding: '40px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              background: file ? 'var(--gray-50)' : 'white'
            }}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {preview ? (
              <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px' }} />
            ) : file && file.type === 'application/pdf' ? (
              <>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📄</div>
                <p className="font-bold">PDF Selected</p>
              </>
            ) : (
              <>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📄</div>
                <p className="font-bold">Drop invoice here or click to browse</p>
                <p className="text-muted">Supports PDF, JPG, PNG, TIFF up to 10MB</p>
              </>
            )}

            {file && (
              <div className="mt-4">
                <span className="badge badge-primary">{file.name}</span>
                <span className="text-muted ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-4">
            <button
              className="btn btn-primary"
              onClick={() => processInvoice(false)}
              disabled={!file || processing}
            >
              {processing ? 'Processing...' : '🔍 Extract Data'}
            </button>
            <button
              className="btn btn-success"
              onClick={() => processInvoice(true)}
              disabled={!file || processing}
            >
              {processing ? 'Processing...' : '⚡ Extract & Create'}
            </button>
          </div>

          {error && (
            <div className="info-banner mt-4" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' }}>
              ❌ {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="section">
          <h3 className="section-title">Extracted Data</h3>

          {result?.extracted_data ? (
            <>
              {/* Confidence Score */}
              <div className="mb-4" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className="font-bold">Confidence:</span>
                <div style={{
                  width: '100px',
                  height: '8px',
                  background: '#e5e7eb',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(result.extracted_data.confidence_score || 0) * 100}%`,
                    height: '100%',
                    background: getConfidenceColor(result.extracted_data.confidence_score),
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span>{((result.extracted_data.confidence_score || 0) * 100).toFixed(0)}%</span>
                <span className="badge badge-gray">{result.extracted_data.extraction_method}</span>
              </div>

              <div className="grid-2 mb-4">
                <div className="form-group">
                  <label className="form-label">Vendor</label>
                  <input className="form-input" value={result.extracted_data.vendor_name || 'Not detected'} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice #</label>
                  <input className="form-input" value={result.extracted_data.invoice_number || 'Not detected'} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice Date</label>
                  <input className="form-input" value={result.extracted_data.invoice_date || 'Not detected'} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Due Date</label>
                  <input className="form-input" value={result.extracted_data.due_date || 'Not detected'} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Subtotal</label>
                  <input className="form-input" value={result.extracted_data.subtotal ? formatCurrency(result.extracted_data.subtotal) : 'Not detected'} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Tax Amount</label>
                  <input className="form-input" value={result.extracted_data.tax_amount ? formatCurrency(result.extracted_data.tax_amount) : 'Not detected'} readOnly />
                </div>
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label">Total Amount</label>
                  <input
                    className="form-input font-bold"
                    style={{ fontSize: '1.25rem' }}
                    value={result.extracted_data.total_amount ? formatCurrency(result.extracted_data.total_amount) : 'Not detected'}
                    readOnly
                  />
                </div>
              </div>

              {result.extracted_data.line_items?.length > 0 && (
                <>
                  <h4 className="font-bold mb-2">Line Items</h4>
                  <div className="table-container mb-4">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Description</th>
                          <th>Qty</th>
                          <th>Unit Price</th>
                          <th>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.extracted_data.line_items.map((item, i) => (
                          <tr key={i}>
                            <td>{item.description}</td>
                            <td>{item.quantity}</td>
                            <td>{formatCurrency(item.unit_price)}</td>
                            <td className="font-bold">{formatCurrency(item.total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {result.extracted_data.suggested_category_name && (
                <div className="info-banner mb-4">
                  💡 Suggested Category: <strong>{result.extracted_data.suggested_category_name}</strong>
                </div>
              )}

              {result.extracted_data.suggested_project_code && (
                <div className="info-banner mb-4">
                  📁 Suggested Project: <strong>{result.extracted_data.suggested_project_code}</strong>
                </div>
              )}

              {!result.auto_created && (
                <button className="btn btn-success mt-4" onClick={createTransaction}>
                  ✅ Create Transaction
                </button>
              )}

              {result.auto_created && (
                <div className="info-banner" style={{ background: '#f0fdf4', borderColor: '#bbf7d0', color: '#16a34a' }}>
                  ✅ Transaction created automatically!
                </div>
              )}
            </>
          ) : (
            <div className="text-center text-muted" style={{ padding: '60px 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📋</div>
              <p>Upload and process an invoice to see extracted data</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
