import { type Page, type Locator } from '@playwright/test';
import { BasePage } from './base.page';
import { Panel } from './components/panel';
import { SITES } from '../helpers/sites';

export class ConsolePage extends BasePage {
  readonly path = SITES.console.path;

  constructor(page: Page) { super(page); }

  /* --- טאבים --- */
  get tabA(): Locator { return this.page.locator('#tabA'); }
  get tabB(): Locator { return this.page.locator('#tabB'); }
  openPartA(): Promise<void> { return this.tabA.click(); }
  openPartB(): Promise<void> { return this.tabB.click(); }

  /* --- תגי הקשר --- */
  get sourceTag(): Locator     { return this.page.locator('#ctxSrc'); }
  get populationTag(): Locator { return this.page.locator('#ctxPop'); }
  get yearTag(): Locator       { return this.page.locator('#ctxYear'); }

  /* --- סרגל הפילטרים --- */
  get filterBar(): Locator { return this.page.locator('#fbar'); }
  private filterGroup(label: string): Locator {
    return this.filterBar.locator('.fg').filter({ has: this.page.locator('label', { hasText: label }) });
  }
  /** בוחר אופציה בבורר מקוטע לפי שם התווית ושם האופציה. */
  chooseSegment(label: string, option: string): Promise<void> {
    return this.filterGroup(label).getByRole('button', { name: option, exact: true }).click();
  }
  /** בוחר ערך בבורר נפתח לפי שם התווית. */
  chooseSelect(label: string, value: string): Promise<string[]> {
    return this.filterGroup(label).getByRole('combobox').selectOption({ label: value });
  }
  selectValue(label: string): Locator { return this.filterGroup(label).getByRole('combobox'); }
  /* --- פקדים שיושבים בתוך פאנל ולא בסרגל הגלובלי ---
     „תקופה” ו„מציג” שייכים לפאנל התמהיל בלבד, ובחירת הרשות שייכת לפאנל
     הענפים בלבד. סרגל גלובלי מחזיק רק את מה שחל על כל הפאנלים. */

  /** בורר התקופה של פאנל התמהיל: 2024 · לאורך זמן. */
  choosePeriod(option: '2024' | 'לאורך זמן'): Promise<void> {
    return this.page.locator('#panel-mix .vtog[aria-label="תקופה"]')
      .getByRole('button', { name: option, exact: true }).click();
  }
  /** בורר „מציג” — קיים רק בתצוגת „לאורך זמן”. */
  get mixModeGroup(): Locator {
    return this.page.locator('#panel-mix .vtog[aria-label="מציג"]');
  }
  chooseMixMode(option: 'הרכב' | 'מספר עובדים'): Promise<void> {
    return this.mixModeGroup.getByRole('button', { name: option, exact: true }).click();
  }
  /** בורר הרשות של פאנל הענפים. */
  get anafAuthority(): Locator {
    return this.page.locator('#panel-anaf').getByRole('combobox', { name: 'רשות בגרף הענפים' });
  }
  /** בורר הענפים הידני שבתוך פאנל הענפים. */
  get anafPicker(): Locator { return this.page.locator('#panel-anaf .picker'); }
  get anafPickerSummary(): Locator { return this.anafPicker.locator('summary'); }
  get anafPickerSearch(): Locator { return this.anafPicker.getByRole('searchbox'); }
  get anafPickerOptions(): Locator { return this.anafPicker.locator('.pk-list label'); }
  openAnafPicker(): Promise<void> { return this.anafPickerSummary.click(); }

  /* --- KPI --- */
  get kpiCards(): Locator  { return this.page.locator('.kpi'); }
  get kpiValues(): Locator { return this.page.locator('.kpi .v'); }

  /* --- פאנלים --- */
  panel(id: 'auth' | 'change' | 'anaf' | 'mix' | 'dist' | 'trend'): Panel {
    return new Panel(this.page.locator(`#panel-${id}`));
  }
  get allPanels(): Locator { return this.page.locator('.panel'); }

  /* --- ייצוא --- */
  get exportToggle(): Locator { return this.page.getByRole('button', { name: 'ייצוא', exact: true }); }
  get exportMenu(): Locator   { return this.page.locator('#exportMenu'); }

  /** קישור לדו״ח המלא. */
  get reportLink(): Locator { return this.page.locator('#reportLink'); }
}
