/**
 * Payments State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { paymentsApi } from '@services/api/payments';

interface Payment {
  id: string;
  type: 'receivable' | 'payable';
  amount: number;
  dueDate: string;
  paidDate?: string;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  description: string;
  clientId?: string;
  clientName?: string;
  vendorId?: string;
  vendorName?: string;
}

interface PaymentsState {
  payments: Payment[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  overdueCount: number;
  upcomingCount: number;
}

const initialState: PaymentsState = {
  payments: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  overdueCount: 0,
  upcomingCount: 0,
};

export const fetchPayments = createAsyncThunk(
  'payments/fetchPayments',
  async (_, { rejectWithValue }) => {
    try {
      const response = await paymentsApi.getPayments();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch payments');
    }
  }
);

export const recordPayment = createAsyncThunk(
  'payments/recordPayment',
  async ({ id, paidDate }: { id: string; paidDate: string }, { rejectWithValue }) => {
    try {
      const response = await paymentsApi.recordPayment(id, paidDate);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to record payment');
    }
  }
);

const paymentsSlice = createSlice({
  name: 'payments',
  initialState,
  reducers: {
    setPayments: (state, action: PayloadAction<Payment[]>) => {
      state.payments = action.payload;
      state.lastUpdated = Date.now();
      state.overdueCount = action.payload.filter((p) => p.status === 'overdue').length;
      state.upcomingCount = action.payload.filter(
        (p) =>
          p.status === 'pending' &&
          new Date(p.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      ).length;
    },
    updatePayment: (state, action: PayloadAction<Payment>) => {
      const index = state.payments.findIndex((p) => p.id === action.payload.id);
      if (index !== -1) {
        state.payments[index] = action.payload;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPayments.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPayments.fulfilled, (state, action) => {
        state.isLoading = false;
        state.payments = action.payload;
        state.lastUpdated = Date.now();
        state.overdueCount = action.payload.filter(
          (p: Payment) => p.status === 'overdue'
        ).length;
        state.upcomingCount = action.payload.filter(
          (p: Payment) =>
            p.status === 'pending' &&
            new Date(p.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
        ).length;
      })
      .addCase(fetchPayments.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(recordPayment.fulfilled, (state, action) => {
        const index = state.payments.findIndex((p) => p.id === action.payload.id);
        if (index !== -1) {
          state.payments[index] = action.payload;
        }
      });
  },
});

export const { setPayments, updatePayment, clearError } = paymentsSlice.actions;
export default paymentsSlice.reducer;
