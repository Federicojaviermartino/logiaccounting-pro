import React, { useState, useEffect } from 'react';
import { History, GitCommit, GitCompare, RotateCcw, ChevronDown, ChevronUp, Check, X } from 'lucide-react';
import { workflowAPI } from '../../../services/api';

export default function VersionHistory({ workflowId, onRollback }) {
  const [versions, setVersions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [rollbackConfirm, setRollbackConfirm] = useState(null);

  useEffect(() => { workflowId && loadVersions(); }, [workflowId]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const res = await workflowAPI.listVersions(workflowId);
      setVersions(res.data || []);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  const handleSelect = (v) => {
    if (selectedVersions.includes(v)) setSelectedVersions(selectedVersions.filter(x => x !== v));
    else if (selectedVersions.length < 2) setSelectedVersions([...selectedVersions, v]);
    else setSelectedVersions([selectedVersions[1], v]);
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;
    const res = await workflowAPI.compareVersions(workflowId, Math.min(...selectedVersions), Math.max(...selectedVersions));
    setComparison(res.data);
  };

  const handleRollback = async (version) => {
    await workflowAPI.rollbackVersion(workflowId, version);
    setRollbackConfirm(null);
    loadVersions();
    onRollback?.();
  };

  return (
    <div className="version-history">
      <div className="header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="left"><History size={16} /><span>Version History</span><span className="count">{versions.length}</span></div>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {isExpanded && (
        <div className="content">
          {selectedVersions.length === 2 && <button className="compare-btn" onClick={handleCompare}><GitCompare size={16} /> Compare</button>}
          <div className="list">
            {versions.map(v => (
              <div key={v.id} className={`item ${selectedVersions.includes(v.version) ? 'selected' : ''}`}>
                <div className="check" onClick={() => handleSelect(v.version)}>{selectedVersions.includes(v.version) ? <Check size={14} /> : <div className="empty" />}</div>
                <div className="info"><GitCommit size={14} /><span className="num">v{v.version}</span>{v.comment && <span className="comment">{v.comment}</span>}</div>
                <button className="rollback" onClick={() => setRollbackConfirm(v.version)}><RotateCcw size={14} /></button>
              </div>
            ))}
          </div>
          {comparison && (
            <div className="comparison">
              <h4>v{comparison.version_a} → v{comparison.version_b}</h4>
              <div className="stats"><span className="add">+{comparison.nodes_added}</span><span className="rem">-{comparison.nodes_removed}</span><span className="mod">~{comparison.nodes_modified}</span></div>
              <button onClick={() => setComparison(null)}><X size={14} /></button>
            </div>
          )}
          {rollbackConfirm && (
            <div className="confirm">
              <p>Rollback to v{rollbackConfirm}?</p>
              <div className="actions"><button onClick={() => setRollbackConfirm(null)}>Cancel</button><button className="primary" onClick={() => handleRollback(rollbackConfirm)}>Rollback</button></div>
            </div>
          )}
        </div>
      )}
      <style jsx>{`
        .version-history { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; }
        .header { display: flex; justify-content: space-between; padding: 12px 16px; cursor: pointer; }
        .header:hover { background: var(--bg-secondary); }
        .left { display: flex; align-items: center; gap: 8px; font-weight: 500; }
        .count { font-size: 12px; color: var(--text-muted); }
        .content { border-top: 1px solid var(--border-color); padding: 12px; }
        .compare-btn { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: var(--primary); color: white; border-radius: 6px; margin-bottom: 12px; }
        .list { display: flex; flex-direction: column; gap: 8px; max-height: 250px; overflow-y: auto; }
        .item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: var(--bg-secondary); border-radius: 6px; border: 2px solid transparent; }
        .item.selected { border-color: var(--primary); }
        .check { cursor: pointer; color: var(--primary); }
        .empty { width: 14px; height: 14px; border: 2px solid var(--border-color); border-radius: 3px; }
        .info { flex: 1; display: flex; align-items: center; gap: 8px; }
        .num { font-weight: 600; }
        .comment { color: var(--text-muted); font-size: 13px; }
        .rollback { padding: 6px; border-radius: 4px; }
        .rollback:hover { background: var(--bg-primary); color: var(--primary); }
        .comparison { margin-top: 16px; padding: 12px; background: var(--bg-secondary); border-radius: 8px; display: flex; align-items: center; gap: 12px; }
        .comparison h4 { margin: 0; font-size: 14px; }
        .stats { display: flex; gap: 12px; font-size: 13px; }
        .add { color: #10b981; }
        .rem { color: #ef4444; }
        .mod { color: #f59e0b; }
        .confirm { margin-top: 16px; padding: 16px; background: rgba(245,158,11,0.1); border-radius: 8px; text-align: center; }
        .actions { display: flex; justify-content: center; gap: 12px; margin-top: 12px; }
        .actions button { padding: 8px 16px; border-radius: 6px; }
        .actions .primary { background: #f59e0b; color: white; }
      `}</style>
    </div>
  );
}
