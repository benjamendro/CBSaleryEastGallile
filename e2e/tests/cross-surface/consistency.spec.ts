import { test, expect } from '../../fixtures/base.fixture';
import { ConsolePage } from '../../pages/console.page';
import { ReportPage } from '../../pages/report.page';

/* אורקל Product: אותו נתון בשני משטחים חייב להיות זהה. שני הדפים נבנים
   מאותם data.json ו-btl.json באותה ריצה, ולכן הפרש כאן פירושו באג בנייה. */

/** מושך {שם רשות → ערך} מטבלת רשויות, בלי להניח מבנה מעבר לסדר העמודות. */
async function authoritySalaries(rows: import('@playwright/test').Locator) {
  return rows.evaluateAll(list =>
    Object.fromEntries(list.map(row => {
      const cells = row.querySelectorAll('td');
      return [cells[0].textContent!.trim(), cells[1].textContent!.replace(/[^\d.]/g, '')];
    })));
}

test('ערכי השכר לפי רשות זהים בדו״ח ובקונסולה', async ({ consolePage, browser }) => {
  await consolePage.goto();
  const authPanel = consolePage.panel('auth');
  await authPanel.showTable();
  await expect(authPanel.tableRows).toHaveCount(18);
  const fromConsole = await authoritySalaries(authPanel.tableRows);

  /* הדו״ח נפתח בהקשר משלו ולכן בדף שני, ולא באותו טאב. */
  const second = await browser.newPage();
  const reportPage = new ReportPage(second);
  await reportPage.goto();
  await reportPage.showAuthorityTable();
  await expect(reportPage.authorityTableRows.first()).toBeVisible();
  const fromReport = await authoritySalaries(reportPage.authorityTableRows);
  await second.close();

  const shared = Object.keys(fromConsole).filter(name => name in fromReport);
  expect(shared.length, 'לא הוצלבה אף רשות בין הדפים').toBe(18);
  for (const name of shared) {
    expect(fromConsole[name], `שכר ${name} נבדל בין הדפים`).toBe(fromReport[name]);
  }
});

test('שני הדפים מקשרים זה לזה', async ({ consolePage, reportPage }) => {
  await consolePage.goto();
  await expect(consolePage.reportLink).toHaveAttribute('href', /index\.html|artifact/);
  await reportPage.goto();
  await expect(reportPage.consoleLink).toHaveAttribute('href', /console\.html|artifact/);
});

test('הקונסולה אינה מציגה ערך למ״ס וערך ביטוח לאומי באותו מסך', async ({ consolePage }) => {
  await consolePage.goto();
  await expect(consolePage.sourceTag).toHaveText(/הלמ"ס/);
  await consolePage.openPartB();
  /* הכלל המחייב נאכף מבנית: החלפת טאב מחליפה מקור, KPI ופאנלים יחד. */
  await expect(consolePage.sourceTag).toHaveText(/ביטוח לאומי/);
  await expect(consolePage.panel('auth').title).toHaveCount(0);
  await expect(consolePage.panel('mix').title).toBeVisible();
});

/* ConsolePage מיובא לצורך הטיפוס בלבד במקומות שבהם נוצר דף שני. */
void ConsolePage;
