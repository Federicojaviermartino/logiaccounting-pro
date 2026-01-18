import { SHORTCUTS } from '../data/shortcuts';

export default function ShortcutsHelp({ isOpen, onClose }) {
  if (!isOpen) return null;

  const renderKey = (key) => {
    const symbols = { ctrl: '⌘/Ctrl', shift: '⇧', alt: '⌥/Alt', escape: 'Esc' };
    return symbols[key] || key.toUpperCase();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>⌨️ Keyboard Shortcuts</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="shortcuts-grid">
            {Object.entries(SHORTCUTS).map(([section, shortcuts]) => (
              <div key={section} className="shortcuts-section">
                <h4>{section.charAt(0).toUpperCase() + section.slice(1)}</h4>
                {shortcuts.map((s, i) => (
                  <div key={i} className="shortcut-item">
                    <span className="shortcut-label">{s.label}</span>
                    <span className="shortcut-keys">
                      {s.keys.map((k, j) => (
                        <span key={j}>
                          <kbd>{renderKey(k)}</kbd>
                          {j < s.keys.length - 1 && (s.keys[0] === 'g' ? ' then ' : ' + ')}
                        </span>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
