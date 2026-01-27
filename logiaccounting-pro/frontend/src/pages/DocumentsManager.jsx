/**
 * Documents Manager Page - Phase 13
 * Full-featured document management interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '../services/documentsApi';

const DocumentsManager = () => {
  const { t } = useTranslation();

  // State
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    category_id: '',
    document_type: '',
    status: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0,
  });
  const [viewMode, setViewMode] = useState('grid');
  const [selectedIds, setSelectedIds] = useState([]);
  const [stats, setStats] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);

  // Load documents
  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      };

      if (searchQuery) {
        params.search = searchQuery;
      }

      const result = await documentsApi.list(params);
      setDocuments(result.documents || []);
      setPagination(prev => ({
        ...prev,
        total: result.pagination?.total || 0,
        total_pages: result.pagination?.total_pages || 0,
      }));
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters, searchQuery]);

  // Load categories and tags
  const loadMetadata = async () => {
    try {
      const [cats, tagsList, storageStats] = await Promise.all([
        documentsApi.getCategories(),
        documentsApi.getTags(),
        documentsApi.getStats(),
      ]);
      setCategories(cats || []);
      setTags(tagsList || []);
      setStats(storageStats);
    } catch (error) {
      console.error('Failed to load metadata:', error);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    loadMetadata();
  }, []);

  // Handle file upload
  const handleFileUpload = async (files) => {
    setUploading(true);

    for (const file of files) {
      const fileId = `${file.name}-${Date.now()}`;

      setUploadProgress(prev => ({
        ...prev,
        [fileId]: { name: file.name, progress: 0, status: 'uploading' },
      }));

      try {
        await documentsApi.upload(file, {
          onProgress: (progress) => {
            setUploadProgress(prev => ({
              ...prev,
              [fileId]: { ...prev[fileId], progress },
            }));
          },
        });

        setUploadProgress(prev => ({
          ...prev,
          [fileId]: { ...prev[fileId], progress: 100, status: 'complete' },
        }));
      } catch (error) {
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: { ...prev[fileId], status: 'error', error: error.message },
        }));
      }
    }

    setUploading(false);
    loadDocuments();

    // Clear completed uploads after 3 seconds
    setTimeout(() => {
      setUploadProgress(prev => {
        const filtered = {};
        Object.entries(prev).forEach(([key, value]) => {
          if (value.status !== 'complete') {
            filtered[key] = value;
          }
        });
        return filtered;
      });
    }, 3000);
  };

  // Handle drag and drop
  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  // Handle document actions
  const handleDelete = async (docIds) => {
    if (!window.confirm(t('documents.confirmDelete', 'Are you sure you want to delete the selected documents?'))) {
      return;
    }

    try {
      await Promise.all(docIds.map(id => documentsApi.delete(id)));
      setSelectedIds([]);
      loadDocuments();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const handleDownload = async (docIds) => {
    for (const id of docIds) {
      try {
        const url = await documentsApi.getDownloadUrl(id);
        window.open(url, '_blank');
      } catch (error) {
        console.error('Download failed:', error);
      }
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    loadDocuments();
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === documents.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(documents.map(d => d.id));
    }
  };

  // Format file size
  const formatSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  // Get document type icon
  const getTypeIcon = (mimeType) => {
    if (mimeType?.includes('pdf')) return '📄';
    if (mimeType?.includes('image')) return '🖼️';
    if (mimeType?.includes('word') || mimeType?.includes('document')) return '📝';
    if (mimeType?.includes('excel') || mimeType?.includes('sheet')) return '📊';
    return '📎';
  };

  return (
    <div className="p-6" onDrop={handleDrop} onDragOver={handleDragOver}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('documents.title', 'Documents')}
          </h1>
          {stats && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {stats.total_documents} {t('documents.files', 'files')} • {stats.total_size_formatted}
            </p>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {viewMode === 'grid' ? '☰' : '⊞'}
          </button>

          <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">
            <input
              type="file"
              multiple
              className="hidden"
              onChange={(e) => handleFileUpload(Array.from(e.target.files))}
            />
            {t('documents.upload', 'Upload')}
          </label>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4 flex-wrap">
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder={t('documents.searchPlaceholder', 'Search documents...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          <select
            value={filters.category_id}
            onChange={(e) => setFilters(prev => ({ ...prev, category_id: e.target.value }))}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
          >
            <option value="">{t('documents.allCategories', 'All Categories')}</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          <select
            value={filters.document_type}
            onChange={(e) => setFilters(prev => ({ ...prev, document_type: e.target.value }))}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
          >
            <option value="">{t('documents.allTypes', 'All Types')}</option>
            <option value="invoice">{t('documents.types.invoice', 'Invoice')}</option>
            <option value="receipt">{t('documents.types.receipt', 'Receipt')}</option>
            <option value="contract">{t('documents.types.contract', 'Contract')}</option>
            <option value="report">{t('documents.types.report', 'Report')}</option>
            <option value="other">{t('documents.types.other', 'Other')}</option>
          </select>

          <button
            type="submit"
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            {t('common.search', 'Search')}
          </button>
        </form>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="mb-6 space-y-2">
          {Object.entries(uploadProgress).map(([key, upload]) => (
            <div
              key={key}
              className={`p-3 rounded-lg flex items-center gap-3 ${
                upload.status === 'complete' ? 'bg-green-50 dark:bg-green-900/20' :
                upload.status === 'error' ? 'bg-red-50 dark:bg-red-900/20' :
                'bg-blue-50 dark:bg-blue-900/20'
              }`}
            >
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
                  {upload.name}
                </p>
                {upload.status === 'uploading' && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}
                {upload.error && (
                  <p className="text-xs text-red-600 mt-1">{upload.error}</p>
                )}
              </div>
              {upload.status === 'complete' && <span className="text-green-600">✓</span>}
              {upload.status === 'error' && <span className="text-red-600">✕</span>}
            </div>
          ))}
        </div>
      )}

      {/* Bulk Actions */}
      {selectedIds.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-between">
          <span className="text-sm text-blue-700 dark:text-blue-300">
            {selectedIds.length} {t('documents.selected', 'selected')}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => handleDownload(selectedIds)}
              className="px-3 py-1 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              {t('common.download', 'Download')}
            </button>
            <button
              onClick={() => handleDelete(selectedIds)}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              {t('common.delete', 'Delete')}
            </button>
          </div>
        </div>
      )}

      {/* Documents Grid/List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="text-6xl mb-4">📂</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {t('documents.empty', 'No documents found')}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {t('documents.emptyHint', 'Upload your first document or drag and drop files here')}
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {documents.map(doc => (
            <div
              key={doc.id}
              className={`bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer ${
                selectedIds.includes(doc.id) ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelectedDocument(doc)}
            >
              <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <span className="text-3xl">{getTypeIcon(doc.mime_type)}</span>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(doc.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelect(doc.id);
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <h3 className="font-medium text-gray-900 dark:text-white truncate mb-1">
                  {doc.name}
                </h3>

                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatSize(doc.file_size)} • {formatDate(doc.created_at)}
                </p>

                {doc.document_type && doc.document_type !== 'other' && (
                  <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded capitalize">
                    {doc.document_type}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === documents.length}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {t('documents.name', 'Name')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {t('documents.type', 'Type')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {t('documents.size', 'Size')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {t('documents.modified', 'Modified')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {t('documents.actions', 'Actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {documents.map(doc => (
                <tr
                  key={doc.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                  onClick={() => setSelectedDocument(doc)}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(doc.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleSelect(doc.id);
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{getTypeIcon(doc.mime_type)}</span>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white truncate max-w-xs">
                          {doc.name}
                        </p>
                        {doc.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">
                            {doc.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {doc.document_type || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {formatSize(doc.file_size)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(doc.updated_at || doc.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload([doc.id]);
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title={t('common.download', 'Download')}
                      >
                        ⬇
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete([doc.id]);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title={t('common.delete', 'Delete')}
                      >
                        🗑
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            {t('common.previous', 'Previous')}
          </button>

          <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
            {pagination.page} / {pagination.total_pages}
          </span>

          <button
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            disabled={pagination.page === pagination.total_pages}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            {t('common.next', 'Next')}
          </button>
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">{getTypeIcon(selectedDocument.mime_type)}</span>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                      {selectedDocument.name}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {selectedDocument.original_filename}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedDocument(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('documents.size', 'Size')}</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formatSize(selectedDocument.file_size)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('documents.type', 'Type')}</p>
                  <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedDocument.document_type || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('documents.created', 'Created')}</p>
                  <p className="font-medium text-gray-900 dark:text-white">{formatDate(selectedDocument.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t('documents.version', 'Version')}</p>
                  <p className="font-medium text-gray-900 dark:text-white">{selectedDocument.version_number || 1}</p>
                </div>
              </div>

              {selectedDocument.description && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{t('documents.description', 'Description')}</p>
                  <p className="text-gray-900 dark:text-white">{selectedDocument.description}</p>
                </div>
              )}

              {selectedDocument.ocr_text && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{t('documents.ocrText', 'Extracted Text')}</p>
                  <p className="text-gray-700 dark:text-gray-300 text-sm bg-gray-50 dark:bg-gray-900 p-3 rounded max-h-40 overflow-auto">
                    {selectedDocument.ocr_text.substring(0, 500)}...
                  </p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => handleDownload([selectedDocument.id])}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {t('common.download', 'Download')}
                </button>
                <button
                  onClick={() => {
                    handleDelete([selectedDocument.id]);
                    setSelectedDocument(null);
                  }}
                  className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  {t('common.delete', 'Delete')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsManager;
