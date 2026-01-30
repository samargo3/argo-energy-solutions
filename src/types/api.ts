// Base API response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Date range query parameters
export interface DateRangeParams {
  startDate: string;
  endDate: string;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

