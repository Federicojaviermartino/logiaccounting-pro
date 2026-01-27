/**
 * Document Scanner Page
 * AI-powered invoice and receipt OCR
 */

import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Edit2,
  Eye,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { aiAPI } from '../services/aiAPI';

const DocumentScanner = () => {
  const { t } = useTranslation();

  const [documents, setDocuments] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});

  const onDrop = useCallback(async (acceptedFiles) => {
    setProcessing(true);

    for (const file of acceptedFiles) {
      try {
        const result = await aiAPI.processDocument(file);
        setDocuments(prev => [{
          ...result,
          filename: file.name,
          uploadedAt: new Date().toISOString(),
        }, ...prev]);
      } catch (error) {
        console.error('Processing failed:', error);
        setDocuments(prev => [{
          document_id: `error_${Date.now()}`,
          filename: file.name,
          status: 'failed',
          error: error.message,
          uploadedAt: new Date().toISOString(),
        }, ...prev]);
      }
    }

    setProcessing(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleApprove = async (docId) => {
    try {
      await aiAPI.approveDocument(docId);
      setDocuments(prev => prev.map(doc =>
        doc.document_id === docId ? { ...doc, status: 'completed' } : doc
      ));
    } catch (error) {
      console.error('Approve failed:', error);
    }
  };

  const handleEdit = (doc) => {
    setSelectedDoc(doc);
    setEditData(doc.extracted_data || {});
    setEditMode(true);
  };

  const handleSaveEdit = async () => {
    try {
      await aiAPI.updateDocument(selectedDoc.document_id, { updates: editData });
      setDocuments(prev => prev.map(doc =>
        doc.document_id === selectedDoc.document_id
          ? { ...doc, extracted_data: editData }
          : doc
      ));
      setEditMode(false);
      setSelectedDoc(null);
    } catch (error) {
      console.error('Update failed:', error);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={18} />;
      case 'failed': return <XCircle className="text-red-500" size={18} />;
      case 'needs_review': return <AlertTriangle className="text-yellow-500" size={18} />;
      default: return <Clock className="text-gray-500" size={18} />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Document Scanner</h1>
        <p className="text-gray-600">Upload invoices and receipts for AI-powered data extraction</p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`mx-auto mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} size={48} />
        {processing ? (
          <div>
            <div className="text-lg font-medium text-gray-700">Processing...</div>
            <div className="text-sm text-gray-500">Extracting data from documents</div>
          </div>
        ) : isDragActive ? (
          <div className="text-lg font-medium text-blue-600">Drop files here</div>
        ) : (
          <div>
            <div className="text-lg font-medium text-gray-700">Drag & drop files here</div>
            <div className="text-sm text-gray-500">or click to browse (PDF, JPG, PNG up to 10MB)</div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h2 className="font-semibold">Processed Documents</h2>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents processed yet. Upload your first document above.
          </div>
        ) : (
          <div className="divide-y">
            {documents.map((doc) => (
              <div key={doc.document_id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <FileText className="text-gray-400 mt-1" size={24} />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{doc.filename}</span>
                        {getStatusIcon(doc.status)}
                      </div>
                      {doc.extracted_data && (
                        <div className="mt-1 text-sm text-gray-600">
                          <span className="font-medium">{doc.extracted_data.vendor?.name || 'Unknown Vendor'}</span>
                          {' • '}
                          <span>{doc.extracted_data.invoice_number || 'No Number'}</span>
                          {' • '}
                          <span className="font-medium">{formatCurrency(doc.extracted_data.total)}</span>
                        </div>
                      )}
                      {doc.error && (
                        <div className="mt-1 text-sm text-red-600">{doc.error}</div>
                      )}
                      {doc.confidence && (
                        <div className="mt-1 text-xs text-gray-500">
                          Confidence: {(doc.confidence * 100).toFixed(0)}%
                          {doc.suggested_category && ` • Category: ${doc.suggested_category}`}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {doc.status === 'needs_review' && (
                      <button
                        onClick={() => handleApprove(doc.document_id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedDoc(doc)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="View Details"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(doc)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedDoc && !editMode && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Document Details</h2>
              <button onClick={() => setSelectedDoc(null)} className="text-gray-500 hover:text-gray-700">
                <XCircle size={24} />
              </button>
            </div>

            {selectedDoc.extracted_data && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Vendor</label>
                    <div className="font-medium">{selectedDoc.extracted_data.vendor?.name || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Invoice Number</label>
                    <div className="font-medium">{selectedDoc.extracted_data.invoice_number || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Invoice Date</label>
                    <div className="font-medium">{selectedDoc.extracted_data.invoice_date || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Due Date</label>
                    <div className="font-medium">{selectedDoc.extracted_data.due_date || '-'}</div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">Line Items</h3>
                  {selectedDoc.extracted_data.line_items?.map((item, i) => (
                    <div key={i} className="flex justify-between py-2 border-b">
                      <span>{item.description}</span>
                      <span>{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.tax_amount)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg">
                    <span>Total</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.total)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentScanner;
