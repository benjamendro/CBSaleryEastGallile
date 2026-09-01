/**
 * What the reader actually sees.
 *
 * These tests boot the published dashboard/index.html in jsdom and compare the
 * rendered page against dashboard/data.json and dashboard/btl.json. The pytest
 * suite proves the page carries that data; this suite proves the page *renders*
 * it — one mark per authority, the figures printed on the metric cards, and the
 * selectors offering exactly the units the data covers.
 *
 * Nothing is stubbed. The page draws its own SVG and loads no third-party
 * script at runtime, so there is no external boundary to fake; jsdom runs the
 * real code against the real data.
 */
import fs from 'node:fs';
import path from 'node:path';
import { JSDOM } from 'jsdom';
import { beforeAll, describe, expect, it } from 'vitest';

const ROOT = path.resolve(import.meta.dirname, '..', '..');
const read = (...parts) => fs.readFileSync(path.join(ROOT, ...parts), 'utf8');

const DATA = JSON.parse(read('dashboard', 'data.json'));
const BTL = JSON.parse(read('dashboard', 'btl.json'));

let document;

/** Digits a reader could compare, with thousands separators removed. */
const numbersIn = (text) =>
  [...text.matchAll(/-?\d[\d,]*(?:\.\d+)?/g)].map((m) => Number(m[0].replace(/,/g, '')));

beforeAll(async () => {
  const dom = new JSDOM(read('dashboard', 'index.html'), {
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    url: 'https://example.org/',
  });
  // let the page finish its first render pass
  await new Promise((resolve) => setTimeout(resolve, 600));
  document = dom.window.document;
});

describe('the page boots', () => {
  it('should render every section the dashboard documents', () => {
    const rendered = [...document.querySelectorAll('section[id]')].map((s) => s.id);
    expect(rendered).toEqual([
      'sec-guide', 'sec-auth', 'sec-change', 'sec-anaf', 'sec-mix', 'sec-dist', 'sec-trend',
    ]);
  });

  it('should draw a figure in each of the six data sections', () => {
    const drawn = [...document.querySelectorAll('section[id] svg')].length;
    expect(drawn).toBeGreaterThanOrEqual(6);
  });

  it('should leave no injection marker visible to the reader', () => {
    expect(document.body.textContent).not.toContain('__DATA__');
    expect(document.body.textContent).not.toContain('__LOGO__');
  });
});

describe('the metric cards', () => {
  it("should print the cluster's people-weighted average wage", () => {
    const card = [...document.querySelectorAll('.kpi, [class*=kpi]')].find((el) =>
      el.textContent.includes(DATA.authorities.region.name),
    );
    expect(card, 'no card names the cluster').toBeTruthy();
    expect(numbersIn(card.textContent)).toContain(Math.round(DATA.authorities.region.salary));
  });

  it('should print the national average as the per-person series', () => {
    const card = [...document.querySelectorAll('.kpi, [class*=kpi]')].find((el) =>
      el.textContent.includes('כלל הארץ'),
    );
    expect(card, 'no card shows the national average').toBeTruthy();
    expect(numbersIn(card.textContent)).toContain(Math.round(DATA.authorities.national.salary));
  });

  it('should warn the reader off the per-post series it is easily confused with', () => {
    // CLAUDE.md pitfall 1: 13,514 ₪ is wages per salaried post, a different
    // series. It may appear on the page only as the thing the reader is told
    // this is not.
    const text = document.body.textContent;
    expect(text).toContain('13,514');
    const note = text.slice(Math.max(0, text.indexOf('13,514') - 400), text.indexOf('13,514') + 200);
    expect(note, 'the figure 13,514 appears without the warning that frames it').toMatch(
      /אינה סדרת|למשרת שכיר/,
    );
  });

  it('should state the gap the two averages actually imply', () => {
    const { region, national } = DATA.authorities;
    const expected = ((region.salary - national.salary) / national.salary) * 100;
    const card = [...document.querySelectorAll('.kpi, [class*=kpi]')].find((el) =>
      el.textContent.includes('פער'),
    );
    expect(card, 'no card shows the gap').toBeTruthy();
    const shown = numbersIn(card.textContent).find((n) => Math.abs(Math.abs(n) - Math.abs(expected)) < 0.15);
    expect(shown, `card reads ${JSON.stringify(card.textContent)}, expected ≈${expected.toFixed(1)}%`).toBeDefined();
  });

  it('should say which year every figure on the page belongs to', () => {
    expect(document.body.textContent).toContain(String(DATA.meta.year));
  });
});

