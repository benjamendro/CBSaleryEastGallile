import { test, expect } from '../../fixtures/base.fixture';

/* רגרסיה לבאג שנמצא בסשן חקר C3/C5 (03/09/2026).
   T(id) קרא רק מ-content.json של זמן הבנייה ולא מעריכות הסשן, ולכן כל ציור
   מחדש — שינוי פילטר בקונסולה, שינוי בורר בחלק ב׳ של הדו״ח — מחק בשקט את
   מה שהמשתמש הרגע הקליד, בעוד מונה העריכות המשיך להראות שהעריכה קיימת.
   שני הדפים נפגעו מאותו שורש. */

const TYPED = 'טקסט בדיקת רגרסיה';

test('קונסולה: הערת עורך שורדת שינוי פילטר', async ({ consolePage, page }) => {
  await consolePage.goto();
  await expect(consolePage.panel('auth').chart).toBeVisible();

  await consolePage.editToggle.click();
  await expect(consolePage.editBar).toBeVisible();

  const anno = consolePage.panel('auth').annotation;
  await anno.click();
  await page.keyboard.type(TYPED);
  await expect(consolePage.editCount).toHaveText('1');

  await consolePage.chooseSegment('מדד להצגה', 'שכירים');

  await expect(consolePage.panel('auth').annotation).toHaveText(TYPED);
  await expect(consolePage.panel('auth').annotation).toHaveAttribute('contenteditable', 'true');
  await expect(consolePage.editCount).toHaveText('1');
});

test('קונסולה: הערת עורך שורדת מעבר בין טאבים וחזרה', async ({ consolePage, page }) => {
  await consolePage.goto();
  await expect(consolePage.panel('auth').chart).toBeVisible();
  await consolePage.editToggle.click();

  await consolePage.panel('auth').annotation.click();
  await page.keyboard.type(TYPED);

  await consolePage.openPartB();
  await expect(consolePage.panel('mix').chart).toBeVisible();
  await consolePage.openPartA();

  await expect(consolePage.panel('auth').annotation).toHaveText(TYPED);
});

/* בדו״ח הבוררים מוקפאים בזמן עריכה במכוון (פתיחי חלק ב׳ תלויי-הקשר), ולכן
   הדרך שהמשתמש הולך בה היא לערוך → „סיום” → להחליף בורר. הטסט הולך בה. */

test('דו״ח: פתיח שנערך שורד שינוי בורר אוכלוסייה', async ({ reportPage, page }) => {
  await reportPage.goto();
  await reportPage.briefButton('mix').click();
  const lead = reportPage.briefBody('mix').locator('[data-t$=".lead"]');
  await expect(lead).toBeVisible();

  await reportPage.editToggle.click();
  await lead.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.type(TYPED);
  await expect(reportPage.editCount).toHaveText('1');
  await reportPage.endEditing();

  await reportPage.choosePopulation('עצמאים');

  await expect(reportPage.briefBody('mix').locator('[data-t$=".lead"]')).toHaveText(TYPED);
});

test('דו״ח: הערת עורך שורדת שינוי מדד', async ({ reportPage, page }) => {
  await reportPage.goto();
  await expect(reportPage.figureAnnotation('auth')).toBeAttached();

  await reportPage.editToggle.click();
  await reportPage.figureAnnotation('auth').click();
  await page.keyboard.type(TYPED);
  await reportPage.endEditing();

  await reportPage.chooseMetric('מספר שכירים');

  await expect(reportPage.figureAnnotation('auth')).toHaveText(TYPED);
});

test('דו״ח: הבוררים מוקפאים בזמן עריכה, וההקפאה מוסברת', async ({ reportPage }) => {
  await reportPage.goto();
  await reportPage.editToggle.click();
  /* הקפאה בלי הסבר נקראת כתקלה — הסרגל חייב לומר למה. */
  await expect(reportPage.editBar).toContainText('מוקפאים');
  const clickable = await reportPage.metricSegment.getByRole('button', { name: 'מספר שכירים' })
    .evaluate(n => getComputedStyle(n).pointerEvents);
  expect(clickable).toBe('none');
});
