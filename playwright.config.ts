import { defineConfig, devices } from '@playwright/test';

/* הדשבורד הוא שני קובצי HTML סטטיים ללא build step, ללא API וללא התחברות.
   מכאן שלוש חריגות מכוונות מתבנית הברירה של playwright-automation, ומתועדות
   ב-.agents/qa-project-context.md: אין storageState (אין משתמשים), אין
   page.route (אין רשת), ואין npm run dev — http-server מגיש את dashboard/
   כדי ש-baseURL ו-toHaveURL יעבדו כרגיל ולא מול file://. */

const isCI = !!process.env.CI;
const PORT = Number(process.env.PORT ?? 4173);
const baseURL = process.env.BASE_URL ?? `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? '50%' : undefined,
  reporter: isCI
    ? [['blob'], ['github'], ['json', { outputFile: 'test-results/results.json' }]]
    : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL,
    locale: 'he-IL',
    trace: isCI ? 'on-first-retry' : 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: isCI ? 'on-first-retry' : 'off',
    navigationTimeout: 30_000,
  },
  /* Chromium בלבד — הדפדפן היחיד המותקן בסביבה, ו-team_maturity: startup
     ממילא ממליץ על כך. Firefox/WebKit ייכנסו כשתהיה סביבת CI שמתקינה אותם. */
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: `http-server dashboard -p ${PORT} -s -c-1 --host 127.0.0.1`,
    url: baseURL,
    reuseExistingServer: !isCI,
    timeout: 60_000,
  },
});
