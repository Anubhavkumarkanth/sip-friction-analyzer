import { formatValidationDetail } from '../formatValidationDetail';

describe('formatValidationDetail', () => {
  it('passes a plain string through', () => {
    expect(formatValidationDetail('Simulation not found')).toBe('Simulation not found');
  });

  it('keeps only the messages from a FastAPI validation list', () => {
    const detail = [
      { type: 'value_error', loc: ['body', 'events', 0], msg: 'Value error, REDUCE requires factor' },
      { type: 'greater_than', loc: ['body', 'years'], msg: 'Input should be greater than 0' },
    ];
    expect(formatValidationDetail(detail)).toBe(
      'REDUCE requires factor; Input should be greater than 0'
    );
  });

  it('falls back to JSON for items that have no message', () => {
    expect(formatValidationDetail([{ code: 7 }])).toBe('{"code":7}');
  });

  it('falls back to JSON for anything else', () => {
    expect(formatValidationDetail({ reason: 'nope' })).toBe('{"reason":"nope"}');
  });
});
