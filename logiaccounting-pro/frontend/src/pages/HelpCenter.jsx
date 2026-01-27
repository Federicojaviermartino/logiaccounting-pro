import { useState } from 'react';
import { HELP_CATEGORIES } from '../data/helpContent';

export default function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);

  const filteredCategories = HELP_CATEGORIES.map(cat => ({
    ...cat,
    articles: cat.articles.filter(
      art => art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
             art.content.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => cat.articles.length > 0 || searchQuery === '');

  const renderMarkdown = (content) => {
    return content
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/\n/g, '<br>');
  };

  return (
    <>
      <div className="section mb-6">
        <div className="help-search">
          <span className="search-icon">O</span>
          <input
            type="text"
            className="form-input help-search-input"
            placeholder="Search help articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {(selectedCategory || selectedArticle) && (
        <div className="breadcrumb mb-4">
          <button onClick={() => { setSelectedCategory(null); setSelectedArticle(null); }}>
            Help Center
          </button>
          {selectedCategory && (
            <>
              <span>/</span>
              <button onClick={() => setSelectedArticle(null)}>{selectedCategory.title}</button>
            </>
          )}
          {selectedArticle && (
            <>
              <span>/</span>
              <span>{selectedArticle.title}</span>
            </>
          )}
        </div>
      )}

      {selectedArticle ? (
        <div className="section">
          <article
            className="help-article"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedArticle.content) }}
          />
        </div>
      ) : selectedCategory ? (
        <div className="section">
          <h3 className="section-title">{selectedCategory.icon} {selectedCategory.title}</h3>
          <div className="articles-list">
            {selectedCategory.articles.map(article => (
              <div
                key={article.id}
                className="article-card"
                onClick={() => setSelectedArticle(article)}
              >
                <h4>{article.title}</h4>
                <p>{article.content.substring(0, 100)}...</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="help-categories mb-6">
            {filteredCategories.map(category => (
              <div
                key={category.id}
                className="help-category-card"
                onClick={() => setSelectedCategory(category)}
              >
                <span className="category-icon">{category.icon}</span>
                <h4>{category.title}</h4>
                <p>{category.articles.length} articles</p>
              </div>
            ))}
          </div>

          <div className="section">
            <h3 className="section-title">Contact Support</h3>
            <div className="support-options">
              <div className="support-option">
                <span>@</span>
                <div>
                  <h4>Email</h4>
                  <p>support@logiaccounting.com</p>
                </div>
              </div>
              <div className="support-option">
                <span>Chat</span>
                <div>
                  <h4>Live Chat</h4>
                  <p>9am - 6pm EST</p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
