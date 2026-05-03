import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


CATEGORY_RULES = {
    "food": ["cafe", "restaurant", "pizza", "market", "coffee", "taco", "grocery"],
    "transport": ["uber", "lyft", "gas", "transit", "parking", "rail"],
    "software": ["github", "openai", "cloud", "domain", "notion", "figma", "aws"],
    "shopping": ["amazon", "store", "shop", "target", "best buy"],
    "utilities": ["electric", "water", "internet", "phone"],
    "travel": ["hotel", "airline", "flight", "rental car"],
}

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DEFAULT_CSV = ROOT / "samples" / "transactions.csv"
SHARED = ROOT.parent / "_shared_project_workbench"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

try:
    from local_llm import chat_json
except Exception:
    chat_json = None


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
    rows = list(db.execute("select date, merchant, amount, category from transactions"))
    by_category = defaultdict(float)
    by_month = defaultdict(float)
    by_merchant = defaultdict(float)

    for date, merchant, amount, category in rows:
        by_category[category] += amount
        by_month[date[:7]] += amount
        by_merchant[merchant] += amount

    transactions = [
        {"date": date, "merchant": merchant, "amount": amount, "category": category}
        for date, merchant, amount, category in rows
    ]

    top_transactions = sorted(transactions, key=lambda row: row["amount"], reverse=True)[:5]
    top_merchants = sorted(
        [{"merchant": name, "total": round(total, 2)} for name, total in by_merchant.items()],
        key=lambda row: row["total"],
        reverse=True
    )[:5]
    category_rows = sorted(
        [{"category": name, "total": round(total, 2)} for name, total in by_category.items()],
        key=lambda row: row["total"],
        reverse=True
    )
    month_rows = sorted(
        [{"month": name, "total": round(total, 2)} for name, total in by_month.items()],
        key=lambda row: row["month"]
    )

    total_spend = round(sum(row["amount"] for row in transactions), 2)
    avg_transaction = round(total_spend / len(transactions), 2) if transactions else 0
    highest_category = category_rows[0] if category_rows else {"category": "none", "total": 0}

    return {
        "total_transactions": len(transactions),
        "total_spend": total_spend,
        "avg_transaction": avg_transaction,
        "highest_category": highest_category,
        "category_totals": category_rows,
        "monthly_totals": month_rows,
        "top_merchants": top_merchants,
        "top_transactions": top_transactions,
        "category_counts": dict(Counter(row["category"] for row in transactions)),
        "transactions": transactions,
    }


def build_summary(csv_path=DEFAULT_CSV):
    db = sqlite3.connect(":memory:")
    import_transactions(db, csv_path)
    summary = summarize(db)
    db.close()
    return summary


finance_summary = build_summary()


def fallback_ai_insights():
    highest = finance_summary["highest_category"]
    return {
        "result": f"Analyzed {finance_summary['total_transactions']} transactions with total spend ${finance_summary['total_spend']:.2f}.",
        "recommendation": f"Review {highest['category']} spending first because it is the largest category at ${highest['total']:.2f}.",
        "decision": "Proceed with budget review and prioritize high-spend merchants for follow-up.",
        "executive_summary": f"Average transaction is ${finance_summary['avg_transaction']:.2f}; top category is {highest['category']}.",
        "top_risks": [
            "High category concentration can hide budget creep.",
            "Large individual transactions should be reviewed for necessity.",
            "Uncategorized or other spending may need better merchant rules."
        ],
        "operator_actions": [
            "Review top merchants and top transactions.",
            "Set budget thresholds for highest-spend categories.",
            "Improve categorization rules for other or unclear merchants."
        ],
        "resume_signal": "Built a finance transaction analytics dashboard with deterministic spending summaries and local-AI budget guidance."
    }


def generate_ai_insights(model="google/gemma-4-e4b"):
    if chat_json is None:
        return fallback_ai_insights()

    prompt = f"""You are a finance operations AI analyst.

Return ONLY valid JSON with:
- result
- recommendation
- decision
- executive_summary
- top_risks array of 3
- operator_actions array of 3
- resume_signal

Rules:
- use only deterministic finance summary
- no hallucinated metrics
- be concise and operator-friendly

Finance summary:
{json.dumps(finance_summary, indent=2)}
"""
    try:
        ai = chat_json(prompt, model=model)
        if not isinstance(ai, dict):
            return fallback_ai_insights()
        return {
            "result": ai.get("result", ""),
            "recommendation": ai.get("recommendation", ""),
            "decision": ai.get("decision", ""),
            "executive_summary": ai.get("executive_summary", ""),
            "top_risks": ai.get("top_risks", []),
            "operator_actions": ai.get("operator_actions", []),
            "resume_signal": ai.get("resume_signal", "")
        }
    except Exception:
        return fallback_ai_insights()


