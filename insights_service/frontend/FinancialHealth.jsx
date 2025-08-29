// frontend/FinancialHealth.jsx
import React, { useState } from 'react';
import useFetch from './utils/useFetch'; // adapt to your app's fetch hook if available

export default function FinancialHealth(){
  const [userId, setUserId] = useState('123');
  const { data, loading, error, reload } = useFetch(`/api/insights/${userId}`);

  return (
    <div className="card financial-health" style={{ maxWidth: '960px', margin: '16px auto' }}>
      <h2 style={{ color: 'var(--primary-color)' }}>Financial Health</h2>
      <div style={{ marginBottom: 12 }}>
        <label>User ID: </label>
        <input value={userId} onChange={(e)=>setUserId(e.target.value)} style={{ marginLeft: 8 }} />
        <button onClick={reload} style={{ marginLeft: 8 }} className="btn btn-primary">Load</button>
      </div>

      {loading && <div>Loading insights...</div>}
      {error && <div className="error">Error loading insights</div>}

      {data && (
        <div>
          <div className="summary" style={{ display: 'flex', gap: 24 }}>
            <div className="stat card">
              <div className="label">Income</div>
              <div className="value">${data.summary.income}</div>
            </div>
            <div className="stat card">
              <div className="label">Spend</div>
              <div className="value">${data.summary.spend}</div>
            </div>
            <div className="stat card">
              <div className="label">Net</div>
              <div className="value">${data.summary.net}</div>
            </div>
          </div>

          <h3 style={{ marginTop: 16 }}>Top categories</h3>
          <ul>
            {data.categories.map(c => (
              <li key={c.name}>{c.name}: ${c.sum}</li>
            ))}
          </ul>

          <h3>Credit utilization</h3>
          <p>{Math.round(data.credit_utilization.ratio * 100)}% of ${data.credit_utilization.limit}</p>

          <h3>Your personalized insight</h3>
          <div className="narrative card">{data.narrative}</div>
        </div>
      )}
    </div>
  )
}
