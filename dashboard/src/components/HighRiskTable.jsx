function HighRiskTable({ portfolios }) {
  if (portfolios.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No high-risk portfolios found. All portfolios are within acceptable risk levels.
      </div>
    )
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'HIGH':
        return 'bg-red-100 text-red-800'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800'
      case 'LOW':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Portfolio ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Risk Score
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Risk Level
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {portfolios.map((portfolio) => (
            <tr key={portfolio.portfolio_id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                #{portfolio.portfolio_id}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {portfolio.risk_score.toFixed(6)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getRiskColor(portfolio.risk)}`}>
                  {portfolio.risk}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default HighRiskTable

