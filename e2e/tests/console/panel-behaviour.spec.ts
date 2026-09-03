import { test, expect } from '../../fixtures/base.fixture';

test.describe('התנהגות פאנל', () => {
  test('טוגל גרף/טבלה מחליף תצוגה בכל הפאנלים', async ({ consolePage }) => {
    await consolePage.goto();
    const p = consolePage.panel('auth');
    await expect(p.chart).toBeVisible();

    await p.showTable();
    await expect(p.table).toBeVisible();
    await expect(p.chart).toHaveCount(0);
    await expect(p.tableRows).toHaveCount(18);

    await p.showChart();
    await expect(p.chart).toBeVisible();
    await expect(p.table).toHaveCount(0);
  });

  test('לחיצה על עמודה מסנכרנת את פילטר הענפים', async ({ consolePage }) => {
    await consolePage.goto();
    await expect(consolePage.panel('auth').chart).toBeVisible();
    await expect(consolePage.selectValue('רשות בגרף הענפים')).toHaveValue('region');

    await consolePage.panel('auth').bar(0).click();

    await expect(consolePage.selectValue('רשות בגרף הענפים')).not.toHaveValue('region');
    await expect(consolePage.panel('anaf').warning).toContainText('סף ההשמטה');
  });

  test('כל פאנל נושא שורת מקור וכפתור ייצוא', async ({ consolePage }) => {
    await consolePage.goto();
    for (const id of ['auth', 'change', 'anaf'] as const) {
      await expect(consolePage.panel(id).source).not.toBeEmpty();
      await expect(consolePage.panel(id).exportButton).toBeVisible();
    }
  });

  test('בחירת קיבוץ ענפים מצמצמת את הרשימה', async ({ consolePage }) => {
    await consolePage.goto();
    const anaf = consolePage.panel('anaf');
    await anaf.showTable();
    await expect(anaf.tableRows).toHaveCount(10);          // ברירת המחדל: 10 הגבוהים
    await anaf.localSelect(0).selectOption({ label: 'כל הענפים' });
    const all = await anaf.tableRows.count();
    expect(all, 'בחירת „כל הענפים” לא הרחיבה את הרשימה').toBeGreaterThan(10);
  });
});
