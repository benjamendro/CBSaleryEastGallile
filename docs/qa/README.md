# בדיקות ממשק

שני קובצי מיומנויות הובאו לפרויקט: `playwright-automation` (סוויטה מתוחזקת)
ו-`exploratory-testing` (סשני חקר). זהו התיעוד של מה שהופעל בפועל.

## הרצה

```bash
npm install                    # פעם אחת
export PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers   # בסביבת הריצה של הפרויקט

npm run test:e2e               # כל הסוויטה
npm run test:e2e -- regression/  # רגרסיות בלבד
npm run test:e2e:ui            # מצב UI, צעד-צעד
npm run typecheck              # tsc --noEmit
```

`playwright.config.ts` מרים `http-server` על `dashboard/` בעצמו — אין צורך
להפעיל שרת ידנית.

## מה בפנים

```
e2e/
├── fixtures/base.fixture.ts        הזרקת אובייקטי הדף
├── pages/
│   ├── base.page.ts                goto + פקדי העריכה המשותפים
│   ├── console.page.ts             טאבים, פילטרים, KPI, פאנלים
│   ├── report.page.ts              מגירות, מורה נבוכים, בוררי הקשר
│   └── components/panel.ts         פאנל בודד בקונסולה
├── helpers/sites.ts                שני ה„אתרים” והקבועים
└── tests/
    ├── a11y/                       סריקת axe + הצהרת שפה וכיוון
    ├── console/                     מטריצת מצב · התנהגות פאנל · RTL ומספרים
    ├── report/                      מגירות ומורה נבוכים
    ├── cross-surface/               אותו נתון בשני הדפים
    └── regression/                  באגים שנמצאו בחקר
```

## מה לא מיושם, ולמה

`playwright-automation` מניח אפליקציה עם שרת, API והתחברות. הדשבורד הוא שני
קובצי HTML סטטיים. שלושה חלקים מהמיומנות **אינם רלוונטיים ולא מומשו**, וזו
החלטה ולא השמטה:

| חלק במיומנות | למה לא |
|---|---|
| `storageState`, אימות רב-תפקידי | אין משתמשים ואין התחברות |
| `page.route`, מוקים, HAR | אין קריאות רשת — הנתונים מוטמעים בקובץ |
| שרדינג ב-CI, מטריצת דפדפנים | `team_maturity: startup`; Chromium הוא הדפדפן היחיד בסביבה |

מה שכן אומץ במלואו: POM עם component objects, פיקסצ׳רים במקום hooks, לוקטורים
פונים-למשתמש, המתנה אוטומטית בלבד, `fullyParallel`, ואכיפת „אל תעשה” ב-lint.

## הכלל שהכי חשוב כאן

**לחיצה שנבדקת חייבת להיות לחיצה אמיתית.** ארבעה ליקויי נגישות חמקו מסשן החקר
הראשון מפני שהוא הפעיל פקדים ב-`element.click()` מתוך JavaScript, שעוקף את
בדיקת ה-hit-testing של הדפדפן. משתמש עם עכבר אינו עוקף אותה. הפירוט:
`docs/qa/exploratory-sessions.md`, סבב 2.

## סשני החקר

הצ׳רטרים, יומן הסשן, הבאגים והדיברוף: `docs/qa/exploratory-sessions.md`.
הקשר הפרויקט (תשובות הגילוי, אזורי סיכון): `.agents/qa-project-context.md`.
