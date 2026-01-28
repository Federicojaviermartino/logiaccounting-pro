import { useState, useRef } from 'react';
import { documentsAPI } from '../services/api';
import toast from '../utils/toast';

export default function DocumentUploader({ entityType, entityId, onUpload }) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const allowedTypes = [
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/webp',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ];

  const handleFiles = async (files) => {
    if (!files.length) return;

    const file = files[0];

    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type. Allowed: PDF, PNG, JPG, WEBP, DOCX, XLSX');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.info('File too large. Maximum size: 10MB');
      return;
    }

    setUploading(true);
    try {
      const response = await documentsAPI.upload(entityType, entityId, file);
      if (onUpload) onUpload(response.data);
    } catch (error) {
      toast.error('Failed to upload: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  return (
    <div
      className={`document-uploader ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx"
        onChange={handleChange}
      />

      {uploading ? (
        <div className="text-center py-6">
          <div className="loading-spinner mx-auto mb-2"></div>
          <p className="text-muted">Uploading...</p>
        </div>
      ) : (
        <div
          className="text-center py-6 cursor-pointer"
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="text-4xl mb-2">📎</div>
          <p className="font-bold">Drop file here or click to upload</p>
          <p className="text-muted text-sm mt-1">
            PDF, PNG, JPG, WEBP, DOCX, XLSX (max 10MB)
          </p>
        </div>
      )}
    </div>
  );
}
