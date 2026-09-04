import { type Locator } from '@playwright/test';

/** פאנל בקונסולה. מקבל Locator שורש ולא Page, כדי שיהיה בר-שימוש חוזר. */
export class Panel {
  constructor(private readonly root: Locator) {}

  get title(): Locator    { return this.root.getByRole('heading', { level: 2 }); }
  get subtitle(): Locator { return this.root.locator('.psub'); }
  get body(): Locator     { return this.root.locator('.p-body'); }
  get chart(): Locator    { return this.root.locator('.p-body svg'); }
  get table(): Locator    { return this.root.getByRole('table'); }
  get tableRows(): Locator{ return this.root.locator('.p-body tbody tr'); }
  get emptyNote(): Locator{ return this.root.locator('.p-empty'); }
  get legendItems(): Locator { return this.root.locator('.legend .it'); }
  get warning(): Locator  { return this.root.locator('.warn'); }
  get source(): Locator   { return this.root.locator('.p-foot .src'); }
  get annotation(): Locator { return this.root.locator('.p-anno'); }
  get exportButton(): Locator {
    return this.root.getByRole('button', { name: /ייצוא תמונה|מייצא|ירד|הועתק|לא ניתן/ });
  }

  /** מחליף בין תצוגת גרף לתצוגת טבלה. */
  showChart(): Promise<void> { return this.root.getByRole('button', { name: 'גרף',  exact: true }).click(); }
  showTable(): Promise<void> { return this.root.getByRole('button', { name: 'טבלה', exact: true }).click(); }

  /** עמודה n בגרף — ללחיצה שמסנכרנת פילטרים. אין assert כאן. */
  bar(index = 0): Locator { return this.root.locator('.p-body svg rect[fill]').nth(index); }

  /** בוררים מקומיים בכותרת הפאנל (קיימים בפאנל הענפים בלבד). */
  localSelect(index = 0): Locator { return this.root.locator('select.loc').nth(index); }
  get rangeSelect(): Locator   { return this.root.getByRole('combobox', { name: 'טווח הענפים המוצג' }); }
  get clusterSelect(): Locator { return this.root.getByRole('combobox', { name: 'קיבוץ ענפים' }); }
}
