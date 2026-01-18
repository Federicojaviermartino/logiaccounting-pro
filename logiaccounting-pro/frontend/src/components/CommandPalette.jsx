import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { COMMAND_ITEMS } from '../data/shortcuts';

export default function CommandPalette({ isOpen, onClose, onShowShortcuts }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const { setTheme } = useTheme();

  const filteredItems = COMMAND_ITEMS.filter(item =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  const groupedItems = filteredItems.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredItems.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      executeItem(filteredItems[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  const executeItem = (item) => {
    if (!item) return;

    if (item.path) {
      navigate(item.path);
    } else if (item.action === 'theme') {
      setTheme(item.value);
    } else if (item.action === 'showShortcuts') {
      onShowShortcuts?.();
    } else if (item.action === 'create') {
      navigate(`/${item.entity}s?action=new`);
    }

    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-overlay" onClick={onClose}>
      <div className="command-palette" onClick={e => e.stopPropagation()}>
        <div className="command-input-wrapper">
          <span className="command-icon">🔍</span>
          <input
            ref={inputRef}
            type="text"
            className="command-input"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="command-kbd">ESC</kbd>
        </div>

        <div className="command-results">
          {Object.entries(groupedItems).map(([category, items]) => (
            <div key={category} className="command-group">
              <div className="command-group-title">{category}</div>
              {items.map((item) => {
                const globalIndex = filteredItems.indexOf(item);
                return (
                  <div
                    key={item.id}
                    className={`command-item ${globalIndex === selectedIndex ? 'selected' : ''}`}
                    onClick={() => executeItem(item)}
                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                  >
                    <span className="command-item-icon">{item.icon}</span>
                    <span className="command-item-label">{item.label}</span>
                  </div>
                );
              })}
            </div>
          ))}
          {filteredItems.length === 0 && (
            <div className="command-empty">No results found</div>
          )}
        </div>
      </div>
    </div>
  );
}
