import axios, { AxiosError, AxiosInstance } from 'axios';
import { Fund, SimulationRequest, SimulationResult, MonteCarloRequest, MonteCarloResult } from '../types';

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      console.warn('Session expired or unauthorized.');
    }
    return Promise.reject(error);
  }
);

// ==================== Funds API ====================
export const fundsAPI = {
  search: async (
    query?: string,
    platform?: string,
    risk?: string,
    sortBy?: string
  ): Promise<Fund[]> => {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (platform && platform !== 'All Platforms') params.append('platform', platform);
    if (risk && risk !== 'All Risks') params.append('risk', risk);
    if (sortBy) params.append('sort_by', sortBy);

    const response = await apiClient.get<Fund[]>('/search-funds', { params });
    return response.data;
  },

  getAll: async (skip = 0, limit = 100): Promise<Fund[]> => {
    const response = await apiClient.get<Fund[]>('/funds', {
      params: { skip, limit },
    });
    return response.data;
  },
};

// ==================== Simulation API ====================
export const simulationAPI = {
  run: async (request: SimulationRequest): Promise<SimulationResult> => {
    const response = await apiClient.post<SimulationResult>('/simulate', request);
    return response.data;
  },

  monteCarlo: async (request: MonteCarloRequest): Promise<MonteCarloResult> => {
    const response = await apiClient.post<MonteCarloResult>('/monte-carlo', request);
    return response.data;
  },
};

// ==================== Error Formatter ====================
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail);
    }
    if (error.response?.status === 404) {
      return 'Requested resource not found.';
    }
    if (error.response?.status === 500) {
      return 'Server error occurred during simulation.';
    }
    if (error.code === 'ECONNABORTED') {
      return 'Simulation request timed out. Please try with fewer iterations.';
    }
    if (error.message === 'Network Error') {
      return 'Backend API is unreachable. Please ensure the server is running.';
    }
    return error.message || 'An error occurred during the request.';
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred.';
};

export default apiClient;
