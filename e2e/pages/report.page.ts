import { type Page, type Locator } from '@playwright/test';
import { BasePage } from './base.page';
import { SITES } from '../helpers/sites';

type Section = 'auth' | 'change' | 'anaf' | 'mix' | 'dist' | 'trend';

export class ReportPage extends BasePage {
  readonly path = SITES.report.path;

  constructor(page: Page) { super(page); }

  /* --- מורה נבוכים --- */
  get guide(): Locator      { return this.page.locator('#sec-guide'); }
  get guideCards(): Locator { return this.page.locator('#guideGrid .guide-card'); }

  /* --- מגירות --- */
  briefButton(sec: Section): Locator {
    return this.page.locator(`button.dbtn[data-open="b-${sec}"]`);
  }
  insightsButton(sec: Section): Locator {
    return this.page.locator(`button.dbtn[data-open="i-${sec}"]`);
  }
  briefBody(sec: Section): Locator    { return this.page.locator(`#b-${sec}`); }
  insightsBody(sec: Section): Locator { return this.page.locator(`#i-${sec}`); }

  /* --- בוררי ההקשר ---
     שני הסרגלים לעולם אינם גלויים יחד: „מדד להצגה” שייך לחלק א׳, ו„אוכלוסייה”
     לחלק ב׳, וההחלפה תלויה במיקום הגלילה. לכן כל שימוש בבורר מתחיל בהבאת החלק
     שלו למסך — בדיוק מה שמשתמש עושה — ולא בלחיצה על סרגל שעדיין אינו בהקשר. */
  private async bringIntoContext(anchor: string): Promise<void> {
    await this.page.locator(anchor).scrollIntoViewIfNeeded();
  }

  async chooseMetric(name: string): Promise<void> {
    await this.bringIntoContext('#sec-auth');
    await this.page.locator('#metricSeg').getByRole('button', { name, exact: true }).click();
  }
  async choosePopulation(name: string): Promise<void> {
    await this.bringIntoContext('#sec-mix');
    await this.page.locator('#btlPop').getByRole('button', { name, exact: true }).click();
  }
  async chooseBtlMode(name: string): Promise<void> {
    await this.bringIntoContext('#sec-mix');
    await this.page.locator('#btlMode').getByRole('button', { name, exact: true }).click();
  }

  /* --- מקטעים --- */
  section(sec: Section): Locator { return this.page.locator(`#sec-${sec}`); }
  figureAnnotation(sec: Section): Locator { return this.section(sec).locator('.fig-anno'); }
  figureNote(sec: Section): Locator { return this.section(sec).locator('.fig-note'); }
  get figureFooters(): Locator { return this.page.locator('.fig-foot'); }

  /** טבלת הרשויות — הטוגל הראשון בעמוד שייך למקטע הזה. */
  showAuthorityTable(): Promise<void> {
    return this.section('auth').getByRole('button', { name: 'טבלה', exact: true }).click();
  }
  get authorityTableRows(): Locator {
    return this.section('auth').locator('tbody tr');
  }

  /** סרגל הבוררים של חלק א׳. */
  get metricSegment(): Locator { return this.page.locator('#metricSeg'); }

  /** יציאה ממצב עריכה — הבוררים מוקפאים עד שיוצאים. */
  endEditing(): Promise<void> {
    return this.page.getByRole('button', { name: 'סיום' }).click();
  }

  /** קישור לקונסולת ה-BI. */
  get consoleLink(): Locator { return this.page.getByRole('link', { name: /קונסולת BI/ }); }
}
