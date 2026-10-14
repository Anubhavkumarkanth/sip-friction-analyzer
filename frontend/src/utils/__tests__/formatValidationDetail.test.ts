import { formatValidationDetail } from '../formatValidationDetail';

describe('formatValidationDetail', () => {
  it('passes a plain string through', () => {
    expect(formatValidationDetail('Simulation not found')).toBe('Simulation not found');
  });

  it('keeps the messages from a FastAPI validation list and names the field each is about', () => {
    const detail = [
      { type: 'value_error', loc: ['body', 'events', 0], msg: 'Value error, REDUCE requires factor' },
      { type: 'greater_than', loc: ['body', 'years'], msg: 'Input should be greater than 0' },
    ];
    expect(formatValidationDetail(detail)).toBe(
      'Event 1: REDUCE requires factor; Years: Input should be greater than 0'
    );
  });

  it('turns a snake_case field into words', () => {
    const detail = [{ loc: ['body', 'monthly_amount'], msg: 'Input should be greater than 0' }];
    expect(formatValidationDetail(detail)).toBe('Monthly amount: Input should be greater than 0');
  });

  it('counts events from 1 and names the field inside the event', () => {
    const detail = [{ loc: ['body', 'events', 2, 'start_month'], msg: 'Input should be greater than or equal to 1' }];
    expect(formatValidationDetail(detail)).toBe('Event 3, start month: Input should be greater than or equal to 1');
  });

  it('names a query parameter without saying it came from the query', () => {
    const detail = [{ loc: ['query', 'skip'], msg: 'Input should be greater than or equal to 0' }];
    expect(formatValidationDetail(detail)).toBe('Skip: Input should be greater than or equal to 0');
  });

  it('gives only the message when the error is about the request as a whole', () => {
    const detail = [{ loc: ['body'], msg: 'Value error, events[0].month is 999, after the end of a 1-year (12-month) plan' }];
    expect(formatValidationDetail(detail)).toBe('events[0].month is 999, after the end of a 1-year (12-month) plan');
  });

  it('gives only the message when there is no location at all', () => {
    expect(formatValidationDetail([{ msg: 'Something is off' }])).toBe('Something is off');
  });

  it('falls back to JSON for items that have no message', () => {
    expect(formatValidationDetail([{ code: 7 }])).toBe('{"code":7}');
  });

  it('falls back to JSON for anything else', () => {
    expect(formatValidationDetail({ reason: 'nope' })).toBe('{"reason":"nope"}');
  });
});
