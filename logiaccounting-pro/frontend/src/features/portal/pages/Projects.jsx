/**
 * Projects - Project visibility and tracking
 */

import React, { useState, useEffect } from 'react';
import {
  Folder, Calendar, CheckCircle, Clock, AlertCircle,
  FileText, ChevronRight, Users, Target, BarChart3,
  ArrowLeft, MessageSquare, Download, ThumbsUp, Star,
} from 'lucide-react';
import toast from '../../../utils/toast';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({});
  const [filter, setFilter] = useState('all');
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackRating, setFeedbackRating] = useState(0);

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API calls
      setStats({
        active: 2,
        completed: 5,
        pending_approval: 1,
        total: 8,
      });
      setProjects([
        {
          id: '1',
          name: 'Website Redesign',
          description: 'Complete redesign of company website with modern UI',
          status: 'in_progress',
          progress: 65,
          start_date: '2025-01-01',
          end_date: '2025-03-15',
          manager: 'Jane Smith',
          budget: 15000,
          spent: 9750,
          milestones: [
            { id: 'm1', name: 'Discovery & Planning', status: 'completed', due_date: '2025-01-15' },
            { id: 'm2', name: 'Design Phase', status: 'completed', due_date: '2025-02-01' },
            { id: 'm3', name: 'Development', status: 'in_progress', due_date: '2025-02-28' },
            { id: 'm4', name: 'Testing & Launch', status: 'pending', due_date: '2025-03-15' },
          ],
          deliverables: [
            { id: 'd1', name: 'Wireframes', status: 'approved', submitted_date: '2025-01-20' },
            { id: 'd2', name: 'Design Mockups', status: 'pending_approval', submitted_date: '2025-02-05' },
          ],
          documents: [
            { id: 'doc1', name: 'Project Proposal.pdf', type: 'pdf', size: '2.4 MB' },
            { id: 'doc2', name: 'Design Guidelines.pdf', type: 'pdf', size: '1.8 MB' },
          ],
        },
        {
          id: '2',
          name: 'Mobile App Development',
          description: 'Native mobile application for iOS and Android',
          status: 'planning',
          progress: 15,
          start_date: '2025-02-01',
          end_date: '2025-06-30',
          manager: 'John Doe',
          budget: 45000,
          spent: 6750,
          milestones: [
            { id: 'm1', name: 'Requirements Gathering', status: 'in_progress', due_date: '2025-02-15' },
            { id: 'm2', name: 'UI/UX Design', status: 'pending', due_date: '2025-03-15' },
            { id: 'm3', name: 'iOS Development', status: 'pending', due_date: '2025-05-01' },
            { id: 'm4', name: 'Android Development', status: 'pending', due_date: '2025-05-15' },
            { id: 'm5', name: 'Testing & Launch', status: 'pending', due_date: '2025-06-30' },
          ],
          deliverables: [],
          documents: [
            { id: 'doc1', name: 'App Specifications.pdf', type: 'pdf', size: '3.1 MB' },
          ],
        },
        {
          id: '3',
          name: 'SEO Optimization',
          description: 'Comprehensive SEO audit and optimization',
          status: 'completed',
          progress: 100,
          start_date: '2024-11-01',
          end_date: '2024-12-31',
          manager: 'Sarah Johnson',
          budget: 5000,
          spent: 4800,
          milestones: [
            { id: 'm1', name: 'Audit', status: 'completed', due_date: '2024-11-15' },
            { id: 'm2', name: 'Implementation', status: 'completed', due_date: '2024-12-15' },
            { id: 'm3', name: 'Reporting', status: 'completed', due_date: '2024-12-31' },
          ],
          deliverables: [
            { id: 'd1', name: 'SEO Audit Report', status: 'approved', submitted_date: '2024-11-15' },
            { id: 'd2', name: 'Final Results Report', status: 'approved', submitted_date: '2024-12-31' },
          ],
          documents: [
            { id: 'doc1', name: 'SEO Strategy.pdf', type: 'pdf', size: '1.2 MB' },
            { id: 'doc2', name: 'Results Report.pdf', type: 'pdf', size: '2.8 MB' },
          ],
        },
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveDeliverable = async (deliverableId, approved) => {
    if (!selectedProject) return;
    try {
      const updatedDeliverables = selectedProject.deliverables.map(d =>
        d.id === deliverableId ? { ...d, status: approved ? 'approved' : 'rejected' } : d
      );
      setSelectedProject({ ...selectedProject, deliverables: updatedDeliverables });
    } catch (error) {
      console.error('Failed to approve deliverable:', error);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim()) return;
    try {
      // API call would go here
      setFeedbackText('');
      setFeedbackRating(0);
      toast.success('Feedback submitted successfully!');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const getStatusInfo = (status) => {
    const info = {
      planning: { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Planning' },
      in_progress: { icon: AlertCircle, color: 'text-blue-600', bg: 'bg-blue-100', label: 'In Progress' },
      on_hold: { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'On Hold' },
      completed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Completed' },
    };
    return info[status] || info.planning;
  };

  const filteredProjects = filter === 'all'
    ? projects
    : projects.filter(p => p.status === filter);

  if (selectedProject) {
    const statusInfo = getStatusInfo(selectedProject.status);
    const StatusIcon = statusInfo.icon;

    return (
      <div className="project-detail">
        <button className="back-btn" onClick={() => setSelectedProject(null)}>
          <ArrowLeft className="w-4 h-4" />
          Back to Projects
        </button>

        <div className="project-header">
          <div className="project-title">
            <h1>{selectedProject.name}</h1>
            <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
              <StatusIcon className="w-4 h-4" />
              {statusInfo.label}
            </span>
          </div>
          <p>{selectedProject.description}</p>
          <div className="project-meta">
            <span><Calendar className="w-4 h-4" /> {new Date(selectedProject.start_date).toLocaleDateString()} - {new Date(selectedProject.end_date).toLocaleDateString()}</span>
            <span><Users className="w-4 h-4" /> {selectedProject.manager}</span>
          </div>
        </div>

        <div className="progress-section">
          <div className="progress-header">
            <span>Overall Progress</span>
            <span>{selectedProject.progress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${selectedProject.progress}%` }} />
          </div>
          <div className="budget-info">
            <span>Budget: ${selectedProject.spent.toLocaleString()} / ${selectedProject.budget.toLocaleString()}</span>
          </div>
        </div>

        <div className="detail-tabs">
          {['overview', 'milestones', 'deliverables', 'documents', 'feedback'].map((tab) => (
            <button
              key={tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && (
            <div className="overview-grid">
              <div className="overview-card">
                <h3><Target className="w-5 h-5" /> Key Milestones</h3>
                {selectedProject.milestones.slice(0, 3).map((milestone) => (
                  <div key={milestone.id} className="milestone-item">
                    <span className={`milestone-status ${milestone.status}`} />
                    <span>{milestone.name}</span>
                    <span className="milestone-date">{new Date(milestone.due_date).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
              <div className="overview-card">
                <h3><BarChart3 className="w-5 h-5" /> Project Stats</h3>
                <div className="stat-row">
                  <span>Milestones Completed</span>
                  <span>{selectedProject.milestones.filter(m => m.status === 'completed').length} / {selectedProject.milestones.length}</span>
                </div>
                <div className="stat-row">
                  <span>Deliverables Approved</span>
                  <span>{selectedProject.deliverables.filter(d => d.status === 'approved').length} / {selectedProject.deliverables.length}</span>
                </div>
                <div className="stat-row">
                  <span>Budget Used</span>
                  <span>{Math.round((selectedProject.spent / selectedProject.budget) * 100)}%</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'milestones' && (
            <div className="milestones-list">
              {selectedProject.milestones.map((milestone, index) => (
                <div key={milestone.id} className="milestone-card">
                  <div className="milestone-number">{index + 1}</div>
                  <div className="milestone-info">
                    <h4>{milestone.name}</h4>
                    <span className="due-date">Due: {new Date(milestone.due_date).toLocaleDateString()}</span>
                  </div>
                  <span className={`status-pill ${milestone.status}`}>
                    {milestone.status === 'completed' && <CheckCircle className="w-4 h-4" />}
                    {milestone.status === 'in_progress' && <Clock className="w-4 h-4" />}
                    {milestone.status === 'pending' && <AlertCircle className="w-4 h-4" />}
                    {milestone.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'deliverables' && (
            <div className="deliverables-list">
              {selectedProject.deliverables.length === 0 ? (
                <div className="empty-state">
                  <FileText className="w-10 h-10" />
                  <p>No deliverables yet</p>
                </div>
              ) : (
                selectedProject.deliverables.map((deliverable) => (
                  <div key={deliverable.id} className="deliverable-card">
                    <div className="deliverable-info">
                      <h4>{deliverable.name}</h4>
                      <span className="submitted-date">Submitted: {new Date(deliverable.submitted_date).toLocaleDateString()}</span>
                    </div>
                    {deliverable.status === 'pending_approval' ? (
                      <div className="approval-actions">
                        <button className="btn-approve" onClick={() => handleApproveDeliverable(deliverable.id, true)}>
                          <ThumbsUp className="w-4 h-4" />
                          Approve
                        </button>
                        <button className="btn-reject" onClick={() => handleApproveDeliverable(deliverable.id, false)}>
                          Request Changes
                        </button>
                      </div>
                    ) : (
                      <span className={`status-pill ${deliverable.status}`}>
                        {deliverable.status === 'approved' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        {deliverable.status.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="documents-list">
              {selectedProject.documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <FileText className="w-5 h-5" />
                  <div className="document-info">
                    <span className="document-name">{doc.name}</span>
                    <span className="document-size">{doc.size}</span>
                  </div>
                  <button className="btn-download">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'feedback' && (
            <div className="feedback-section">
              <h3>Share Your Feedback</h3>
              <p>Help us improve by sharing your thoughts on this project.</p>
              <div className="rating-row">
                <span>Rating:</span>
                <div className="stars">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      className={`star-btn ${star <= feedbackRating ? 'active' : ''}`}
                      onClick={() => setFeedbackRating(star)}
                    >
                      <Star className="w-6 h-6" fill={star <= feedbackRating ? '#f59e0b' : 'none'} />
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                placeholder="Your feedback..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={4}
              />
              <button className="btn-submit" onClick={handleSubmitFeedback}>
                <MessageSquare className="w-4 h-4" />
                Submit Feedback
              </button>
            </div>
          )}
        </div>

        <style jsx>{`
          .project-detail {
            max-width: 900px;
            margin: 0 auto;
          }

          .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #64748b;
            margin-bottom: 20px;
            background: none;
            border: none;
            cursor: pointer;
          }

          .project-header {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
          }

          .project-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
          }

          .project-title h1 {
            font-size: 24px;
            margin: 0;
          }

          .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
          }

          .project-header p {
            color: #64748b;
            margin: 0 0 16px;
          }

          .project-meta {
            display: flex;
            gap: 24px;
            font-size: 14px;
            color: #64748b;
          }

          .project-meta span {
            display: flex;
            align-items: center;
            gap: 6px;
          }

          .progress-section {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
          }

          .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: 500;
          }

          .progress-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
          }

          .progress-fill {
            height: 100%;
            background: #3b82f6;
            border-radius: 4px;
            transition: width 0.3s;
          }

          .budget-info {
            margin-top: 12px;
            font-size: 14px;
            color: #64748b;
          }

          .detail-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            overflow-x: auto;
          }

          .tab {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            background: #f8fafc;
            border: none;
            color: #64748b;
            cursor: pointer;
            white-space: nowrap;
          }

          .tab.active {
            background: #3b82f6;
            color: white;
          }

          .tab-content {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
          }

          .overview-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
          }

          @media (max-width: 640px) {
            .overview-grid {
              grid-template-columns: 1fr;
            }
          }

          .overview-card {
            background: #f8fafc;
            border-radius: 10px;
            padding: 16px;
          }

          .overview-card h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0 0 16px;
            font-size: 15px;
          }

          .milestone-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            font-size: 14px;
          }

          .milestone-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
          }

          .milestone-status.completed { background: #10b981; }
          .milestone-status.in_progress { background: #3b82f6; }
          .milestone-status.pending { background: #d1d5db; }

          .milestone-date {
            margin-left: auto;
            color: #64748b;
            font-size: 13px;
          }

          .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            font-size: 14px;
            border-bottom: 1px solid #e2e8f0;
          }

          .stat-row:last-child {
            border-bottom: none;
          }

          .milestones-list, .deliverables-list, .documents-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
          }

          .milestone-card {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            background: #f8fafc;
            border-radius: 10px;
          }

          .milestone-number {
            width: 32px;
            height: 32px;
            background: #e2e8f0;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
          }

          .milestone-info {
            flex: 1;
          }

          .milestone-info h4 {
            margin: 0 0 4px;
          }

          .due-date {
            font-size: 13px;
            color: #64748b;
          }

          .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
          }

          .status-pill.completed { background: #dcfce7; color: #16a34a; }
          .status-pill.in_progress { background: #dbeafe; color: #2563eb; }
          .status-pill.pending { background: #f1f5f9; color: #64748b; }
          .status-pill.approved { background: #dcfce7; color: #16a34a; }
          .status-pill.pending_approval { background: #fef3c7; color: #d97706; }
          .status-pill.rejected { background: #fee2e2; color: #dc2626; }

          .deliverable-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            background: #f8fafc;
            border-radius: 10px;
          }

          .deliverable-info h4 {
            margin: 0 0 4px;
          }

          .submitted-date {
            font-size: 13px;
            color: #64748b;
          }

          .approval-actions {
            display: flex;
            gap: 8px;
          }

          .btn-approve {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #10b981;
            color: white;
            border-radius: 8px;
            font-size: 13px;
            border: none;
            cursor: pointer;
          }

          .btn-reject {
            padding: 8px 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 13px;
            background: white;
            cursor: pointer;
          }

          .document-card {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px;
            background: #f8fafc;
            border-radius: 10px;
          }

          .document-info {
            flex: 1;
          }

          .document-name {
            font-weight: 500;
            display: block;
          }

          .document-size {
            font-size: 13px;
            color: #64748b;
          }

          .btn-download {
            width: 36px;
            height: 36px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            cursor: pointer;
          }

          .empty-state {
            text-align: center;
            padding: 40px;
            color: #64748b;
          }

          .empty-state svg {
            margin: 0 auto 12px;
            color: #cbd5e1;
          }

          .feedback-section h3 {
            margin: 0 0 8px;
          }

          .feedback-section > p {
            color: #64748b;
            margin: 0 0 20px;
          }

          .rating-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
          }

          .stars {
            display: flex;
            gap: 4px;
          }

          .star-btn {
            color: #d1d5db;
            background: none;
            border: none;
            cursor: pointer;
          }

          .star-btn.active {
            color: #f59e0b;
          }

          .feedback-section textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-bottom: 16px;
            resize: none;
            font-size: 15px;
          }

          .btn-submit {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: #3b82f6;
            color: white;
            border-radius: 8px;
            font-weight: 500;
            border: none;
            cursor: pointer;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="projects-page">
      <div className="page-header">
        <div>
          <h1>My Projects</h1>
          <p>Track progress of your projects</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon active">
            <Folder className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.active}</span>
            <span className="stat-label">Active</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon completed">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.completed}</span>
            <span className="stat-label">Completed</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon pending">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.pending_approval}</span>
            <span className="stat-label">Pending Approval</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon total">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Total Projects</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <div className="filter-tabs">
          {['all', 'in_progress', 'planning', 'completed'].map((status) => (
            <button
              key={status}
              className={`filter-tab ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Projects List */}
      <div className="projects-list">
        {isLoading ? (
          <div className="loading">Loading projects...</div>
        ) : filteredProjects.length === 0 ? (
          <div className="empty-state">
            <Folder className="w-12 h-12" />
            <p>No projects found</p>
          </div>
        ) : (
          filteredProjects.map((project) => {
            const statusInfo = getStatusInfo(project.status);
            const StatusIcon = statusInfo.icon;
            return (
              <button
                key={project.id}
                className="project-card"
                onClick={() => setSelectedProject(project)}
              >
                <div className="project-main">
                  <div className="project-icon">
                    <Folder className="w-5 h-5" />
                  </div>
                  <div className="project-details">
                    <div className="project-header-row">
                      <h3>{project.name}</h3>
                      <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        {statusInfo.label}
                      </span>
                    </div>
                    <p>{project.description}</p>
                    <div className="project-progress">
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${project.progress}%` }} />
                      </div>
                      <span>{project.progress}%</span>
                    </div>
                    <div className="project-meta">
                      <span><Calendar className="w-3 h-3" /> Due: {new Date(project.end_date).toLocaleDateString()}</span>
                      <span><Users className="w-3 h-3" /> {project.manager}</span>
                    </div>
                  </div>
                </div>
                <ChevronRight className="chevron" />
              </button>
            );
          })
        )}
      </div>

      <style jsx>{`
        .projects-page {
          max-width: 1000px;
          margin: 0 auto;
        }

        .page-header {
          margin-bottom: 24px;
        }

        .page-header h1 {
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 4px;
        }

        .page-header p {
          color: #64748b;
          margin: 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        @media (max-width: 768px) {
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .stat-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon.active {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .stat-icon.completed {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .stat-icon.pending {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .stat-icon.total {
          background: rgba(139, 92, 246, 0.1);
          color: #8b5cf6;
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
        }

        .stat-label {
          font-size: 13px;
          color: #64748b;
        }

        .filters-row {
          margin-bottom: 20px;
        }

        .filter-tabs {
          display: flex;
          gap: 8px;
          background: #f8fafc;
          padding: 4px;
          border-radius: 10px;
          width: fit-content;
        }

        .filter-tab {
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          background: transparent;
          border: none;
          color: #64748b;
          cursor: pointer;
          text-transform: capitalize;
        }

        .filter-tab.active {
          background: #ffffff;
          color: #1e293b;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .projects-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .project-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          cursor: pointer;
          width: 100%;
          text-align: left;
        }

        .project-card:hover {
          border-color: #3b82f6;
        }

        .project-main {
          display: flex;
          gap: 16px;
          flex: 1;
        }

        .project-icon {
          width: 44px;
          height: 44px;
          background: #f1f5f9;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          flex-shrink: 0;
        }

        .project-details {
          flex: 1;
        }

        .project-header-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 4px;
        }

        .project-header-row h3 {
          margin: 0;
          font-size: 16px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .project-card p {
          margin: 0 0 12px;
          color: #64748b;
          font-size: 14px;
        }

        .project-progress {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .progress-bar {
          flex: 1;
          height: 6px;
          background: #e2e8f0;
          border-radius: 3px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #3b82f6;
          border-radius: 3px;
        }

        .project-meta {
          display: flex;
          gap: 16px;
          font-size: 13px;
          color: #94a3b8;
        }

        .project-meta span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .chevron {
          color: #cbd5e1;
          flex-shrink: 0;
        }

        .empty-state, .loading {
          text-align: center;
          padding: 48px;
          color: #64748b;
        }

        .empty-state svg {
          margin: 0 auto 12px;
          color: #cbd5e1;
        }
      `}</style>
    </div>
  );
}
