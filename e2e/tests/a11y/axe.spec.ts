import AxeBuilder from '@axe-core/playwright';
import { test, expect } from '../../fixtures/base.fixture';
import { SITES } from '../../helpers/sites';

/* סריקת axe בסיסית בלבד. כיווני WCAG, כוונון חוקים ותיקון מעמיק
   שייכים ל-accessibility-testing, לא לכאן. */

for (const [name, site] of Object.entries(SITES)) {
  test(`${name}: אין הפרות נגישות קריטיות`, async ({ page }) => {
    await page.goto(site.path);
    /* חריגה מוצדקת: ל-<svg> אין role נגיש לבחירה, והוא סימן המוכנות של הדף. */
    await expect(page.locator('svg').first()).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    const serious = results.violations.filter(v => ['critical', 'serious'].includes(v.impact ?? ''));
    expect(serious.map(v => `${v.id}: ${v.nodes.length} צמתים`)).toEqual([]);
  });
}

test('הדף מצהיר על עברית ועל כיוון RTL', async ({ page }) => {
  await page.goto(SITES.report.path);
  /* חריגה מוצדקת: <html> אינו נבחר לפי role או label. */
  await expect(page.locator('html')).toHaveAttribute('lang', 'he');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
});
