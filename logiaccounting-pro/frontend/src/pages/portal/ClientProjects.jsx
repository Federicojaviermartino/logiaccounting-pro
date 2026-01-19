import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function ClientProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/projects');
      setProjects(res.data.projects || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = { active: 'success', completed: 'info', on_hold: 'warning', cancelled: 'danger' };
    return colors[status] || 'gray';
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Projects</h2>

      {projects.length === 0 ? (
        <div className="section text-center text-muted">No projects found</div>
      ) : (
        <div className="portal-projects-grid">
          {projects.map(project => (
            <div key={project.id} className="portal-project-card">
              <div className="portal-project-header">
                <h4>{project.name}</h4>
                <span className={`badge badge-${getStatusColor(project.status)}`}>
                  {project.status}
                </span>
              </div>
              <p className="portal-project-desc">{project.description?.substring(0, 100) || 'No description'}</p>

              <div className="portal-project-progress">
                <div className="progress-label">
                  <span>Progress</span>
                  <span>{project.progress || 0}%</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${project.progress || 0}%` }} />
                </div>
              </div>

              <div className="portal-project-dates">
                <span>{project.start_date || 'TBD'}</span>
                <span>to</span>
                <span>{project.end_date || 'TBD'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
