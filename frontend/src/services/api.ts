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
import { describeApiError, SIGN_IN_PATH } from '../utils/apiErrorMessage';

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

// A production build is served by the FastAPI app itself, so it calls the API on
// its own origin. VITE_API_URL overrides this when the API lives elsewhere; the
// dev server keeps talking to the local backend.
const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:8000');

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
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
    // A 401 from the sign-in request itself is a wrong password, not an ended session.
    if (error.response?.status === 401 && error.config?.url !== SIGN_IN_PATH) {
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

    const response = await apiClient.post<AuthToken>(SIGN_IN_PATH, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    authStorage.set(response.data.access_token);
    return response.data.access_token;
  },

  /**
   * Sign in as the shared demo account. Resolves true when it worked, and false
   * when the server has demo mode off (404) or cannot be reached, so the caller
   * falls back to the normal sign-in page.
   */
  demoLogin: async (): Promise<boolean> => {
    try {
      const response = await apiClient.post<AuthToken>('/demo-token');
      authStorage.set(response.data.access_token);
      return true;
    } catch {
      return false;
    }
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

/** Plain-language message for whatever a request threw (the rules live in utils/apiErrorMessage.ts, where they are tested). */
export const handleApiError = describeApiError;

export default apiClient;