describe('the authority comparison', () => {
  it('should draw one bar per authority in the cluster', () => {
    const bars = document.querySelectorAll('#sec-auth svg rect');
    expect(bars.length).toBe(DATA.authorities.items.length);
  });

  it('should label the bars with the authorities the data names', () => {
    const labels = [...document.querySelectorAll('#sec-auth svg text')].map((t) => t.textContent.trim());
    const named = DATA.authorities.items.filter((item) => labels.includes(item.name));
    expect(named.length, `only ${named.length} of 18 authorities are labelled`).toBe(
      DATA.authorities.items.length,
    );
  });

  it('should offer the three sort orders and nothing else', () => {
    const options = [...document.querySelector('#authSort').options].map((o) => o.value);
    expect(options).toEqual(['desc', 'asc', 'name']);
  });
});

describe('the industry comparison', () => {
  it('should let the reader scope down to any single authority', () => {
    const options = [...document.querySelector('#anafScope').options].map((o) => o.value);
    const perAuthority = options.filter((v) => v.startsWith('a:')).map((v) => v.slice(2));
    expect(new Set(perAuthority)).toEqual(new Set(Object.keys(DATA.anafByAuth)));
  });

  it('should offer the aggregate scopes alongside the authorities', () => {
    const options = [...document.querySelector('#anafScope').options].map((o) => o.value);
    expect(options).toContain('reg');
    expect(options).toContain('nat');
  });
});

describe('the National Insurance part', () => {
  it('should offer the cluster plus every authority the source covers', () => {
    const options = [...document.querySelector('#btlAuth').options].map((o) => o.value);
    const covered = BTL.authorities.filter((a) => !a.missing).map((a) => a.name);
    expect(options[0]).toBe('__cluster__');
    expect(new Set(options.slice(1))).toEqual(new Set(covered));
  });

  it('should not offer a unit the source has no data for at all', () => {
    // 'missing' means the source never covers the authority; 'excluded' only
    // means it is kept out of the cluster aggregate (no 2016 baseline) while
    // still being selectable for the years it does have. The two must not be
    // conflated: only the former may vanish from the selector.
    const options = [...document.querySelector('#btlAuth').options].map((o) => o.value);
    const absent = BTL.authorities.filter((a) => a.missing).map((a) => a.name);
    expect(absent.length, 'no authority is flagged missing, so this asserts nothing').toBeGreaterThan(0);
    for (const name of absent) {
      expect(options, `${name} has no data yet is offered as a unit`).not.toContain(name);
    }
  });

  it('should still offer an authority that is only kept out of the cluster aggregate', () => {
    const options = [...document.querySelector('#btlAuth').options].map((o) => o.value);
    const partial = BTL.cluster.excluded
      .map((item) => item.name)
      .filter((name) => !BTL.authorities.find((a) => a.name === name)?.missing);
    for (const name of partial) {
      expect(options, `${name} has data for some years but cannot be selected`).toContain(name);
    }
  });

  it('should tell the reader the two sources cannot be compared', () => {
    expect(document.body.textContent).toMatch(/8\.7%\s*[–-]\s*27\.2%/);
  });

  it('should separate the two sources with a visible break', () => {
    expect(document.querySelector('#srcbreak'), 'the source divider is gone').toBeTruthy();
  });
});
