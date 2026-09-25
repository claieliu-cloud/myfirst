#!/usr/bin/env python3
"""依學科關鍵字自動分類期刊名稱。

用法:
    python classify_journals.py journals.csv
    python classify_journals.py journals.csv -o result.csv --column journal_name

分類規則:
    - 每個學科有一組關鍵字（字首比對、不分大小寫，例如 "chem" 可比對
      Chemistry / Chemical / Chemie）。
    - 多字關鍵字（例如 "machine learning"）權重較高，依字數計分。
    - 分數最高的學科為主分類；其他有命中的學科列為次要分類。
    - 同分時依 CATEGORIES 中的先後順序決定。
    - 完全沒命中者歸類為「未分類」。
"""

import argparse
import csv
import re
import sys
from collections import Counter

UNCLASSIFIED = "未分類"

# 學科 -> 關鍵字（字首比對）。順序即同分時的優先順序。
CATEGORIES = {
    "醫學": [
        "medicine", "medical", "clinical", "oncolog", "lancet", "cancer",
        "surgery", "cardiolog", "patholog", "pharmac", "nursing", "health",
    ],
    "生命科學": [
        "cell", "biolog", "genetic", "genom", "molecular", "evolution",
        "biochem", "neuroscien", "microbio", "immunolog",
    ],
    "資訊科學": [
        "comput", "software", "machine learning", "machine intelligence",
        "artificial intelligence", "pattern analysis", "information system",
        "data mining", "acm",
    ],
    "工程": [
        "engineer", "civil", "mechanical", "electrical", "design",
        "robotic", "materials",
    ],
    "物理與天文": [
        "physic", "astrophysic", "astronom", "optic", "quantum",
    ],
    "化學": [
        "chem", "catalys", "polymer",
    ],
    "數學與統計": [
        "mathemat", "statistic", "probabilit", "algebra", "geometr",
    ],
    "環境與地球科學": [
        "environment", "ecolog", "climate", "geolog", "geophysic",
        "earth", "ocean", "atmospher",
    ],
    "教育": [
        "educat", "teaching", "learning and instruction", "pedagog",
    ],
    "心理學": [
        "psycholog",
    ],
    "經濟與財務": [
        "econom", "financ", "accounting", "monetary",
    ],
    "商管": [
        "management", "marketing", "business", "organization",
    ],
    "社會科學": [
        "sociolog", "political", "anthropolog", "social",
    ],
    "法律": [
        "law", "legal", "juris",
    ],
    "人文": [
        "history", "historical", "philosoph", "literat", "linguistic",
        "asian studies", "african studies", "european studies", "religio",
    ],
}

NAME_COLUMN_CANDIDATES = ["journal_name", "journal", "name", "title", "期刊名稱", "期刊"]


def compile_patterns(categories):
    """把關鍵字編譯成 (學科, 關鍵字, 權重, regex) 清單。"""
    patterns = []
    for category, keywords in categories.items():
        for kw in keywords:
            regex = re.compile(r"\b" + re.escape(kw).replace(r"\ ", r"\s+"), re.IGNORECASE)
            patterns.append((category, kw, len(kw.split()), regex))
    return patterns


PATTERNS = compile_patterns(CATEGORIES)
CATEGORY_ORDER = {c: i for i, c in enumerate(CATEGORIES)}


def classify(name):
    """回傳 (主分類, 次要分類清單, 命中關鍵字清單)。"""
    scores = Counter()
    matched = []
    for category, kw, weight, regex in PATTERNS:
        if regex.search(name):
            scores[category] += weight
            matched.append(kw)
    if not scores:
        return UNCLASSIFIED, [], []
    ranked = sorted(scores, key=lambda c: (-scores[c], CATEGORY_ORDER[c]))
    return ranked[0], ranked[1:], matched


def detect_name_column(fieldnames, preferred=None):
    if preferred:
        if preferred not in fieldnames:
            raise SystemExit(f"找不到欄位 '{preferred}'，可用欄位: {', '.join(fieldnames)}")
        return preferred
    lowered = {f.strip().lower(): f for f in fieldnames}
    for cand in NAME_COLUMN_CANDIDATES:
        if cand in lowered:
            return lowered[cand]
    return fieldnames[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description="依學科關鍵字自動分類期刊名稱")
    parser.add_argument("input", help="輸入 CSV 檔")
    parser.add_argument("-o", "--output", default="journals_classified.csv",
                        help="輸出 CSV 檔（預設: journals_classified.csv）")
    parser.add_argument("-c", "--column", help="期刊名稱欄位（預設自動偵測）")
    args = parser.parse_args(argv)

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("輸入檔是空的或沒有標題列")
        fieldnames = list(reader.fieldnames)
        name_col = detect_name_column(fieldnames, args.column)
        rows = list(reader)

    out_fields = fieldnames + ["category", "secondary_categories", "matched_keywords"]
    summary = Counter()
    for row in rows:
        primary, secondary, matched = classify(row.get(name_col) or "")
        row["category"] = primary
        row["secondary_categories"] = "; ".join(secondary)
        row["matched_keywords"] = "; ".join(matched)
        summary[primary] += 1

    # utf-8-sig 讓 Excel 開啟時中文不亂碼
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows)

    width = max((len(r.get(name_col) or "") for r in rows), default=10)
    for row in rows:
        extra = f"  (另: {row['secondary_categories']})" if row["secondary_categories"] else ""
        print(f"{row[name_col]:<{width}}  →  {row['category']}{extra}")

    print(f"\n共 {len(rows)} 筆，已輸出至 {args.output}")
    print("分類統計:")
    for category, count in sorted(summary.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {category}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
