/**
 * API Services Exports
 */

export { default as apiClient, handleApiError } from './client';
export type { ApiResponse, ApiError } from './client';

export { inventoryApi } from './inventory';
export type { Material, Movement } from './inventory';

export { transactionsApi } from './transactions';
export type { Transaction, TransactionFilters } from './transactions';

export { paymentsApi } from './payments';
export type { Payment, PaymentFilters } from './payments';

export { projectsApi } from './projects';
export type { Project, ProjectFilters } from './projects';
