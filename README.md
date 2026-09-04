# CBSaleryEastGallile

דשבורד שכר ותעסוקה של **מרכז הידע האזורי גליל מזרחי | מערבי** — 18 הרשויות שבנפות צפת
וגולן, על נתוני הלשכה המרכזית לסטטיסטיקה והביטוח הלאומי.

- **הדשבורד:** [`dashboard/index.html`](dashboard/index.html) — קובץ HTML עצמאי אחד
- **תיעוד למשתמש:** [`dashboard/README.md`](dashboard/README.md)
- **הקשר לפיתוח והמלכודות שבנתונים:** [`CLAUDE.md`](CLAUDE.md)
- **שילוב נתוני הביטוח הלאומי:** [`docs/btl-integration.md`](docs/btl-integration.md)

## בנייה

```bash
pip install openpyxl Pillow
python3 dashboard/build_data.py
python3 dashboard/build.py
```
