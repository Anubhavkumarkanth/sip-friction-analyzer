import axios, { AxiosError, AxiosInstance } from 'axios';
import { Fund, SimulationRequest, SimulationResult } from '../types';

// Create axios instance with base URL from environment
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== Request/Response Interceptors ====================
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// ==================== Funds API ====================
export const fundsAPI = {
  /**
   * Search funds with optional filters
   */
  search: async (
    query?: string,
    platform?: string,
    risk?: string,
    sortBy?: string
  ): Promise<Fund[]> => {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (platform && platform !== 'All Platforms')
        params.append('platform', platform);
      if (risk) params.append('risk', risk);
      if (sortBy) params.append('sort_by', sortBy);

      const response = await apiClient.get<Fund[]>('/search-funds', { params });
      return response.data;
    } catch (error) {
      console.error('Error searching funds:', error);
      throw error;
    }
  },

  /**
   * Get all funds with pagination
   */
  getAll: async (skip = 0, limit = 100): Promise<Fund[]> => {
    try {
      const response = await apiClient.get<Fund[]>('/funds', {
        params: { skip, limit },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching funds:', error);
      throw error;
    }
  },

  /**
   * Get fund by ID
   */
  getById: async (id: number): Promise<Fund> => {
    try {
      const response = await apiClient.get<Fund>(`/funds/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching fund ${id}:`, error);
      throw error;
    }
  },
};

// ==================== Simulation API ====================
export const simulationAPI = {
  /**
   * Run SIP simulation with given parameters
   */
  run: async (request: SimulationRequest): Promise<SimulationResult> => {
    try {
      const response = await apiClient.post<SimulationResult>(
        '/simulate',
        request
      );
      return response.data;
    } catch (error) {
      console.error('Error running simulation:', error);
      throw error;
    }
  },

  /**
   * Run Monte Carlo simulation
   */
  monteCarlo: async (
    monthlyAmount: number,
    annualReturn: number,
    years: number,
    simulations = 1000,
    volatility = 0.15
  ): Promise<any> => {
    try {
      const response = await apiClient.post('/monte-carlo', {
        monthly_amount: monthlyAmount,
        annual_return: annualReturn,
        years,
        simulations,
        volatility,
      });
      return response.data;
    } catch (error) {
      console.error('Error running Monte Carlo:', error);
      throw error;
    }
  },
};

// ==================== Error Handling Utility ====================
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.status === 404) {
      return 'Resource not found';
    }
    if (error.response?.status === 500) {
      return 'Server error. Please try again later.';
    }
    if (error.message === 'Network Error') {
      return 'Unable to connect to server';
    }
    return error.message || 'An error occurred';
  }
  return 'An unexpected error occurred';
};

export default apiClient;
