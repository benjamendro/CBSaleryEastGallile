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

  test('לחיצה על עמודה מסנכרנת את בורר הרשות שבפאנל הענפים', async ({ consolePage }) => {
    await consolePage.goto();
    await expect(consolePage.panel('auth').chart).toBeVisible();
    await expect(consolePage.anafAuthority).toHaveValue('region');

    await consolePage.panel('auth').bar(0).click();

    await expect(consolePage.anafAuthority).not.toHaveValue('region');
    await expect(consolePage.panel('anaf').warning).toContainText('סף ההשמטה');
  });

  test('בחירת רשות בפאנל הענפים מסננת את הפאנל בלבד', async ({ consolePage }) => {
    await consolePage.goto();
    await expect(consolePage.panel('anaf').chart).toBeVisible();
    await consolePage.anafAuthority.selectOption({ label: 'צפת' });
    await expect(consolePage.panel('anaf').subtitle).toContainText('צפת');
    await expect(consolePage.panel('anaf').warning).toContainText('משכירי צפת');
    /* שאר הפאנלים אינם מושפעים — זה פקד של פאנל, לא של המסך. */
    await expect(consolePage.panel('auth').subtitle).not.toContainText('צפת');
  });

  test('כל פאנל נושא שורת מקור וכפתור ייצוא', async ({ consolePage }) => {
    await consolePage.goto();
    for (const id of ['auth', 'change', 'anaf'] as const) {
      await expect(consolePage.panel(id).source).not.toBeEmpty();
      await expect(consolePage.panel(id).exportButton).toBeVisible();
    }
  });

  test('בחירת טווח מרחיבה את רשימת הענפים', async ({ consolePage }) => {
    await consolePage.goto();
    const anaf = consolePage.panel('anaf');
    await anaf.showTable();
    await expect(anaf.tableRows).toHaveCount(10);          // ברירת המחדל: 10 הגבוהים
    await anaf.rangeSelect.selectOption({ label: 'כל הענפים' });
    const all = await anaf.tableRows.count();
    expect(all, 'בחירת „כל הענפים” לא הרחיבה את הרשימה').toBeGreaterThan(10);
  });
});

test.describe('בחירת ענפים ידנית', () => {
  test('חיפוש מצמצם את רשימת הסימון', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openAnafPicker();
    const before = await consolePage.anafPickerOptions.count();
    expect(before).toBeGreaterThan(20);
    await consolePage.anafPickerSearch.fill('חינוך');
    const after = await consolePage.anafPickerOptions.count();
    expect(after, 'החיפוש לא צמצם את הרשימה').toBeLessThan(before);
    expect(after).toBeGreaterThan(0);
  });

  test('סימון ענפים גובר על טווח ועל קיבוץ', async ({ consolePage }) => {
    await consolePage.goto();
    const anaf = consolePage.panel('anaf');
    await anaf.showTable();
    await expect(anaf.tableRows).toHaveCount(10);

    await consolePage.openAnafPicker();
    await consolePage.anafPickerOptions.nth(0).getByRole('checkbox').check();
    await consolePage.anafPickerOptions.nth(1).getByRole('checkbox').check();

    await expect(anaf.tableRows).toHaveCount(2);
    await expect(consolePage.anafPickerSummary).toContainText('2 נבחרו');
    /* הבוררים האוטומטיים מושבתים כדי שלא ייראה שהם עדיין קובעים. */
    await expect(anaf.rangeSelect).toBeDisabled();
    await expect(anaf.clusterSelect).toBeDisabled();
  });

  test('ניקוי הבחירה מחזיר את החיתוך האוטומטי', async ({ consolePage }) => {
    await consolePage.goto();
    const anaf = consolePage.panel('anaf');
    await anaf.showTable();
    await consolePage.openAnafPicker();
    await consolePage.anafPickerOptions.nth(0).getByRole('checkbox').check();
    await expect(anaf.tableRows).toHaveCount(1);

    await consolePage.anafPicker.getByRole('button', { name: 'ניקוי הבחירה' }).click();

    await expect(anaf.tableRows).toHaveCount(10);
    await expect(anaf.rangeSelect).toBeEnabled();
  });
});
