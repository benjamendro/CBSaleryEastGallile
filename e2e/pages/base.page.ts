import { type Page, type Locator } from '@playwright/test';

export abstract class BasePage {
  constructor(protected readonly page: Page) {}
  abstract readonly path: string;

  async goto(): Promise<void> {
    /* ‏'load' ממתין גם לגיליון הפונטים של Google, שאינו נענה בסביבה ללא רשת
       ומפיל את הניווט בטיימאאוט. הדף אינו תלוי בו — יש לו מחסנית גיבוי —
       ולכן ההמתנה היא ל-DOM. סימן המוכנות האמיתי הוא ה-assertion הראשון על
       גרף או טבלה, שממתין אוטומטית; אין כאן השהיה קבועה. */
    await this.page.goto(this.path, { waitUntil: 'domcontentloaded' });
  }

  /** כפתור מצב העריכה, משותף לשני הדפים. */
  get editToggle(): Locator {
    return this.page.locator('#editToggle');
  }
  get editCount(): Locator {
    return this.page.locator('#editCount');
  }
  get editBar(): Locator {
    return this.page.locator('#editbar');
  }
  /** כל צומת טקסט שניתן לעריכה, לפי מזהה יציב. */
  editable(id: string): Locator {
    return this.page.locator(`[data-t="${id}"]`);
  }
}
