import { test, expect } from '../../fixtures/base.fixture';
import { METRICS, POPULATIONS, AUTHORITY_WITHOUT_2016_BASE } from '../../helpers/sites';

/* מטריצת המצב היא אזור הסיכון הראשון: 3 מדדים בחלק א׳, ו-3 אוכלוסיות ×
   2 תצוגות × 2 מצבי תמהיל בחלק ב׳. כל צירוף חייב לצייר משהו — גרף, טבלה,
   או הודעת „אין נתון” מפורשת. פאנל ריק בלי הודעה הוא כישלון. */

test.describe('חלק א׳ · הלמ"ס', () => {
  for (const metric of METRICS) {
    test(`מדד „${metric}” — שלושת הפאנלים מציגים תוכן`, async ({ consolePage }) => {
      await consolePage.goto();
      await consolePage.chooseSegment('מדד להצגה', metric);

      await expect(consolePage.allPanels).toHaveCount(3);
      for (const id of ['auth', 'change', 'anaf'] as const) {
        const p = consolePage.panel(id);
        await expect(p.title).toBeVisible();
        /* „חודשי עבודה” אינו קיים בקובץ 2022, ולכן פאנל השינוי מציג הודעה
           מפורשת במקום גרף — זו התנהגות נכונה, לא כשל. */
        const hasContent = (await p.chart.count()) + (await p.emptyNote.count());
        expect(hasContent, `פאנל ${id} במדד ${metric} לא צייר דבר`).toBeGreaterThan(0);
      }
    });
  }

  test('„חודשי עבודה” מסביר למה אין גרף שינוי, ולא נשאר ריק', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.chooseSegment('מדד להצגה', 'חודשי עבודה');
    await expect(consolePage.panel('change').emptyNote).toContainText('אין בו ממוצע חודשי עבודה');
    await expect(consolePage.panel('change').chart).toHaveCount(0);
  });

  test('קווי הייחוס מוצגים במדד השכר בלבד', async ({ consolePage }) => {
    await consolePage.goto();
    await expect(consolePage.panel('auth').subtitle).toContainText('עם קווי ייחוס');
    await consolePage.chooseSegment('מדד להצגה', 'שכירים');
    await expect(consolePage.panel('auth').subtitle).toContainText('ללא קווי ייחוס');
  });
});

test.describe('חלק ב׳ · ביטוח לאומי', () => {
  for (const pop of POPULATIONS) {
    test(`אוכלוסייה „${pop}” — 2024 ולאורך זמן`, async ({ consolePage }) => {
      await consolePage.goto();
      await consolePage.openPartB();
      await consolePage.chooseSegment('אוכלוסייה', pop);

      for (const view of ['2024', 'לאורך זמן'] as const) {
        await consolePage.choosePeriod(view);
        for (const id of ['mix', 'dist', 'trend'] as const) {
          const p = consolePage.panel(id);
          const drawn = (await p.chart.count()) + (await p.emptyNote.count());
          expect(drawn, `${pop}/${view}: פאנל ${id} לא צייר דבר`).toBeGreaterThan(0);
          await expect(p.body).not.toContainText(/NaN|undefined|Infinity/);
        }
      }
    });
  }

  test('בורר „מציג” מופיע רק בתצוגת לאורך זמן', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    await expect(consolePage.mixModeGroup).toHaveCount(0);
    await consolePage.choosePeriod('לאורך זמן');
    await expect(consolePage.mixModeGroup).toBeVisible();
    await consolePage.choosePeriod('2024');
    await expect(consolePage.mixModeGroup).toHaveCount(0);
  });

  test('הסרגל הגלובלי מחזיק רק פקדים שחלים על כל הפאנלים', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    /* „תקופה” ו„מציג” ירדו לפאנל התמהיל אחרי הסידור מחדש: מגמת השכר תמיד
       לאורך זמן וההתפלגות תמיד 2024, ולכן הם נוגעים לפאנל אחד בלבד. */
    const labels = await consolePage.filterBar.locator('.fg > label').allTextContents();
    expect(labels.map(t => t.trim())).toEqual(['אוכלוסייה', 'יחידה']);
  });

  test('מגמת השכר היא הפאנל הראשון, ברוחב מלא, ותמיד לאורך זמן', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    const titles = await consolePage.allPanels.locator('h2').allTextContents();
    expect(titles[0]).toContain('מגמת השכר לאורך זמן');
    expect(titles).toEqual(['מגמת השכר לאורך זמן', 'תמהיל התעסוקה', 'התפלגות השכר']);
    /* „ממוצע מול חציון” הוסר מהקונסולה והוא נשאר בדו״ח. */
    await consolePage.choosePeriod('2024');
    await expect(consolePage.panel('trend').subtitle).toContainText('2016–2024');
  });

  test('„כלל העובדים” לאורך זמן אינו מציג שיעור טאוטולוגי', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    await consolePage.chooseSegment('אוכלוסייה', 'כלל העובדים');
    await consolePage.choosePeriod('לאורך זמן');
    /* „שיעור כלל העובדים מכלל העובדים” הוא 100% בהגדרה. באוכלוסייה הזו
       הפאנל חייב להציג את ההרכב עצמו. */
    await expect(consolePage.panel('mix').subtitle).not.toContainText('מכלל העובדים');
    await expect(consolePage.panel('mix').subtitle).toContainText('הרכב העובדים');
  });

  test('מצב „מספר עובדים” מצהיר על סדרה שאין לה בסיס 2016', async ({ consolePage }) => {
    await consolePage.goto();
    await consolePage.openPartB();
    await consolePage.choosePeriod('לאורך זמן');
    await consolePage.chooseMixMode('מספר עובדים');
    await expect(consolePage.panel('mix').warning)
      .toContainText(AUTHORITY_WITHOUT_2016_BASE);
  });
});
