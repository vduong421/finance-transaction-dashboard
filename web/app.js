function money(value){
  return "$" + Number(value || 0).toFixed(2)
}

function box(title, value){
  return `<div class="box"><b>${title}</b><div>${value || "-"}</div></div>`
}

function list(items, labelKey, valueKey){
  if(!items || !items.length) return "<p class='muted'>No data</p>"
  return items.map(item => `
    <div class="row">
      <span>${item[labelKey]}</span>
      <strong>${money(item[valueKey])}</strong>
    </div>
  `).join("")
}

function makeChart(title, rows, labelKey, valueKey, targetId){
  if(!rows || !rows.length){
    document.getElementById(targetId).innerHTML = "<p class='muted'>No chart data</p>"
    return
  }

  const max = Math.max(...rows.map(r => r[valueKey]), 1)

  document.getElementById(targetId).innerHTML =
    `<h3>${title}</h3>` +
    rows.map(r => {
      const width = Math.round((r[valueKey] / max) * 100)
      return `
        <div class="chart-row">
          <div class="chart-label">${r[labelKey]}</div>
          <div class="chart-track">
            <div class="chart-bar" style="width:${width}%"></div>
          </div>
          <div class="chart-value">$${Number(r[valueKey]).toFixed(2)}</div>
        </div>
      `
    }).join("")
}

function preset(q){
  document.getElementById("question").value = q
}

async function load(){
  const res = await fetch("/api/data")
  const data = await res.json()
  const s = data.summary
  const ai = data.ai_copilot || {}

  document.getElementById("totalSpend").innerText = money(s.total_spend)
  document.getElementById("txCount").innerText = s.total_transactions
  document.getElementById("avgTx").innerText = money(s.avg_transaction)
  document.getElementById("topCategory").innerText = s.highest_category.category

  document.getElementById("analyst").innerHTML =
    box("Result", ai.result) +
    box("Recommendation", ai.recommendation) +
    box("Decision", ai.decision) +
    box("Executive Summary", ai.executive_summary) +
    box("Top Risks", (ai.top_risks || []).map(x => `<li>${x}</li>`).join("")) +
    box("Operator Actions", (ai.operator_actions || []).map(x => `<li>${x}</li>`).join(""))

  document.getElementById("categories").innerHTML = list(s.category_totals, "category", "total")
  document.getElementById("merchants").innerHTML = list(s.top_merchants, "merchant", "total")
  document.getElementById("months").innerHTML = list(s.monthly_totals, "month", "total")

  makeChart("Category Spend", s.category_totals, "category", "total", "categoryChart")
  makeChart("Monthly Spend", s.monthly_totals, "month", "total", "monthlyChart")
  makeChart("Top Merchants", s.top_merchants, "merchant", "total", "merchantChart")

  document.getElementById("largest").innerHTML = s.top_transactions.map(t => `
    <div class="row">
      <span>${t.merchant}<br><small>${t.date} · ${t.category}</small></span>
      <strong>${money(t.amount)}</strong>
    </div>
  `).join("")

  let rows = `<tr><th>Date</th><th>Merchant</th><th>Category</th><th>Amount</th></tr>`
  s.transactions.forEach(t => {
    rows += `<tr><td>${t.date}</td><td>${t.merchant}</td><td><span class="pill">${t.category}</span></td><td>${money(t.amount)}</td></tr>`
  })
  document.getElementById("transactions").innerHTML = rows
}

async function askAI(){
  const question = document.getElementById("question").value
  document.getElementById("status").innerText = "Running Local AI..."
  document.getElementById("answer").innerHTML = ""

  try {
    const res = await fetch("/api/ask", { method:"POST", body:question })
    const d = await res.json()
    document.getElementById("status").innerText = "Local AI Finished"

    document.getElementById("answer").innerHTML =
      box("Answer", d.answer) +
      box("Evidence", d.evidence) +
      box("Next Action", d.next_action) +
      box("Recommendation", d.recommendation) +
      box("Decision", d.decision) +
      box("Risks", (d.risks || []).map(x => `<li>${x}</li>`).join("")) +
      box("Operator Actions", (d.operator_actions || []).map(x => `<li>${x}</li>`).join(""))
  } catch(e) {
    document.getElementById("status").innerText = "Local AI Failed"
    document.getElementById("answer").innerHTML = box("Fallback", "Could not reach finance AI endpoint.")
  }
}

load()