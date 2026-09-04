import { test, expect } from '../../fixtures/base.fixture';

/* רגרסיה לבאג שדווח על ה-Artifact (04/09/2026):
   „כל פעם שאני לוחץ על כפתור בגרפים התחתונים זה מיד מקפיץ אותי לתחילת העמוד”.

   בקונסולה כל שינוי מצב בונה מחדש את גריד הפאנלים. הבנייה מוחקת את צומת
   העוגן שהדפדפן משתמש בו לשמירת מיקום הגלילה (scroll anchoring), ומכיוון
   שגובה המסמך אינו משתנה — הדפדפן פשוט ויתר וקפץ לראש. נמדד: 693 → 64.

   בדו״ח המנגנון אחר: הגובה כן משתנה (טבלה נמוכה מגרף), ולכן שמירת scrollY
   מוחלטת שגויה שם. מה שנשמר הוא מיקום הפקד שנלחץ בתוך החלון. */

const PANEL_CONTROLS = [
  { panel: 'anaf'   as const, button: 'טבלה' },
  { panel: 'change' as const, button: 'טבלה' },
];

test.describe('קונסולה · הגלילה נשארת במקום', () => {
  for (const { panel, button } of PANEL_CONTROLS) {
    test(`לחיצה על „${button}” בפאנל ${panel} אינה מקפיצה לראש`, async ({ consolePage, page }) => {
      await consolePage.goto();
      await expect(consolePage.panel(panel).chart).toBeVisible();
      await consolePage.panel(panel).body.scrollIntoViewIfNeeded();

      const before = await page.evaluate(() => Math.round(window.scrollY));
      expect(before, 'הבדיקה חייבת להתחיל כשהעמוד גלול').toBeGreaterThan(100);

      await consolePage.panel(panel).root_click(button);

      await expect.poll(() => page.evaluate(() => Math.round(window.scrollY)),
        { message: 'הלחיצה הקפיצה את העמוד' }).toBe(before);
    });
  }

  test('פקדי חלק ב׳ שומרים על מיקום הגלילה', async ({ consolePage, page }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    await expect(consolePage.panel('dist').chart).toBeVisible();
    await consolePage.panel('dist').body.scrollIntoViewIfNeeded();

    const before = await page.evaluate(() => Math.round(window.scrollY));
    expect(before).toBeGreaterThan(100);

    await consolePage.choosePeriod('לאורך זמן');

    await expect.poll(() => page.evaluate(() => Math.round(window.scrollY))).toBe(before);
  });

  test('הפוקוס חוזר לפקד המקביל אחרי הבנייה מחדש', async ({ consolePage, page }) => {
    await consolePage.goto();
    /* הכפתור שנלחץ נמחק בבנייה מחדש; בלי שחזור, משתמש מקלדת מאבד את מקומו. */
    await consolePage.panel('anaf').showTable();
    const focused = await page.evaluate(() =>
      (document.activeElement?.textContent || '').trim());
    expect(focused).toBe('טבלה');
  });

  test('מעבר בין טאבים כן חוזר לראש העמוד', async ({ consolePage, page }) => {
    await consolePage.goto();
    await consolePage.panel('anaf').body.scrollIntoViewIfNeeded();
    expect(await page.evaluate(() => Math.round(window.scrollY))).toBeGreaterThan(100);

    await consolePage.openPartB();

    /* כאן זו ההתנהגות הנכונה: כל התוכן הוחלף. */
    await expect.poll(() => page.evaluate(() => Math.round(window.scrollY))).toBe(0);
  });
});

test.describe('דו״ח · הפקד שנלחץ נשאר במקומו', () => {
  test('החלפה לטבלה אינה מזיזה את הפקד, גם כשהמקטע מתקצר', async ({ reportPage, page }) => {
    await reportPage.goto();
    const toggle = page.locator('#changeView');
    await toggle.scrollIntoViewIfNeeded();

    const before = await toggle.evaluate(n => Math.round(n.getBoundingClientRect().top));
    const height = await page.evaluate(() => document.documentElement.scrollHeight);

    await toggle.getByRole('button', { name: 'טבלה', exact: true }).click();

    /* גובה המסמך באמת משתנה — ולכן שמירת scrollY מוחלטת הייתה שגויה כאן. */
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollHeight))
      .not.toBe(height);
    await expect.poll(() => toggle.evaluate(n => Math.round(n.getBoundingClientRect().top)),
      { message: 'הפקד זז מתחת לאצבע' }).toBe(before);
  });
});
