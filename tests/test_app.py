import sqlite3

from app import categorize, import_transactions, summarize


def test_categorize_merchants():
    assert categorize("OpenAI Cloud") == "software"
    assert categorize("Pizza Market") == "food"
    assert categorize("Unknown Vendor") == "other"


def test_import_transactions_and_summarize(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "date,merchant,amount\n"
        "2026-01-01,OpenAI Cloud,20.50\n"
        "2026-01-02,Pizza Market,12.00\n",
        encoding="utf-8",
    )
    db = sqlite3.connect(":memory:")

    import_transactions(db, csv_path)
    by_category, by_month = summarize(db)

    assert by_category["software"] == 20.50
    assert by_category["food"] == 12.00
    assert by_month["2026-01"] == 32.50
