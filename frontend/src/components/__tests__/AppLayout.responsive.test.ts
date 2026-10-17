/// <reference types="node" />
import { readFileSync } from 'fs';
import { resolve } from 'path';

/**
 * jsdom does not evaluate media queries, so these tests read the stylesheet
 * itself. They fail if the phone rules are removed or weakened; they do not
 * render anything. The layout was checked in a real browser at 375px wide.
 * (tsconfig.json limits the global types to vite/client, so the node types
 * the file reader needs are referenced here.)
 */
const stylesheet = readFileSync(resolve(__dirname, '../layout/AppLayout.css'), 'utf8');

type Declarations = Record<string, string>;

/** The text between the braces of the @media (max-width: 768px) block, or '' if there is none. */
function phoneBlock(source: string): string {
  const start = source.indexOf('@media (max-width: 768px)');
  if (start === -1) return '';
  const open = source.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(open + 1, i);
    }
  }
  return '';
}

/** Each selector in a block of plain rules, with its declarations as a property -> value map. */
function rulesIn(block: string): Map<string, Declarations> {
  const rules = new Map<string, Declarations>();
  for (const part of block.split('}')) {
    const [selector, body] = part.split('{');
    if (body === undefined) continue;
    const declarations: Declarations = {};
    for (const declaration of body.split(';')) {
      const [property, ...value] = declaration.split(':');
      if (value.length > 0) declarations[property.trim()] = value.join(':').trim();
    }
    rules.set(selector.trim(), declarations);
  }
  return rules;
}

describe('AppLayout on a phone', () => {
  const phone = rulesIn(phoneBlock(stylesheet));

  it('has rules for narrow screens', () => {
    expect(phone.size).toBeGreaterThan(0);
  });

  it('stacks the sidebar above the page and lets the page grow instead of clipping it', () => {
    const layout = phone.get('.app-layout');
    expect(layout).toMatchObject({
      'flex-direction': 'column',
      height: 'auto',
      overflow: 'visible',
    });
  });

  it('gives the sidebar the width of the screen instead of its fixed 260px', () => {
    expect(phone.get('.sidebar')).toMatchObject({ width: 'auto' });
  });

  it('lays the three navigation links out in a row of equal shares', () => {
    expect(phone.get('.sidebar-nav')).toMatchObject({ 'flex-direction': 'row' });
    expect(phone.get('.nav-item')).toMatchObject({ flex: '1 1 0', 'min-width': '0' });
  });

  it('lets the page content take the width that is left', () => {
    expect(phone.get('.main-content-area')).toMatchObject({ overflow: 'visible', 'min-width': '0' });
    expect(phone.get('.page-content')).toMatchObject({ 'overflow-y': 'visible' });
  });

  it('leaves the desktop sidebar at its fixed width', () => {
    const desktop = rulesIn(stylesheet.slice(0, stylesheet.indexOf('@media (max-width: 768px)')));
    expect(desktop.get('.sidebar')).toMatchObject({ width: '260px' });
  });
});
