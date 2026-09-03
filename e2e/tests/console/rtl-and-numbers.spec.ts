import { test, expect } from '../../fixtures/base.fixture';

/* אזור הסיכון הראשון בפרויקט: RTL ו-bidi. שתי תקלות אמיתיות בעבר —
   text-anchor שמתנהג הפוך, ומספר עם סימן שהתהפך. */

test('מספרי KPI מבודדים כדי שהסימן לא יזוז', async ({ consolePage }) => {
  await consolePage.goto();
  await expect(consolePage.kpiValues.first()).toBeVisible();
  const styles = await consolePage.kpiValues.evaluateAll(ns =>
    ns.map(n => getComputedStyle(n).unicodeBidi));
  expect(styles.every(s => s === 'isolate'), 'ערך KPI ללא unicode-bidi:isolate').toBe(true);
});

test('הפער מהארצי מוצג עם סימן מינus בצד הנכון', async ({ consolePage }) => {
  await consolePage.goto();
  const gap = consolePage.kpiCards.filter({ hasText: 'הפער מהארצי' }).locator('.v');
  /* האשכול מתחת לארצי, ולכן הערך שלילי והסימן חייב להיות בתחילת המחרוזת. */
  await expect(gap).toHaveText(/^[−-]\d/);
});

test('ה-SVG בקונסולה מוגדר LTR — שם העיגון מתנהג כרגיל', async ({ consolePage }) => {
  await consolePage.goto();
  await expect(consolePage.panel('auth').chart).toBeVisible();
  const dir = await consolePage.panel('auth').chart.evaluate(n => getComputedStyle(n).direction);
  expect(dir).toBe('ltr');
});

test('אין גלילה אופקית ברוחבי מסך צרים', async ({ consolePage, page }) => {
  /* טעינה אחת ואחריה שינויי רוחב — זה גם מה שמשתמש עושה כשהוא משנה גודל
     חלון, וגם חוסך שלוש טעינות של דף בן 178KB. */
  await consolePage.goto();
  await expect(consolePage.panel('auth').chart).toBeVisible();

  for (const width of [1440, 1024, 768, 420]) {
    await page.setViewportSize({ width, height: 900 });
    /* ResizeObserver מצייר מחדש אחרי שינוי הרוחב, ולכן המדידה חייבת לחזור
       על עצמה עד שהפריסה נחה. expect.poll עושה בדיוק את זה — לא השהיה קבועה. */
    await expect.poll(() => page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth),
      { message: `גלילה אופקית ברוחב ${width}px` }).toBeLessThanOrEqual(2);
  }
});

test('גיאומטריית הגרף היא 1:1 מול הקונטיינר', async ({ consolePage, page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await consolePage.goto();
  await expect(consolePage.panel('auth').chart).toBeVisible();
  /* viewBox קבוע + width:100% מקטין גם את הטקסט, והתוויות בעברית נשברות. */
  await expect.poll(() => consolePage.panel('auth').chart.evaluate(svg => {
    const vb = (svg as unknown as SVGSVGElement).viewBox.baseVal.width;
    const box = (svg.parentElement as HTMLElement).clientWidth;
    return Math.abs(vb - box);
  }), { message: 'ה-viewBox אינו תואם את רוחב הקונטיינר' }).toBeLessThanOrEqual(4);
});
