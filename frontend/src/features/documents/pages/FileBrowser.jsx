/**
 * File Browser Page with Folder Navigation
 */
import { useState, useEffect } from 'react';
import { 
  Folder, File, ChevronRight, Home, FolderPlus, 
  Upload, MoreVertical, ArrowLeft
} from 'lucide-react';
import documentsAPI from '../services/documentsAPI';

export default function FileBrowser() {
  const [currentFolder, setCurrentFolder] = useState(null);
  const [contents, setContents] = useState({ subfolders: [], documents: [], breadcrumbs: [] });
  const [folderTree, setFolderTree] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewFolder, setShowNewFolder] = useState(false);

  useEffect(() => {
    loadFolderTree();
    loadRootFolders();
  }, []);

  const loadFolderTree = async () => {
    try {
      const response = await documentsAPI.getFolderTree();
      setFolderTree(response.data);
    } catch (err) {
      console.error('Failed to load folder tree:', err);
    }
  };

  const loadRootFolders = async () => {
    try {
      setLoading(true);
      const foldersRes = await documentsAPI.getFolders();
      const docsRes = await documentsAPI.getDocuments({ pageSize: 50 });
      
      setContents({
        subfolders: foldersRes.data,
        documents: docsRes.data.items,
        breadcrumbs: []
      });
      setCurrentFolder(null);
    } catch (err) {
      console.error('Failed to load root:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadFolderContents = async (folderId) => {
    try {
      setLoading(true);
      const response = await documentsAPI.getFolderContents(folderId);
      setContents({
        subfolders: response.data.subfolders,
        documents: response.data.documents,
        breadcrumbs: response.data.breadcrumbs
      });
      setCurrentFolder(response.data.folder);
    } catch (err) {
      console.error('Failed to load folder:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async (name) => {
    try {
      await documentsAPI.createFolder({
        name,
        parent_id: currentFolder?.id || null
      });
      setShowNewFolder(false);
      loadFolderTree();
      if (currentFolder) {
        loadFolderContents(currentFolder.id);
      } else {
        loadRootFolders();
      }
    } catch (err) {
      console.error('Failed to create folder:', err);
    }
  };

  const navigateUp = () => {
    if (contents.breadcrumbs.length > 1) {
      const parentId = contents.breadcrumbs[contents.breadcrumbs.length - 2].id;
      loadFolderContents(parentId);
    } else {
      loadRootFolders();
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="flex h-[calc(100vh-200px)]">
      {/* Sidebar - Folder Tree */}
      <div className="w-64 border-r bg-gray-50 overflow-y-auto">
        <div className="p-4">
          <button
            onClick={loadRootFolders}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-gray-100"
          >
            <Home size={16} />
            <span>All Files</span>
          </button>
          
          <div className="mt-4">
            <FolderTreeNode 
              folders={folderTree} 
              onSelect={loadFolderContents}
              currentFolderId={currentFolder?.id}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="p-4 border-b flex justify-between items-center">
          <div className="flex items-center gap-2">
            {currentFolder && (
              <button
                onClick={navigateUp}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeft size={16} />
              </button>
            )}
            
            {/* Breadcrumbs */}
            <div className="flex items-center gap-1 text-sm">
              <button
                onClick={loadRootFolders}
                className="hover:text-blue-600"
              >
                Home
              </button>
              {contents.breadcrumbs.map((crumb, idx) => (
                <span key={crumb.id} className="flex items-center gap-1">
                  <ChevronRight size={14} className="text-gray-400" />
                  <button
                    onClick={() => loadFolderContents(crumb.id)}
                    className="hover:text-blue-600"
                  >
                    {crumb.name}
                  </button>
                </span>
              ))}
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setShowNewFolder(true)}
              className="flex items-center gap-2 px-3 py-2 border rounded-lg hover:bg-gray-50"
            >
              <FolderPlus size={16} />
              New Folder
            </button>
            <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Upload size={16} />
              Upload
            </button>
          </div>
        </div>

        {/* File/Folder Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {/* Folders */}
              {contents.subfolders.map(folder => (
                <div
                  key={folder.id}
                  onClick={() => loadFolderContents(folder.id)}
                  className="bg-white rounded-lg border p-4 hover:shadow-md cursor-pointer group"
                >
                  <div className="flex justify-center py-2">
                    <Folder size={40} className="text-yellow-500" />
                  </div>
                  <p className="font-medium text-sm truncate text-center mt-2">
                    {folder.name}
                  </p>
                  <p className="text-xs text-gray-500 text-center">
                    {folder.document_count} items
                  </p>
                </div>
              ))}
              
              {/* Documents */}
              {contents.documents.map(doc => (
                <div
                  key={doc.id}
                  className="bg-white rounded-lg border p-4 hover:shadow-md cursor-pointer group"
                >
                  <div className="flex justify-center py-2">
                    <File size={40} className="text-gray-400" />
                  </div>
                  <p className="font-medium text-sm truncate text-center mt-2">
                    {doc.title}
                  </p>
                  <p className="text-xs text-gray-500 text-center">
                    {formatSize(doc.file_size)}
                  </p>
                </div>
              ))}
              
              {contents.subfolders.length === 0 && contents.documents.length === 0 && (
                <div className="col-span-full text-center py-12 text-gray-500">
                  This folder is empty
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* New Folder Modal */}
      {showNewFolder && (
        <NewFolderModal
          onClose={() => setShowNewFolder(false)}
          onCreate={handleCreateFolder}
        />
      )}
    </div>
  );
}

function FolderTreeNode({ folders, onSelect, currentFolderId, depth = 0 }) {
  return (
    <div className={depth > 0 ? 'ml-4' : ''}>
      {folders.map(folder => (
        <div key={folder.id}>
          <button
            onClick={() => onSelect(folder.id)}
            className={`flex items-center gap-2 w-full px-3 py-1.5 rounded text-sm text-left hover:bg-gray-200 ${
              currentFolderId === folder.id ? 'bg-blue-100 text-blue-700' : ''
            }`}
          >
            <Folder size={14} className="text-yellow-500" />
            <span className="truncate">{folder.name}</span>
          </button>
          {folder.children && folder.children.length > 0 && (
            <FolderTreeNode
              folders={folder.children}
              onSelect={onSelect}
              currentFolderId={currentFolderId}
              depth={depth + 1}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function NewFolderModal({ onClose, onCreate }) {
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name.trim()) {
      onCreate(name.trim());
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-sm w-full mx-4">
        <div className="p-4 border-b">
          <h3 className="font-semibold">New Folder</h3>
        </div>
        <form onSubmit={handleSubmit} className="p-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Folder name"
            className="w-full px-3 py-2 border rounded-lg"
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
