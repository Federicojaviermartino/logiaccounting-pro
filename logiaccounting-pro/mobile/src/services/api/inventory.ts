/**
 * Inventory API Service
 */

import apiClient from './client';

export interface Material {
  id: string;
  reference: string;
  name: string;
  description?: string;
  category: string;
  location: string;
  currentStock: number;
  minStock: number;
  unitCost: number;
  state: 'active' | 'inactive' | 'depleted';
  updatedAt: string;
}

export interface Movement {
  id: string;
  materialId: string;
  projectId?: string;
  type: 'entry' | 'exit';
  quantity: number;
  date: string;
  notes?: string;
  createdBy: string;
}

export const inventoryApi = {
  // Materials
  getMaterials: () => apiClient.get<Material[]>('/materials'),

  getMaterial: (id: string) => apiClient.get<Material>(`/materials/${id}`),

  createMaterial: (data: Omit<Material, 'id' | 'updatedAt'>) =>
    apiClient.post<Material>('/materials', data),

  updateMaterial: (id: string, data: Partial<Material>) =>
    apiClient.put<Material>(`/materials/${id}`, data),

  deleteMaterial: (id: string) => apiClient.delete(`/materials/${id}`),

  // Movements
  getMovements: (materialId?: string) => {
    const url = materialId
      ? `/materials/${materialId}/movements`
      : '/materials/movements';
    return apiClient.get<Movement[]>(url);
  },

  createMovement: (data: Omit<Movement, 'id' | 'createdBy'>) =>
    apiClient.post<Movement>('/materials/movements', data),

  // Stock operations
  adjustStock: (materialId: string, quantity: number, reason: string) =>
    apiClient.post(`/materials/${materialId}/adjust`, { quantity, reason }),

  // Reports
  getLowStockMaterials: () =>
    apiClient.get<Material[]>('/materials/reports/low-stock'),

  getInventoryValue: () =>
    apiClient.get<{ totalValue: number; breakdown: any[] }>(
      '/materials/reports/value'
    ),
};

export default inventoryApi;
