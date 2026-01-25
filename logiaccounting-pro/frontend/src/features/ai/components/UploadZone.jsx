/**
 * Upload Zone Component
 * Drag and drop file upload for documents
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

const UploadZone = ({
  onFilesSelected,
  accept = {
    'application/pdf': ['.pdf'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
  },
  maxSize = 10 * 1024 * 1024,
  maxFiles = 10,
  multiple = true,
}) => {
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle accepted files
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: 'pending',
    }));

    setFiles(prev => [...prev, ...newFiles]);
    onFilesSelected?.(acceptedFiles);

    // Handle rejected files
    const newErrors = rejectedFiles.map(({ file, errors }) => ({
      file: file.name,
      errors: errors.map(e => e.message),
    }));

    if (newErrors.length > 0) {
      setErrors(prev => [...prev, ...newErrors]);
    }
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles,
    multiple,
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearErrors = () => {
    setErrors([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragActive && !isDragReject ? 'border-blue-500 bg-blue-50' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
          ${!isDragActive ? 'border-gray-300 hover:border-gray-400 hover:bg-gray-50' : ''}
        `}
      >
        <input {...getInputProps()} />

        <Upload
          className={`mx-auto mb-4 ${
            isDragActive && !isDragReject ? 'text-blue-500' :
            isDragReject ? 'text-red-500' : 'text-gray-400'
          }`}
          size={48}
        />

        {isDragReject ? (
          <div>
            <div className="text-lg font-medium text-red-600">Invalid file type</div>
            <div className="text-sm text-red-500">Please upload PDF or image files</div>
          </div>
        ) : isDragActive ? (
          <div className="text-lg font-medium text-blue-600">Drop files here</div>
        ) : (
          <div>
            <div className="text-lg font-medium text-gray-700">
              Drag & drop files here
            </div>
            <div className="text-sm text-gray-500 mt-1">
              or click to browse
            </div>
            <div className="text-xs text-gray-400 mt-2">
              PDF, JPG, PNG up to {formatFileSize(maxSize)}
            </div>
          </div>
        )}
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-red-800 font-medium flex items-center gap-2">
              <AlertCircle size={18} />
              Upload Errors
            </span>
            <button
              onClick={clearErrors}
              className="text-red-600 hover:text-red-800"
            >
              <X size={18} />
            </button>
          </div>
          <ul className="text-sm text-red-700 space-y-1">
            {errors.map((error, i) => (
              <li key={i}>
                {error.file}: {error.errors.join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(({ file, id, status }) => (
            <div
              key={id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <File className="text-gray-400" size={20} />
                <div>
                  <div className="font-medium text-sm">{file.name}</div>
                  <div className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {status === 'pending' && (
                  <span className="text-xs text-gray-500">Pending</span>
                )}
                {status === 'processing' && (
                  <span className="text-xs text-blue-600">Processing...</span>
                )}
                {status === 'complete' && (
                  <CheckCircle className="text-green-500" size={18} />
                )}
                {status === 'error' && (
                  <AlertCircle className="text-red-500" size={18} />
                )}

                <button
                  onClick={() => removeFile(id)}
                  className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadZone;
