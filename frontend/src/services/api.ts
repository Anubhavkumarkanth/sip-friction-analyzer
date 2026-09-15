import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  AuthToken,
  Fund,
  SimulationRequest,
  SimulationResult,
  SimulationSummary,
  SimulationDetail,
  MonteCarloRequest,
  MonteCarloResult,
} from '../types';

const TOKEN_KEY = 'sip_access_token';

/** Fired when the API rejects a request as unauthenticated. */
export const UNAUTHORIZED_EVENT = 'sip:unauthorized';

/**
 * Access token storage.
 *
 * Every access is wrapped: localStorage throws in a private window or when a
 * browser is set to block site data, and an exception here would otherwise take
 * down the whole page on load.
 */
export const authStorage = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string): void {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* ignore: the session simply will not survive a reload */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the bearer token to every request that has one available.
apiClient.interceptors.request.use((config) => {
  const token = authStorage.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // The token is gone or expired. Drop it and tell the app, so the UI can
      // return to the sign-in screen instead of leaving the user clicking a
      // button that will keep failing.
      authStorage.clear();
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  /**
   * Exchange credentials for a token.
   *
   * Sent as form-encoded rather than JSON because the endpoint uses FastAPI's
   * OAuth2PasswordRequestForm, which reads form fields.
   */
  login: async (username: string, password: string): Promise<string> => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);

    const response = await apiClient.post<AuthToken>('/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    authStorage.set(response.data.access_token);
    return response.data.access_token;
  },

  logout: (): void => authStorage.clear(),

  isLoggedIn: (): boolean => authStorage.get() !== null,
};

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

export const simulationAPI = {
  run: async (request: SimulationRequest): Promise<SimulationResult> => {
    const response = await apiClient.post<SimulationResult>('/simulate', request);
    return response.data;
  },

  history: async (limit = 20): Promise<SimulationSummary[]> => {
    const response = await apiClient.get<SimulationSummary[]>('/simulations', {
      params: { limit },
    });
    return response.data;
  },

  detail: async (id: number): Promise<SimulationDetail> => {
    const response = await apiClient.get<SimulationDetail>(`/simulations/${id}`);
    return response.data;
  },

  monteCarlo: async (request: MonteCarloRequest): Promise<MonteCarloResult> => {
    const response = await apiClient.post<MonteCarloResult>('/monte-carlo', request);
    return response.data;
  },
};

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      return 'Your session has expired. Please sign in again.';
    }
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