ai_copilot = generate_ai_insights()


def answer_question(question, model="google/gemma-4-e4b"):
    q = question.lower()

    fallback = {
        "answer": f"Total spend is ${finance_summary['total_spend']:.2f} across {finance_summary['total_transactions']} transactions.",
        "evidence": f"Average transaction is ${finance_summary['avg_transaction']:.2f}; top category is {finance_summary['highest_category']['category']}.",
        "next_action": "Review top merchants and highest-spend categories.",
        "recommendation": ai_copilot["recommendation"],
        "decision": ai_copilot["decision"],
        "risks": ai_copilot["top_risks"],
        "operator_actions": ai_copilot["operator_actions"],
    }

    if "risk" in q:
        fallback["answer"] = "Main finance risks are category concentration, large transactions, and unclear merchant categories."
        fallback["evidence"] = "; ".join(ai_copilot["top_risks"])
    elif "category" in q:
        fallback["answer"] = "Category totals: " + ", ".join(f"{row['category']}=${row['total']}" for row in finance_summary["category_totals"])
        fallback["evidence"] = "Derived from deterministic merchant categorization rules."
    elif "merchant" in q:
        fallback["answer"] = "Top merchants: " + ", ".join(f"{row['merchant']}=${row['total']}" for row in finance_summary["top_merchants"])
        fallback["evidence"] = "Merchants are ranked by total spend."
    elif "month" in q or "trend" in q:
        fallback["answer"] = "Monthly totals: " + ", ".join(f"{row['month']}=${row['total']}" for row in finance_summary["monthly_totals"])
        fallback["evidence"] = "Monthly spend is grouped by YYYY-MM from transaction dates."
    elif "large" in q or "highest" in q:
        fallback["answer"] = "Largest transactions: " + ", ".join(f"{row['merchant']}=${row['amount']}" for row in finance_summary["top_transactions"])
        fallback["evidence"] = "Transactions are ranked by amount."

    if chat_json is None:
        return fallback

    prompt = f"""You are a finance analytics copilot.

Answer using ONLY deterministic finance summary.

Return ONLY valid JSON with:
- answer
- evidence
- next_action
- recommendation
- decision
- risks array
- operator_actions array

Question:
{question}

Finance summary:
{json.dumps(finance_summary, indent=2)}

AI analyst:
{json.dumps(ai_copilot, indent=2)}
"""
    try:
        response = chat_json(prompt, model=model)
        if not isinstance(response, dict):
            return fallback
        return {
            "answer": response.get("answer", fallback["answer"]),
            "evidence": response.get("evidence", fallback["evidence"]),
            "next_action": response.get("next_action", fallback["next_action"]),
            "recommendation": response.get("recommendation", fallback["recommendation"]),
            "decision": response.get("decision", fallback["decision"]),
            "risks": response.get("risks", fallback["risks"]),
            "operator_actions": response.get("operator_actions", fallback["operator_actions"]),
        }
    except Exception:
        return fallback


def render_report(by_category, by_month, out_path):
    category_rows = "".join(f"<tr><td>{name}</td><td>${value:.2f}</td></tr>" for name, value in sorted(by_category.items()))
    month_rows = "".join(f"<tr><td>{name}</td><td>${value:.2f}</td></tr>" for name, value in sorted(by_month.items()))
    html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Finance Transaction Dashboard</title></head>
<body>
  <h1>Finance Transaction Dashboard</h1>
  <h2>Spend By Category</h2>
  <table><tr><th>Category</th><th>Total</th></tr>{category_rows}</table>
  <h2>Spend By Month</h2>
  <table><tr><th>Month</th><th>Total</th></tr>{month_rows}</table>
</body>
</html>"""
    Path(out_path).write_text(html, encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = "/index.html" if self.path == "/" else self.path
        if path == "/api/data":
            self._send_json({
                "summary": finance_summary,
                "ai_copilot": ai_copilot
            })
            return

        file_path = WEB_ROOT / path.strip("/")
        if file_path.exists():
            self.send_response(200)
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/ask":
            length = int(self.headers.get("Content-Length", 0))
            question = self.rfile.read(length).decode("utf-8")
            self._send_json(answer_question(question))
            return
        self.send_error(404, "Not Found")

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def serve():
    server = HTTPServer(("127.0.0.1", 8007), Handler)
    print("Finance dashboard running at http://127.0.0.1:8007")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Import transactions and generate a finance report.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--out", default="report.html")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    if args.serve:
        serve()
        return

    db = sqlite3.connect(":memory:")
    import_transactions(db, args.csv)
    render_report(*summarize(db), args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
