/**
 * Inventory State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { inventoryApi } from '@services/api/inventory';

interface Material {
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

interface Movement {
  id: string;
  materialId: string;
  projectId?: string;
  type: 'entry' | 'exit';
  quantity: number;
  date: string;
  notes?: string;
  createdBy: string;
}

interface InventoryState {
  materials: Material[];
  movements: Movement[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  filters: {
    search: string;
    category: string | null;
    location: string | null;
    state: string | null;
  };
}

const initialState: InventoryState = {
  materials: [],
  movements: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {
    search: '',
    category: null,
    location: null,
    state: null,
  },
};

// Async thunks
export const fetchMaterials = createAsyncThunk(
  'inventory/fetchMaterials',
  async (_, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.getMaterials();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch materials');
    }
  }
);

export const fetchMovements = createAsyncThunk(
  'inventory/fetchMovements',
  async (materialId: string | undefined, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.getMovements(materialId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch movements');
    }
  }
);

export const createMovement = createAsyncThunk(
  'inventory/createMovement',
  async (movement: Omit<Movement, 'id' | 'createdBy'>, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.createMovement(movement);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create movement');
    }
  }
);

// Slice
const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setMaterials: (state, action: PayloadAction<Material[]>) => {
      state.materials = action.payload;
      state.lastUpdated = Date.now();
    },
    updateMaterial: (state, action: PayloadAction<Material>) => {
      const index = state.materials.findIndex((m) => m.id === action.payload.id);
      if (index !== -1) {
        state.materials[index] = action.payload;
      }
    },
    setFilters: (state, action: PayloadAction<Partial<InventoryState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch materials
      .addCase(fetchMaterials.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMaterials.fulfilled, (state, action) => {
        state.isLoading = false;
        state.materials = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchMaterials.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch movements
      .addCase(fetchMovements.fulfilled, (state, action) => {
        state.movements = action.payload;
      })
      // Create movement
      .addCase(createMovement.fulfilled, (state, action) => {
        state.movements.unshift(action.payload);
        // Update material stock
        const material = state.materials.find(
          (m) => m.id === action.payload.materialId
        );
        if (material) {
          const delta =
            action.payload.type === 'entry'
              ? action.payload.quantity
              : -action.payload.quantity;
          material.currentStock += delta;
        }
      });
  },
});

export const {
  setMaterials,
  updateMaterial,
  setFilters,
  clearFilters,
  clearError,
} = inventorySlice.actions;

export default inventorySlice.reducer;
