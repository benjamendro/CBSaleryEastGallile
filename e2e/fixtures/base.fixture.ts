import { test as base } from '@playwright/test';
import { ConsolePage } from '../pages/console.page';
import { ReportPage } from '../pages/report.page';

/* הזרקת אובייקטי הדף דרך פיקסצ׳רים, לא דרך new בגוף הטסט.
   כל פיקסצ׳ר עומד בפני עצמו ואינו תלוי בסדר ריצה. */
type Pages = { consolePage: ConsolePage; reportPage: ReportPage };

export const test = base.extend<Pages>({
  consolePage: async ({ page }, use) => { await use(new ConsolePage(page)); },
  reportPage:  async ({ page }, use) => { await use(new ReportPage(page)); },
});

export { expect } from '@playwright/test';
