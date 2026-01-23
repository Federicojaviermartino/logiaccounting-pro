/**
 * Knowledge Base - Self-service help articles
 */

import React, { useState, useEffect } from 'react';
import {
  Search, Book, ChevronRight, ThumbsUp, ThumbsDown,
  Eye, Rocket, CreditCard, User, Folder, Wrench, ArrowLeft,
} from 'lucide-react';

const categoryIcons = {
  'getting-started': Rocket,
  'billing': CreditCard,
  'account': User,
  'projects': Folder,
  'troubleshooting': Wrench,
};

export default function KnowledgeBase() {
  const [categories, setCategories] = useState([]);
  const [articles, setArticles] = useState([]);
  const [popularArticles, setPopularArticles] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [selectedCategory]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API calls
      setCategories([
        { id: 'getting-started', name: 'Getting Started', slug: 'getting-started', description: 'Learn the basics', article_count: 5 },
        { id: 'billing', name: 'Billing & Payments', slug: 'billing', description: 'Payment questions', article_count: 8 },
        { id: 'account', name: 'Account Management', slug: 'account', description: 'Manage your account', article_count: 6 },
        { id: 'projects', name: 'Projects', slug: 'projects', description: 'Working with projects', article_count: 4 },
        { id: 'troubleshooting', name: 'Troubleshooting', slug: 'troubleshooting', description: 'Common issues', article_count: 7 },
      ]);
      setArticles([
        { id: '1', title: 'Welcome to Customer Portal', slug: 'welcome', excerpt: 'Your portal hub for projects, payments, and support.', category_name: 'Getting Started', view_count: 150 },
        { id: '2', title: 'How to Pay an Invoice', slug: 'pay-invoice', excerpt: 'Learn how to pay your invoices online.', category_name: 'Billing', view_count: 120 },
        { id: '3', title: 'Updating Your Profile', slug: 'update-profile', excerpt: 'Update your name, email, and password.', category_name: 'Account', view_count: 80 },
      ]);
      setPopularArticles([
        { id: '1', title: 'How to Pay an Invoice', slug: 'pay-invoice' },
        { id: '2', title: 'Tracking Project Progress', slug: 'project-progress' },
        { id: '3', title: 'Login Troubleshooting', slug: 'login-issues' },
      ]);
    } catch (error) {
      console.error('Failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    // Simulated search - replace with API call
    setSearchResults(articles.filter(a =>
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.excerpt.toLowerCase().includes(searchQuery.toLowerCase())
    ));
  };

  const loadArticle = async (slug) => {
    // Simulated article load - replace with API call
    setSelectedArticle({
      id: '1',
      title: 'Welcome to Customer Portal',
      slug: slug,
      content: `# Welcome to Your Customer Portal

Your customer portal is your one-stop destination for managing your relationship with us.

## What You Can Do

- **View Projects** - Track the progress of your active projects
- **Pay Invoices** - View and pay your invoices online
- **Get Support** - Create and manage support tickets
- **View Documents** - Access shared documents and files

## Getting Started

1. Navigate using the sidebar menu
2. Click on any section to explore
3. Use the search bar to find specific information

If you need any help, don't hesitate to create a support ticket!`,
      category_name: 'Getting Started',
      view_count: 150,
      helpful_yes: 45,
      helpful_no: 5,
    });
  };

  const handleVote = async (articleId, helpful) => {
    if (selectedArticle?.id === articleId) {
      setSelectedArticle({
        ...selectedArticle,
        helpful_yes: selectedArticle.helpful_yes + (helpful ? 1 : 0),
        helpful_no: selectedArticle.helpful_no + (helpful ? 0 : 1),
      });
    }
  };

  if (selectedArticle) {
    return (
      <div className="kb-article">
        <button className="back-btn" onClick={() => setSelectedArticle(null)}>
          <ArrowLeft className="w-4 h-4" />
          Back to Knowledge Base
        </button>
        <article className="article-content">
          <span className="category-badge">{selectedArticle.category_name}</span>
          <h1>{selectedArticle.title}</h1>
          <div className="meta">
            <Eye className="w-4 h-4" />
            {selectedArticle.view_count} views
          </div>
          <div className="content" dangerouslySetInnerHTML={{
            __html: selectedArticle.content
              .replace(/^# (.*$)/gm, '<h1>$1</h1>')
              .replace(/^## (.*$)/gm, '<h2>$1</h2>')
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/- (.*$)/gm, '<li>$1</li>')
              .replace(/\d\. (.*$)/gm, '<li>$1</li>')
              .replace(/\n\n/g, '</p><p>')
          }} />
          <div className="helpful">
            <span>Was this helpful?</span>
            <button onClick={() => handleVote(selectedArticle.id, true)}>
              <ThumbsUp className="w-4 h-4" />
              Yes ({selectedArticle.helpful_yes})
            </button>
            <button onClick={() => handleVote(selectedArticle.id, false)}>
              <ThumbsDown className="w-4 h-4" />
              No ({selectedArticle.helpful_no})
            </button>
          </div>
        </article>

        <style jsx>{`
          .kb-article {
            max-width: 800px;
            margin: 0 auto;
          }

          .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #64748b;
            margin-bottom: 24px;
            background: none;
            border: none;
            cursor: pointer;
          }

          .article-content {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 32px;
          }

          .category-badge {
            display: inline-block;
            padding: 4px 12px;
            background: #f1f5f9;
            border-radius: 20px;
            font-size: 13px;
            color: #64748b;
            margin-bottom: 16px;
          }

          .article-content h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 12px;
          }

          .meta {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #64748b;
            font-size: 14px;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e2e8f0;
          }

          .content {
            font-size: 16px;
            line-height: 1.7;
            color: #374151;
          }

          .content h1, .content h2 {
            margin: 24px 0 16px;
          }

          .content li {
            margin-left: 20px;
            margin-bottom: 8px;
          }

          .helpful {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid #e2e8f0;
          }

          .helpful span {
            color: #64748b;
          }

          .helpful button {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #ffffff;
            cursor: pointer;
          }

          .helpful button:hover {
            background: #f8fafc;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="knowledge-base">
      <div className="kb-header">
        <h1>Knowledge Base</h1>
        <p>Find answers to common questions</p>
        <div className="search-box">
          <Search className="w-5 h-5" />
          <input
            type="text"
            placeholder="Search articles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>Search</button>
        </div>
      </div>

      {searchResults ? (
        <div className="search-results">
          <div className="results-header">
            <h2>Search Results</h2>
            <button onClick={() => { setSearchResults(null); setSearchQuery(''); }}>Clear</button>
          </div>
          {searchResults.length > 0 ? (
            searchResults.map((article) => (
              <button key={article.id} className="article-card" onClick={() => loadArticle(article.slug)}>
                <h3>{article.title}</h3>
                <p>{article.excerpt}</p>
              </button>
            ))
          ) : (
            <p className="no-results">No articles found</p>
          )}
        </div>
      ) : (
        <>
          <div className="categories-grid">
            {categories.map((cat) => {
              const Icon = categoryIcons[cat.slug] || Book;
              return (
                <button
                  key={cat.id}
                  className={`category-card ${selectedCategory === cat.slug ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(selectedCategory === cat.slug ? '' : cat.slug)}
                >
                  <Icon className="w-8 h-8" />
                  <h3>{cat.name}</h3>
                  <p>{cat.description}</p>
                  <span className="count">{cat.article_count} articles</span>
                </button>
              );
            })}
          </div>

          <div className="content-grid">
            <div className="articles-section">
              <h2>{selectedCategory ? categories.find(c => c.slug === selectedCategory)?.name : 'All Articles'}</h2>
              <div className="article-list">
                {articles.map((article) => (
                  <button key={article.id} className="article-card" onClick={() => loadArticle(article.slug)}>
                    <h3>{article.title}</h3>
                    <p>{article.excerpt}</p>
                    <div className="article-meta">
                      <span>{article.category_name}</span>
                      <span><Eye className="w-3 h-3" /> {article.view_count}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <aside className="popular-section">
              <h3>Popular Articles</h3>
              {popularArticles.map((article) => (
                <button key={article.id} className="popular-item" onClick={() => loadArticle(article.slug)}>
                  <span>{article.title}</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ))}
            </aside>
          </div>
        </>
      )}

      <style jsx>{`
        .knowledge-base {
          max-width: 1200px;
          margin: 0 auto;
        }

        .kb-header {
          text-align: center;
          margin-bottom: 32px;
        }

        .kb-header h1 {
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px;
        }

        .kb-header p {
          color: #64748b;
          margin: 0 0 24px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 12px;
          max-width: 600px;
          margin: 0 auto;
          padding: 12px 20px;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
        }

        .search-box input {
          flex: 1;
          border: none;
          outline: none;
          font-size: 16px;
        }

        .search-box button {
          padding: 8px 20px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          border: none;
          cursor: pointer;
        }

        .categories-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .category-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
        }

        .category-card:hover {
          border-color: #3b82f6;
        }

        .category-card.active {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.05);
        }

        .category-card h3 {
          margin: 12px 0 8px;
          font-size: 16px;
        }

        .category-card p {
          margin: 0 0 12px;
          font-size: 13px;
          color: #64748b;
        }

        .category-card .count {
          font-size: 12px;
          color: #3b82f6;
        }

        .content-grid {
          display: grid;
          grid-template-columns: 1fr 300px;
          gap: 24px;
        }

        @media (max-width: 768px) {
          .content-grid {
            grid-template-columns: 1fr;
          }
        }

        .articles-section h2 {
          font-size: 18px;
          margin: 0 0 16px;
        }

        .article-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .article-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          padding: 16px;
          text-align: left;
          cursor: pointer;
          width: 100%;
        }

        .article-card:hover {
          border-color: #3b82f6;
        }

        .article-card h3 {
          margin: 0 0 8px;
          font-size: 16px;
        }

        .article-card p {
          margin: 0 0 12px;
          font-size: 14px;
          color: #64748b;
        }

        .article-meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #94a3b8;
        }

        .article-meta span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .popular-section {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          height: fit-content;
        }

        .popular-section h3 {
          margin: 0 0 16px;
          font-size: 16px;
        }

        .popular-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
          padding: 12px;
          border-radius: 8px;
          cursor: pointer;
          background: none;
          border: none;
          text-align: left;
        }

        .popular-item:hover {
          background: #f8fafc;
        }

        .search-results {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 24px;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .results-header h2 {
          margin: 0;
        }

        .results-header button {
          color: #3b82f6;
          background: none;
          border: none;
          cursor: pointer;
        }

        .no-results {
          text-align: center;
          color: #64748b;
          padding: 32px;
        }
      `}</style>
    </div>
  );
}
