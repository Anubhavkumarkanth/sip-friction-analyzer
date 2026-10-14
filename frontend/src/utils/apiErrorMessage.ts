import { formatValidationDetail } from './formatValidationDetail';

/** The sign-in request. Its 401 means "wrong username or password", not "your session ended". */
export const SIGN_IN_PATH = '/token';

/** The parts of an Axios error that the messages below depend on (kept structural so this file needs no Axios import). */
interface ApiErrorLike {
  isAxiosError: true;
  code?: string;
  message?: string;
  config?: { url?: string };
  response?: { status?: number; data?: { detail?: unknown } };
}

const isApiError = (error: unknown): error is ApiErrorLike =>
  typeof error === 'object' && error !== null && (error as { isAxiosError?: unknown }).isAxiosError === true;

/** One sentence for the person using the app, for anything a request can throw. */
export const describeApiError = (error: unknown): string => {
  if (isApiError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (status === 401) {
      if (error.config?.url === SIGN_IN_PATH) {
        return typeof detail === 'string' && detail ? detail : 'Incorrect username or password.';
      }
      return 'Your session has expired. Please sign in again.';
    }
    if (detail) return formatValidationDetail(detail);
    if (status === 404) return 'Requested resource not found.';
    if (status === 500) return 'Server error occurred during simulation.';
    if (error.code === 'ECONNABORTED') return 'Simulation request timed out. Please try with fewer iterations.';
    if (error.message === 'Network Error') return 'Backend API is unreachable. Please ensure the server is running.';
    return error.message || 'An error occurred during the request.';
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred.';
};
