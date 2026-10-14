/**
 * Turn the `detail` of a failed API response into one readable line.
 *
 * FastAPI reports a rejected request body as a list of {loc, msg, ...} objects.
 * Shown as raw JSON that is unreadable, so keep only the messages. Pydantic
 * prefixes messages raised by our own validators with "Value error, "; that is
 * noise for the person reading it.
 */
export const formatValidationDetail = (detail: unknown): string => {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return JSON.stringify(detail);

  return detail
    .map((item) =>
      typeof item?.msg === 'string' ? item.msg.replace(/^Value error, /, '') : JSON.stringify(item)
    )
    .join('; ');
};
