import { useState, useCallback, useEffect } from 'react';
import { handleApiError } from '../services/api';

export interface UseFetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Custom hook for fetching data with error handling
 * @param fetchFn - Async function that returns the data
 * @param deps - Dependency array for re-running fetch
 */
export const useFetch = <T,>(
  fetchFn: () => Promise<T>,
  deps: unknown[] = []
): UseFetchState<T> & { refetch: () => Promise<void> } => {
  const [state, setState] = useState<UseFetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await fetchFn();
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: handleApiError(err),
      });
    }
  }, [fetchFn]);

  useEffect(() => {
    refetch();
  }, deps);

  return { ...state, refetch };
};

