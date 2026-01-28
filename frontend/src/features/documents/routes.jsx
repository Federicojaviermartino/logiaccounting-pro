import DocumentList from './pages/DocumentList';
import FileBrowser from './pages/FileBrowser';

export const documentRoutes = [
  { path: '/documents', element: <DocumentList />, title: 'Documents' },
  { path: '/documents/browse', element: <FileBrowser />, title: 'File Browser' }
];
