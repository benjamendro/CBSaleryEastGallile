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
  /** בורר „בתמהיל” קיים רק בתצוגת „לאורך זמן”. */
  get mixModeGroup(): Locator { return this.filterGroup('בתמהיל'); }

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
