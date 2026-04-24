// DataTable.jsx — Renders structured product data returned by MCP tools

export default function DataTable({ data }) {
  if (!data || data.length === 0) return null

  // Exclude internal/less useful fields from display
  const exclude = new Set()
  const columns = Object.keys(data[0]).filter(k => !exclude.has(k))

  const formatCell = (key, val) => {
    if (key === 'stock') {
      const low = Number(val) < 10
      return (
        <span className={`stock-badge ${low ? 'stock-low' : 'stock-ok'}`}>
          {val}
        </span>
      )
    }
    if (key === 'price') return `₹${Number(val).toFixed(2)}`
    return val ?? '—'
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col}>{col.replace(/_/g, ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {columns.map(col => (
                <td key={col}>{formatCell(col, row[col])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
