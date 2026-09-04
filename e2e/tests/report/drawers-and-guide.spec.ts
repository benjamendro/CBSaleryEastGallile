import { test, expect } from '../../fixtures/base.fixture';

const SECTIONS = ['auth', 'change', 'anaf', 'mix', 'dist', 'trend'] as const;

test.describe('מגירות ומורה נבוכים', () => {
  test('שתי מגירות לכל מקטע, סגורות כברירת מחדל', async ({ reportPage }) => {
    await reportPage.goto();
    for (const sec of SECTIONS) {
      await expect(reportPage.briefButton(sec)).toHaveAttribute('aria-expanded', 'false');
      await expect(reportPage.insightsButton(sec)).toHaveAttribute('aria-expanded', 'false');
      await expect(reportPage.briefBody(sec)).toBeHidden();
    }
  });

  test('לחיצה פותחת וסוגרת, ו-aria-expanded עוקב', async ({ reportPage }) => {
    await reportPage.goto();
    const btn = reportPage.briefButton('auth');
    await btn.click();
    await expect(btn).toHaveAttribute('aria-expanded', 'true');
    await expect(reportPage.briefBody('auth')).toBeVisible();
    await btn.click();
    await expect(btn).toHaveAttribute('aria-expanded', 'false');
    await expect(reportPage.briefBody('auth')).toBeHidden();
  });

  test('הכפתור נקרא „על הנתונים” ולא בשם הישן', async ({ reportPage, page }) => {
    await reportPage.goto();
    await expect(reportPage.briefButton('auth')).toHaveText(/על הנתונים/);
    await expect(page.getByRole('button', { name: 'מה יש כאן' })).toHaveCount(0);
  });

  test('מורה נבוכים בונה כרטיס לכל מקטע, עם שאלות', async ({ reportPage }) => {
    await reportPage.goto();
    await expect(reportPage.guideCards).toHaveCount(6);
    /* הכרטיסים נבנים מתוך ה-DOM של הפתיחים עצמם, ולכן לא יכולים להתיישן
       ביחס אליהם — כרטיס בלי שאלות פירושו שהקישור נשבר. */
    const counts = await reportPage.guideCards.evaluateAll(cards =>
      cards.map(c => c.querySelectorAll('li').length));
    expect(counts.every(n => n > 0), `כרטיס ללא שאלות: ${counts.join(',')}`).toBe(true);
  });

  test('קישור מהמורה נבוכים פותח את המגירה ביעד', async ({ reportPage }) => {
    await reportPage.goto();
    await expect(reportPage.briefButton('mix')).toHaveAttribute('aria-expanded', 'false');
    await reportPage.guideCards.filter({ hasText: 'תמהיל התעסוקה' })
      .getByRole('link', { name: /למקטע/ }).click();
    await expect(reportPage.briefButton('mix')).toHaveAttribute('aria-expanded', 'true');
  });

  test('לכל גרף כותרת תחתונה עם ייצוא', async ({ reportPage }) => {
    await reportPage.goto();
    await expect(reportPage.figureFooters).toHaveCount(6);
  });
});
