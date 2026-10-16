import { describeApiError, SIGN_IN_PATH } from '../apiErrorMessage';

/** The shape of an Axios error, which is all describeApiError looks at. */
const apiError = (parts: {
  status?: number;
  detail?: unknown;
  url?: string;
  code?: string;
  message?: string;
}) => ({
  isAxiosError: true as const,
  message: parts.message ?? 'Request failed',
  code: parts.code,
  config: { url: parts.url },
  response: parts.status === undefined ? undefined : { status: parts.status, data: { detail: parts.detail } },
});

describe('describeApiError', () => {
  describe('signing in', () => {
    it('says the credentials are wrong when the sign-in request is refused', () => {
      const error = apiError({ status: 401, url: SIGN_IN_PATH, detail: 'Incorrect username or password' });
      expect(describeApiError(error)).toBe('Incorrect username or password');
    });

    it('does not say the session expired for a refused sign-in, even without a server message', () => {
      const message = describeApiError(apiError({ status: 401, url: SIGN_IN_PATH }));
      expect(message).toBe('Incorrect username or password.');
      expect(message).not.toMatch(/expired/i);
    });
  });

  describe('a session that ended', () => {
    it('asks the person to sign in again when another request gets a 401', () => {
      const error = apiError({ status: 401, url: '/simulations', detail: 'Could not validate credentials' });
      expect(describeApiError(error)).toBe('Your session has expired. Please sign in again.');
    });
  });

  describe('invalid input', () => {
    it('names the field that was rejected', () => {
      const error = apiError({
        status: 422,
        detail: [{ loc: ['body', 'years'], msg: 'Input should be less than or equal to 60' }],
      });
      expect(describeApiError(error)).toBe('Years: Input should be less than or equal to 60');
    });

    it('names the event that was rejected', () => {
      const error = apiError({
        status: 422,
        detail: [
          { loc: ['body', 'events', 0], msg: 'Value error, PAUSE_RANGE end_month must not be before start_month' },
        ],
      });
      expect(describeApiError(error)).toBe('Event 1: PAUSE_RANGE end_month must not be before start_month');
    });

    it('passes a plain-text server message through', () => {
      expect(describeApiError(apiError({ status: 404, detail: 'Simulation not found' }))).toBe('Simulation not found');
    });
  });

  describe('failures with no server message', () => {
    it('explains a missing resource', () => {
      expect(describeApiError(apiError({ status: 404 }))).toBe('Requested resource not found.');
    });

    it('explains a server error', () => {
      expect(describeApiError(apiError({ status: 500 }))).toBe('Server error occurred during simulation.');
    });

    it('explains a timeout', () => {
      expect(describeApiError(apiError({ code: 'ECONNABORTED' }))).toMatch(/timed out/);
    });

    it('explains an unreachable server', () => {
      expect(describeApiError(apiError({ message: 'Network Error' }))).toMatch(/unreachable/);
    });

    it('falls back to the error text', () => {
      expect(describeApiError(apiError({ status: 418, message: 'I am a teapot' }))).toBe('I am a teapot');
    });
  });

  describe('errors that did not come from a request', () => {
    it('uses the message of an ordinary Error', () => {
      expect(describeApiError(new Error('boom'))).toBe('boom');
    });

    it('has a sentence for anything else', () => {
      expect(describeApiError('nope')).toBe('An unexpected error occurred.');
    });
  });
});
