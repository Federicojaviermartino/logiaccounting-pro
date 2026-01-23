import React, { useState, useEffect } from 'react';
import { Search, Star, Download, Eye, Sparkles, Zap } from 'lucide-react';
import { workflowAPI } from '../../../services/api';

export default function TemplateMarketplace() {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [installing, setInstalling] = useState(null);

  useEffect(() => { loadData(); }, [selectedCategory, searchQuery]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [templatesRes, categoriesRes] = await Promise.all([
        workflowAPI.listTemplates({ category: selectedCategory, search: searchQuery }),
        workflowAPI.getTemplateCategories(),
      ]);
      setTemplates(templatesRes.data.items || []);
      setCategories(categoriesRes.data || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInstall = async (templateId) => {
    try {
      setInstalling(templateId);
      const result = await workflowAPI.installTemplate(templateId, {});
      alert(`Installed! Workflow: ${result.data.workflow_id}`);
      loadData();
    } catch (error) {
      alert('Failed to install');
    } finally {
      setInstalling(null);
    }
  };

  const handlePreview = async (template) => {
    const res = await workflowAPI.previewTemplate(template.id);
    setSelectedTemplate({ ...template, definition: res.data.definition });
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Workflow Templates</h1>
        <p className="text-gray-500">Pre-built automations ready to use</p>
      </div>

      <div className="grid grid-cols-[240px_1fr] gap-6">
        <aside className="bg-white border rounded-xl p-5 h-fit">
          <div className="flex items-center gap-2 px-3 py-2 border rounded-lg mb-5">
            <Search className="w-4 h-4 text-gray-400" />
            <input className="flex-1 outline-none" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          </div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">Categories</h3>
          <button className={`w-full text-left px-3 py-2 rounded-lg mb-1 ${!selectedCategory ? 'bg-blue-50 text-blue-600' : ''}`} onClick={() => setSelectedCategory('')}>All</button>
          {categories.map((cat) => (
            <button key={cat.id} className={`w-full flex justify-between px-3 py-2 rounded-lg mb-1 ${selectedCategory === cat.id ? 'bg-blue-50 text-blue-600' : ''}`} onClick={() => setSelectedCategory(cat.id)}>
              {cat.name} <span className="text-xs text-gray-400">{cat.count}</span>
            </button>
          ))}
        </aside>

        <main className="grid grid-cols-2 gap-5">
          {templates.map((tpl) => (
            <div key={tpl.id} className="bg-white border rounded-xl p-5 flex flex-col">
              <div className="flex justify-between mb-3">
                {tpl.is_official && <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded"><Sparkles className="w-3 h-3" /> Official</span>}
                <span className="text-xs text-gray-400 uppercase">{tpl.category}</span>
              </div>
              <h3 className="font-semibold mb-2">{tpl.name}</h3>
              <p className="text-sm text-gray-500 flex-1 mb-3">{tpl.description}</p>
              <div className="flex gap-1 mb-4">{tpl.tags?.slice(0, 3).map((tag) => <span key={tag} className="text-xs bg-gray-100 px-2 py-1 rounded">{tag}</span>)}</div>
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="flex gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1"><Star className="w-4 h-4" /> {tpl.rating || 'N/A'}</span>
                  <span className="flex items-center gap-1"><Download className="w-4 h-4" /> {tpl.install_count}</span>
                </div>
                <div className="flex gap-2">
                  <button className="p-2 border rounded-lg" onClick={() => handlePreview(tpl)}><Eye className="w-4 h-4" /></button>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg" onClick={() => handleInstall(tpl.id)} disabled={installing === tpl.id}>
                    {installing === tpl.id ? '...' : 'Install'}
                  </button>
                </div>
              </div>
            </div>
          ))}
          {templates.length === 0 && !isLoading && <div className="col-span-2 text-center py-16 text-gray-400"><Zap className="w-12 h-12 mx-auto mb-4" /><p>No templates found</p></div>}
        </main>
      </div>

      {selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedTemplate(null)}>
          <div className="bg-white rounded-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">{selectedTemplate.name}</h2>
            <p className="text-gray-600 mb-4">{selectedTemplate.description}</p>
            <h4 className="font-medium mb-2">Structure</h4>
            <div className="space-y-2 mb-6">
              <div className="px-4 py-3 bg-green-50 text-green-700 rounded-lg">Trigger: {selectedTemplate.definition?.trigger?.type}</div>
              {selectedTemplate.definition?.nodes?.filter(n => n.type !== 'trigger').map((n, i) => (
                <div key={i} className="px-4 py-3 bg-blue-50 text-blue-700 rounded-lg">{n.action_type || n.type}</div>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <button className="px-4 py-2 border rounded-lg" onClick={() => setSelectedTemplate(null)}>Cancel</button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg" onClick={() => { handleInstall(selectedTemplate.id); setSelectedTemplate(null); }}>Install</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
