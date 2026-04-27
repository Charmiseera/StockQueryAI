import { useState, useEffect } from 'react'
import api from '../services/api'
import DataTable from './DataTable'

export default function AlertsDashboard() {
  const [lowStockItems, setLowStockItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true)
        const { data } = await api.post('/query', { question: 'Which products are low in stock?' })
        setLowStockItems(data.data || [])
      } catch (err) {
        setError('Failed to load stock alerts.')
      } finally {
        setLoading(false)
      }
    }
    fetchAlerts()
  }, [])

  return (
    <div className="alerts-dashboard" style={{ padding: '2rem', animation: 'fade-up 0.4s ease-out' }}>
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid #333', paddingBottom: '1rem' }}>
        <h2 style={{ color: '#ff6b2b', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.5rem' }}>⚠</span> Low Stock Alerts
        </h2>
        <p style={{ color: '#888', marginTop: '0.5rem' }}>
          The following items have stock levels below the threshold (10 units).
        </p>
      </header>

      {loading ? (
        <div className="loading-state" style={{ color: '#666', fontStyle: 'italic' }}>
          Scanning inventory for low stock...
        </div>
      ) : error ? (
        <div className="error-state" style={{ color: '#ff6b2b' }}>{error}</div>
      ) : lowStockItems.length === 0 ? (
        <div className="empty-state" style={{ padding: '3rem', textAlign: 'center', background: '#121820', border: '1px dashed #333' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✅</div>
          <h3 style={{ color: '#fff' }}>Inventory Healthy</h3>
          <p style={{ color: '#888' }}>All products are currently above the stock threshold.</p>
        </div>
      ) : (
        <div className="alerts-content">
          <div className="alert-summary" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ background: 'rgba(255, 107, 43, 0.1)', border: '1px solid rgba(255, 107, 43, 0.2)', padding: '1.5rem' }}>
              <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Total Alerts</div>
              <div style={{ color: '#ff6b2b', fontSize: '2.5rem', fontWeight: '800', fontFamily: 'var(--font-mono)' }}>{lowStockItems.length}</div>
            </div>
            <div style={{ background: 'rgba(0, 255, 136, 0.05)', border: '1px solid rgba(255, 255, 255, 0.05)', padding: '1.5rem' }}>
              <div style={{ color: '#888', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Critical (&lt; 5)</div>
              <div style={{ color: '#fff', fontSize: '2.5rem', fontWeight: '800', fontFamily: 'var(--font-mono)' }}>
                {lowStockItems.filter(item => item.stock < 5).length}
              </div>
            </div>
          </div>
          <DataTable data={lowStockItems} />
        </div>
      )}
    </div>
  )
}
