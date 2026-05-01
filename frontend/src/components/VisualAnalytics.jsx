import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend
} from 'recharts';

/**
 * VisualAnalytics — Automatically detects data patterns and renders neon-themed charts.
 */
export default function VisualAnalytics({ data, userQuery = '' }) {
  if (!data || data.length === 0) return null;

  const q = userQuery.toLowerCase();
  const wantsVisual = q.includes('graph') || 
                      q.includes('chart') || 
                      q.includes('visual') || 
                      q.includes('plot') || 
                      q.includes('diagram') ||
                      q.includes('analytic');

  if (!wantsVisual) return null;

  const isCategoryStats = data.some(item => 'category' in item && ('product_count' in item || 'total_stock' in item));
  const isProductList = data.some(item => 'name' in item && 'stock' in item);

  const COLORS = ['#00ff88', '#00d4ff', '#ffea00', '#ff4d00', '#ff00ff'];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="neon-tooltip">
          <p className="label">{`${label}`}</p>
          {payload.map((pld, index) => (
            <p key={index} style={{ color: pld.fill, fontSize: '12px', fontWeight: 'bold' }}>
              {`${pld.name}: ${pld.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (isCategoryStats) {
    return (
      <div className="analytics-chart-wrapper">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Category Insights</h3>
            <span className="chart-subtitle">Distribution & Stock Levels</span>
          </div>
          <span className="chart-badge">LIVE DATA</span>
        </div>
        
        <div className="chart-grid">
          <div className="chart-item">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data}>
                <XAxis dataKey="category" hide />
                <YAxis hide />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="total_stock" radius={[6, 6, 0, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <h4 className="chart-subtitle">Stock Volume</h4>
          </div>

          <div className="chart-item">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={8}
                  dataKey="product_count"
                  nameKey="category"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <h4 className="chart-subtitle">Item Count</h4>
          </div>
        </div>

        <div className="chart-footer">
          <div className="footer-stat">
            <span className="stat-label">Total Categories</span>
            <span className="stat-value">{data.length}</span>
          </div>
          <div className="footer-divider" />
          <div className="footer-stat">
            <span className="stat-label">Analytics Mode</span>
            <span className="stat-value">Semantic</span>
          </div>
        </div>
      </div>
    );
  }

  if (isProductList && data.length > 2) {
    return (
      <div className="analytics-chart-wrapper">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Product Stock Analysis</h3>
            <span className="chart-subtitle">Comparing top {Math.min(8, data.length)} items</span>
          </div>
          <span className="chart-badge">METRICS</span>
        </div>

        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data.slice(0, 8)}>
            <XAxis dataKey="name" hide />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="stock" radius={[8, 8, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="chart-footer">
          <div className="footer-stat">
            <span className="stat-label">Sample Size</span>
            <span className="stat-value">{data.length} items</span>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
