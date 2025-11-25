import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

function RiskChart({ riskDistribution }) {
  const data = [
    { name: 'LOW', value: riskDistribution.LOW || 0, color: '#10b981' },
    { name: 'MEDIUM', value: riskDistribution.MEDIUM || 0, color: '#f59e0b' },
    { name: 'HIGH', value: riskDistribution.HIGH || 0, color: '#ef4444' },
  ].filter(item => item.value > 0)

  const COLORS = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#ef4444'
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No risk data available. Please run the portfolio risk job.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

export default RiskChart

