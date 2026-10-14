/**
 * Turn the `detail` of a failed API response into one readable line.
 *
 * FastAPI reports a rejected request as a list of {loc, msg, ...} objects. Shown as raw JSON that is unreadable, so keep
 * the messages and say which field each one is about: "Years: Input should be less than or equal to 60".
 * Pydantic prefixes messages raised by our own validators with "Value error, "; that is noise for the person reading it.
 */

/** Where FastAPI says a value came from. The reader does not need it. */
const SOURCES = ['body', 'query', 'path', 'header', 'cookie'];

const humanize = (key: string): string => {
  const words = key.replace(/_/g, ' ').trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
};

/**
 * "Years", "Monthly amount", "Event 2" or "Event 2, start month" for a FastAPI `loc`; an empty string when the error is
 * about the request as a whole (its message then has to say what it is about).
 */
const describeLocation = (loc: unknown): string => {
  if (!Array.isArray(loc)) return '';
  const parts = loc.filter((part, i) => !(i === 0 && typeof part === 'string' && SOURCES.includes(part)));

  // Events are a list, so the position matters. People count from 1.
  const eventsAt = parts.indexOf('events');
  const position = eventsAt === -1 ? undefined : parts[eventsAt + 1];
  if (typeof position === 'number') {
    const label = `Event ${position + 1}`;
    const field = parts[eventsAt + 2];
    return typeof field === 'string' ? `${label}, ${field.replace(/_/g, ' ')}` : label;
  }

  const last = [...parts].reverse().find((part) => typeof part === 'string');
  return typeof last === 'string' ? humanize(last) : '';
};

export const formatValidationDetail = (detail: unknown): string => {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return JSON.stringify(detail);

  return detail
    .map((item) => {
      if (typeof item?.msg !== 'string') return JSON.stringify(item);
      const message = item.msg.replace(/^Value error, /, '');
      const where = describeLocation(item.loc);
      return where ? `${where}: ${message}` : message;
    })
    .join('; ');
};
