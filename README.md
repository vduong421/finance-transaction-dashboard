# Finance Transaction Dashboard

Finance Transaction Dashboard is a local finance-operations tool that categorizes transactions, summarizes spending patterns, flags budget risk, and uses a local AI analyst to explain financial trends.

The deterministic dashboard provides the numbers; the AI analyst converts those numbers into business-readable insight and recommended follow-up.

## What It Does

- Loads transaction records from local sample data.
- Categorizes spending by merchant, account, and expense type.
- Computes budget totals, category totals, and unusual activity signals.
- Displays metrics in a browser dashboard.
- Adds an AI analyst summary for operational review.

## AI Features

- Local AI analyst explains budget pressure and spending movement.
- AI guidance is grounded in deterministic transaction totals.
- Highlights categories or accounts needing follow-up.
- Produces concise finance-operations recommendations.

## Architecture

```text
Transaction data
      |
      v
Categorization + aggregation + anomaly flags
      |
      v
Local AI analyst -> finance summary + recommended action
      |
      v
Browser dashboard
```

## Run

```powershell
run.bat
```

## Local AI Setup

- Default local model target: `google/gemma-4-e4b`.
- Compatible with LM Studio or another OpenAI-compatible local server.
- The core dashboard works without AI.

## Main Files

- `app.py` - transaction analytics and AI insight generation.
- `web/index.html` - dashboard UI.
- `agents/Agent.md` - AI analyst role instructions.
- `samples/` - local transaction data.

## Output

The app shows transaction totals, category summaries, risk notes, and AI-generated finance guidance.
