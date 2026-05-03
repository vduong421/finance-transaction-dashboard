# Finance Transaction Dashboard

A Python analytics app that imports transaction CSV data into SQLite, categorizes spending, and generates an HTML spending report.

## What It Does

- Imports CSV transaction data into a local SQLite database.
- Applies merchant/category rules for spending analysis.
- Produces monthly and category-level summaries.
- Generates a browser-readable HTML report for review.

## Run

```powershell
python app.py --csv samples/transactions.csv --out report.html
```

Open `report.html` in your browser.

## Engineering Value

- Models a small finance/product data workflow with ingestion, persistence, transformation, and reporting.
- Can be extended into a backend API, scheduled reporting job, or internal analytics dashboard.
- Useful for product analytics, fintech tooling, and lightweight operational reporting.

## Project Workbench

Launch the production-style desktop workbench with:

```powershell
launch-workbench.bat
```

What it adds:

- Local-first AI copilot using `google/gemma-4-e4b` by default
- Operator-focused workbench for reviewing real project inputs and outputs
- System design, production-impact, and operational brief generation on demand
- Grounded responses based on this project's README, sample files, and deterministic outputs
