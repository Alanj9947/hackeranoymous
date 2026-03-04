import React, { useState, useEffect } from 'react';
import {
  Search, Plus, BookOpen, AlertCircle, Loader, Trash2,
  FileText, Tag, Folder
} from 'lucide-react';

/**
 * Knowledge Base Component - Search and manage knowledge base documents.
 */
function KnowledgeBase({ companyId = 'default' }) {
  const [activeTab, setActiveTab] = useState('search'); // search, documents, create
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  
  const [createForm, setCreateForm] = useState({
    title: '',
    content: '',
    doc_type: 'article',
    category: 'general',
    tags: ''
  });
  const [creating, setCreating] = useState(false);

  const docTypes = [
    { value: 'faq', label: 'FAQ' },
    { value: 'article', label: 'Article' },
    { value: 'guide', label: 'Guide' },
    { value: 'troubleshooting', label: 'Troubleshooting' },
    { value: 'policy', label: 'Policy' },
    { value: 'product', label: 'Product' }
  ];

  const categories = [
    'general',
    'billing',
    'technical',
    'account',
    'product',
    'support'
  ];

  // Load documents on mount and tab change
  useEffect(() => {
    if (activeTab === 'documents') {
      loadDocuments();
    }
  }, [activeTab, categoryFilter, typeFilter]);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (typeFilter) params.append('doc_type', typeFilter);

      const response = await fetch(
        `/api/v1/knowledge-base/documents?${params}`
      );

      if (!response.ok) throw new Error('Failed to load documents');

      const data = await response.json();
      setDocuments(data.documents);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/knowledge-base/search?query=${encodeURIComponent(searchQuery)}&limit=10`
      );

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setSearchResults(data.documents);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  };

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);

    try {
      const tags = createForm.tags
        .split(',')
        .map(t => t.trim())
        .filter(t => t);

      const response = await fetch('/api/v1/knowledge-base/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...createForm,
          tags
        })
      });

      if (!response.ok) throw new Error('Failed to create document');

      setCreateForm({
        title: '',
        content: '',
        doc_type: 'article',
        category: 'general',
        tags: ''
      });
      setActiveTab('documents');
      loadDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Delete this document?')) return;

    try {
      const response = await fetch(
        `/api/v1/knowledge-base/documents/${docId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) throw new Error('Failed to delete');

      setDocuments(documents.filter(d => d.doc_id !== docId));
      setSelectedDoc(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      faq: 'bg-blue-50 text-blue-700',
      article: 'bg-green-50 text-green-700',
      guide: 'bg-purple-50 text-purple-700',
      troubleshooting: 'bg-red-50 text-red-700',
      policy: 'bg-yellow-50 text-yellow-700',
      product: 'bg-indigo-50 text-indigo-700'
    };
    return colors[type] || 'bg-gray-50 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-500 mt-1">Search, create, and manage documentation</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'search'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Search className="w-4 h-4 inline mr-2" />
            Search
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'documents'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <BookOpen className="w-4 h-4 inline mr-2" />
            Documents
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'create'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Create
          </button>
        </div>

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-6">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search documentation, FAQs, guides..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={searching || !searchQuery.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {searching ? 'Searching...' : 'Search'}
                </button>
              </div>
            </form>

            {/* Search Results */}
            {searchResults.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                {searchQuery ? 'No results found' : 'Enter a search query'}
              </div>
            ) : (
              <div className="space-y-4">
                {searchResults.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => setSelectedDoc(doc)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-semibold text-gray-900">{doc.title}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTypeColor(doc.type)}`}>
                        {doc.type}
                      </span>
                    </div>
                    <p className="text-gray-600 line-clamp-2 mb-3">{doc.content}</p>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 text-gray-500">
                        <Folder className="w-4 h-4" />
                        {doc.category}
                      </div>
                      <div className="text-blue-600 font-medium">
                        {Math.round(doc.relevance_score * 100)}% match
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Document Detail Modal */}
            {selectedDoc && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
                  <div className="flex items-start justify-between mb-4">
                    <h2 className="text-2xl font-bold text-gray-900">{selectedDoc.title}</h2>
                    <button
                      onClick={() => setSelectedDoc(null)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="flex items-center gap-2 mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTypeColor(selectedDoc.type)}`}>
                      {selectedDoc.type}
                    </span>
                    <span className="text-sm text-gray-600">{selectedDoc.category}</span>
                    {selectedDoc.tags.length > 0 && (
                      <div className="flex items-center gap-1 ml-auto">
                        {selectedDoc.tags.map((tag) => (
                          <span key={tag} className="text-xs bg-gray-200 text-gray-800 px-2 py-1 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="prose prose-sm max-w-none">
                    {selectedDoc.content}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4 flex gap-4">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">All Types</option>
                {docTypes.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* Documents Grid */}
            {loading ? (
              <div className="text-center py-12">
                <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No documents found
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {documents.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <FileText className="w-6 h-6 text-blue-600" />
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${getTypeColor(doc.type)}`}>
                        {doc.type}
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                      {doc.title}
                    </h3>
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {doc.content}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{doc.category}</span>
                      <button
                        onClick={() => handleDeleteDocument(doc.doc_id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Create Tab */}
        {activeTab === 'create' && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Create Document</h2>

              <form onSubmit={handleCreateDocument} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={createForm.title}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      title: e.target.value
                    }))}
                    placeholder="Document title"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content *
                  </label>
                  <textarea
                    value={createForm.content}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      content: e.target.value
                    }))}
                    placeholder="Document content"
                    rows="8"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Type *
                    </label>
                    <select
                      value={createForm.doc_type}
                      onChange={(e) => setCreateForm(prev => ({
                        ...prev,
                        doc_type: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      {docTypes.map((type) => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Category *
                    </label>
                    <select
                      value={createForm.category}
                      onChange={(e) => setCreateForm(prev => ({
                        ...prev,
                        category: e.target.value
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      {categories.map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={createForm.tags}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      tags: e.target.value
                    }))}
                    placeholder="e.g., urgent, common, faq"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <button
                  type="submit"
                  disabled={creating || !createForm.title || !createForm.content}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {creating ? 'Creating...' : 'Create Document'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeBase;
