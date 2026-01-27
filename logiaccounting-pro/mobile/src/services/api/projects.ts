/**
 * Projects API Service
 */

import apiClient from './client';

export interface Project {
  id: string;
  code: string;
  name: string;
  clientId: string;
  clientName: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  startDate: string;
  endDate?: string;
  budget: number;
  spent: number;
  description?: string;
}

export interface ProjectFilters {
  status?: Project['status'];
  clientId?: string;
}

export const projectsApi = {
  getProjects: (filters?: ProjectFilters) =>
    apiClient.get<Project[]>('/projects', { params: filters }),

  getProject: (id: string) =>
    apiClient.get<Project>(`/projects/${id}`),

  createProject: (data: Omit<Project, 'id' | 'spent'>) =>
    apiClient.post<Project>('/projects', data),

  updateProject: (id: string, data: Partial<Project>) =>
    apiClient.put<Project>(`/projects/${id}`, data),

  deleteProject: (id: string) => apiClient.delete(`/projects/${id}`),

  // Project financials
  getProjectFinancials: (id: string) =>
    apiClient.get<{
      budget: number;
      spent: number;
      remaining: number;
      transactions: any[];
    }>(`/projects/${id}/financials`),

  // Project materials
  getProjectMaterials: (id: string) =>
    apiClient.get<any[]>(`/projects/${id}/materials`),
};

export default projectsApi;
