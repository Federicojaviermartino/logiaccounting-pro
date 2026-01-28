/**
 * Document List Page
 */
import { useState, useEffect } from 'react';
import { 
  Search, Filter, Upload, FolderPlus, File, FileText, Image, 
  Download, Trash2, Share2, MoreVertical, ChevronLeft, ChevronRight,
  Grid, List, Eye
} from 'lucide-react';
import documentsAPI from '../services/documentsAPI';

const FILE_ICONS = {
  'application/pdf': <FileText className="text-red-500" />,
  'image/jpeg': <Image className="text-blue-500" />,
  'image/png': <Image className="text-blue-500" />,
  'application/vnd.ms-excel': <File className="text-green-500" />,
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': <File className="text-green-500" />,
  'default': <File className="text-gray-500" />
};

export default function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  const [viewMode, setViewMode] = useState('list');
  const [showUpload, setShowUpload] = useState(false);
  
  const [filters, setFilters] = useState({
    search: '',
    documentType: '',
    categoryId: ''
  });
  
  const [categories, setCategories] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);

  useEffect(() => {
    loadFilters();
    loadDocuments();
  }, []);

  const loadFilters = async () => {
    try {
      const [catRes, typeRes] = await Promise.all([
        documentsAPI.getCategories(),
        documentsAPI.getDocumentTypes()
      ]);
      setCategories(catRes.data);
      setDocumentTypes(typeRes.data);
    } catch (err) {
      console.error('Failed to load filters:', err);
    }
  };

  const loadDocuments = async (page = 1) => {
    try {
      setLoading(true);
      const response = await documentsAPI.getDocuments({
        page,
        pageSize: 24,
        ...filters
      });
      setDocuments(response.data.items);
      setPagination({
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total
      });
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadDocuments(1);
  };

  const handleDownload = async (doc) => {
    try {
      const response = await documentsAPI.downloadDocument(doc.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await documentsAPI.deleteDocument(docId);
      loadDocuments(pagination.page);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const getFileIcon = (mimeType) => {
    return FILE_ICONS[mimeType] || FILE_ICONS.default;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-500">Manage your files and documents</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Upload size={16} />
            Upload
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search documents..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={filters.documentType}
              onChange={(e) => setFilters({...filters, documentType: e.target.value})}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Types</option>
              {documentTypes.map(type => (
                <option key={type.code} value={type.code}>{type.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={filters.categoryId}
              onChange={(e) => setFilters({...filters, categoryId: e.target.value})}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
          
          <button
            type="submit"
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            <Filter size={16} />
          </button>
          
          <div className="flex border rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`p-2 ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
            >
              <List size={16} />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-2 ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
            >
              <Grid size={16} />
            </button>
          </div>
        </form>
      </div>

      {/* Document List/Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : viewMode === 'list' ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Size</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Modified</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No documents found
                  </td>
                </tr>
              ) : (
                documents.map(doc => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {getFileIcon(doc.mime_type)}
                        <div>
                          <p className="font-medium">{doc.title}</p>
                          <p className="text-xs text-gray-500">{doc.file_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm capitalize">
                      {doc.document_type.replace('_', ' ')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatSize(doc.file_size)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(doc.updated_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => handleDownload(doc)}
                          className="p-1 hover:bg-gray-100 rounded"
                          title="Download"
                        >
                          <Download size={16} className="text-gray-500" />
                        </button>
                        <button
                          onClick={() => {}}
                          className="p-1 hover:bg-gray-100 rounded"
                          title="Share"
                        >
                          <Share2 size={16} className="text-gray-500" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1 hover:bg-gray-100 rounded"
                          title="Delete"
                        >
                          <Trash2 size={16} className="text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          
          {/* Pagination */}
          <div className="px-4 py-3 border-t flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {pagination.total} documents
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => loadDocuments(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="p-2 border rounded-lg disabled:opacity-50"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="px-4 py-2">
                Page {pagination.page} of {pagination.pages}
              </span>
              <button
                onClick={() => loadDocuments(pagination.page + 1)}
                disabled={pagination.page >= pagination.pages}
                className="p-2 border rounded-lg disabled:opacity-50"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {documents.map(doc => (
            <div key={doc.id} className="bg-white rounded-lg shadow p-4 hover:shadow-md cursor-pointer">
              <div className="flex justify-center py-4">
                <div className="w-12 h-12 flex items-center justify-center">
                  {getFileIcon(doc.mime_type)}
                </div>
              </div>
              <p className="font-medium text-sm truncate text-center">{doc.title}</p>
              <p className="text-xs text-gray-500 text-center">{formatSize(doc.file_size)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <UploadModal onClose={() => setShowUpload(false)} onSuccess={() => {
          setShowUpload(false);
          loadDocuments(1);
        }} categories={categories} documentTypes={documentTypes} />
      )}
    </div>
  );
}

function UploadModal({ onClose, onSuccess, categories, documentTypes }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState('other');
  const [categoryId, setCategoryId] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title || file.name);
      formData.append('document_type', documentType);
      if (categoryId) formData.append('category_id', categoryId);
      
      await documentsAPI.upload(formData);
      onSuccess();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="font-semibold">Upload Document</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">×</button>
        </div>
        <form onSubmit={handleUpload} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
            <input
              type="file"
              onChange={(e) => {
                setFile(e.target.files[0]);
                if (!title) setTitle(e.target.files[0]?.name || '');
              }}
              className="w-full"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {documentTypes.map(type => (
                <option key={type.code} value={type.code}>{type.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">None</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || uploading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
