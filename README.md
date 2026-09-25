# myfirst
## 期刊學科分類腳本

`classify_journals.py` 讀取期刊名稱 CSV，依學科關鍵字自動分類。

```bash
python3 classify_journals.py journals.csv -o journals_classified.csv
```

- 自動偵測名稱欄位（`journal_name` / `journal` / `name` / `title` …），或用 `--column` 指定
- 輸出新增三欄：`category`（主分類）、`secondary_categories`（次要分類）、`matched_keywords`
- 沒命中任何關鍵字者標為「未分類」；要新增學科或關鍵字，編輯腳本中的 `CATEGORIES` 即可
