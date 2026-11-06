def percentage_table_script(table_data_json: str) -> str:
    table_data_json = table_data_json.replace("</", "<\\/")
    return """
<style>
.ipp-sync-table { margin-top:14px; overflow-x:auto; font-family:Segoe UI,Arial,sans-serif; }
.ipp-sync-table table { width:100%; border-collapse:collapse; table-layout:fixed; font-size:13px; }
.ipp-sync-table th,.ipp-sync-table td { padding:7px 12px; border-bottom:1px solid #E8E8E8; }
</style>
<div class="ipp-sync-table">
  <h3>Forecast / Actuals percentage</h3>
  <table>
    <thead><tr id="ipp-table-header"><th>Forecast / Actuals</th></tr></thead>
    <tbody id="ipp-table-body"></tbody>
  </table>
</div>
<script>
(function () {
  const tableData = """ + table_data_json + """;
  let range = null;

  function rebuildTable() {
    const header = document.getElementById("ipp-table-header");
    const body = document.getElementById("ipp-table-body");
    if (!header || !body || !range) return;
    const start = Number(range.start), end = Number(range.end);
    const visible = tableData.months.filter(month =>
      month.timestamp >= start - 43200000 &&
      month.timestamp <= end + 43200000
    );
    header.innerHTML = '<th>Forecast / Actuals</th>';
    for (const month of visible) {
      const cell = document.createElement("th");
      cell.style.textAlign = "right";
      cell.textContent = new Date(month.timestamp).toLocaleDateString("en-US", {
        month: "short", year: "numeric", timeZone: "UTC"
      });
      header.appendChild(cell);
    }
    body.innerHTML = "";
    for (const row of tableData.rows) {
      const show = row.label === "Actuals" || visible.some(month =>
        Object.prototype.hasOwnProperty.call(row.cells, month.key) &&
        row.cells[month.key] !== "—"
      );
      if (!show) continue;
      const tr = document.createElement("tr");
      const label = document.createElement("td");
      label.textContent = row.label;
      label.style.fontWeight = row.label === "Actuals" ? "600" : "400";
      tr.appendChild(label);
      for (const month of visible) {
        const cell = document.createElement("td");
        cell.style.textAlign = "right";
        const value = row.cells[month.key] || "—";
        cell.textContent = value;
        if (value !== "—") {
          const numericValue = Number.parseFloat(value);
          if (Number.isFinite(numericValue) &&
              (numericValue > 104 || numericValue < 96)) {
            cell.style.color = "#C74634";
            cell.style.fontWeight = "700";
          }
        }
        tr.appendChild(cell);
      }
      body.appendChild(tr);
    }
  }

  function initializeTable() {
    if (!window.Bokeh || !window.Bokeh.documents) return false;
    for (const doc of window.Bokeh.documents) {
      for (const model of doc.roots()) {
        if (model.x_range) { range = model.x_range; break; }
      }
      if (range) break;
    }
    if (!range) return false;
    rebuildTable();
    let lastStart = Number(range.start), lastEnd = Number(range.end);
    setInterval(() => {
      const nextStart = Number(range.start), nextEnd = Number(range.end);
      if (nextStart !== lastStart || nextEnd !== lastEnd) {
        lastStart = nextStart; lastEnd = nextEnd; rebuildTable();
      }
    }, 200);
    return true;
  }

  let attempts = 0;
  const timer = setInterval(() => {
    if (initializeTable() || ++attempts >= 100) clearInterval(timer);
  }, 50);
})();
</script>
"""
