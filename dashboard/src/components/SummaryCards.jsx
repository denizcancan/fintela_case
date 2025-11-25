function SummaryCards({ totalPortfolios, highRiskCount, poorPerformersCount }) {
  const cards = [
    {
      title: 'Total Portfolios',
      value: totalPortfolios,
      color: 'blue',
      icon: '📊'
    },
    {
      title: 'High-Risk Portfolios',
      value: highRiskCount,
      color: 'red',
      icon: '⚠️'
    },
    {
      title: 'Poor Performing Funds',
      value: poorPerformersCount,
      color: 'orange',
      icon: '📉'
    }
  ]

  const colorClasses = {
    blue: 'bg-blue-500',
    red: 'bg-red-500',
    orange: 'bg-orange-500'
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow p-6 border-l-4"
          style={{ borderLeftColor: card.color === 'blue' ? '#3b82f6' : card.color === 'red' ? '#ef4444' : '#f97316' }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
            </div>
            <div className="text-4xl">{card.icon}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SummaryCards

