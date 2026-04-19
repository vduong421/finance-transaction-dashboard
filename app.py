import argparse
import csv
import sqlite3
from collections import defaultdict
from pathlib import Path


CATEGORY_RULES = {
    "food": ["cafe", "restaurant", "pizza", "market"],
    "transport": ["uber", "lyft", "gas", "transit"],
    "software": ["github", "openai", "cloud", "domain"],
    "shopping": ["amazon", "store", "shop"],
}


def categorize(merchant):
    lowered = merchant.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other"


def import_transactions(db, csv_path):
    db.execute(
        """
        create table if not exists transactions (
          id integer primary key,
          date text,
          merchant text,
          amount real,
          category text
        )
        """
    )
    db.execute("delete from transactions")
    with open(csv_path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            db.execute(
                "insert into transactions(date, merchant, amount, category) values (?, ?, ?, ?)",
                (row["date"], row["merchant"], float(row["amount"]), categorize(row["merchant"])),
            )
    db.commit()


def summarize(db):
    by_category = defaultdict(float)
    by_month = defaultdict(float)
    for date, amount, category in db.execute("select date, amount, category from transactions"):
        by_category[category] += amount
        by_month[date[:7]] += amount
    return by_category, by_month


def render_report(by_category, by_month, out_path):
    category_rows = "".join(f"<tr><td>{name}</td><td>${value:.2f}</td></tr>" for name, value in sorted(by_category.items()))
    month_rows = "".join(f"<tr><td>{name}</td><td>${value:.2f}</td></tr>" for name, value in sorted(by_month.items()))
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Finance Transaction Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #17202f; }}
    table {{ border-collapse: collapse; margin-bottom: 24px; min-width: 360px; }}
    td, th {{ border: 1px solid #d9dee8; padding: 8px 10px; text-align: left; }}
  </style>
</head>
<body>
  <h1>Finance Transaction Dashboard</h1>
  <h2>Spend By Category</h2>
  <table><tr><th>Category</th><th>Total</th></tr>{category_rows}</table>
  <h2>Spend By Month</h2>
  <table><tr><th>Month</th><th>Total</th></tr>{month_rows}</table>
</body>
</html>"""
    Path(out_path).write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import transactions and generate a finance report.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", default="report.html")
    args = parser.parse_args()

    db = sqlite3.connect(":memory:")
    import_transactions(db, args.csv)
    render_report(*summarize(db), args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
