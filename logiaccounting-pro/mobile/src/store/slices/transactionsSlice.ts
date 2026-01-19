/**
 * Transactions State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { transactionsApi } from '@services/api/transactions';

interface Transaction {
  id: string;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  taxAmount: number;
  date: string;
  description: string;
  vendorName?: string;
  invoiceNumber?: string;
  invoiceUrl?: string;
  projectId?: string;
}

interface TransactionsState {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  filters: {
    type: 'all' | 'income' | 'expense';
    dateRange: { start: string | null; end: string | null };
    category: string | null;
  };
}

const initialState: TransactionsState = {
  transactions: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {
    type: 'all',
    dateRange: { start: null, end: null },
    category: null,
  },
};

export const fetchTransactions = createAsyncThunk(
  'transactions/fetchTransactions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await transactionsApi.getTransactions();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch transactions');
    }
  }
);

export const createTransaction = createAsyncThunk(
  'transactions/createTransaction',
  async (transaction: Omit<Transaction, 'id'>, { rejectWithValue }) => {
    try {
      const response = await transactionsApi.createTransaction(transaction);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create transaction');
    }
  }
);

const transactionsSlice = createSlice({
  name: 'transactions',
  initialState,
  reducers: {
    setTransactions: (state, action: PayloadAction<Transaction[]>) => {
      state.transactions = action.payload;
      state.lastUpdated = Date.now();
    },
    setFilters: (state, action: PayloadAction<Partial<TransactionsState['filters']>>) => {
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
      .addCase(fetchTransactions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.transactions = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(createTransaction.fulfilled, (state, action) => {
        state.transactions.unshift(action.payload);
      });
  },
});

export const { setTransactions, setFilters, clearFilters, clearError } = transactionsSlice.actions;
export default transactionsSlice.reducer;
