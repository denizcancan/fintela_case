function PoorPerformersTable({ funds }) {
  if (funds.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No poor performing funds found. All funds are performing within acceptable ranges.
      </div>
    )
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'bg-red-100 text-red-800'
    if (confidence >= 0.4) return 'bg-orange-100 text-orange-800'
    return 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Fund Code
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Confidence
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Severity
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {funds
            .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
            .map((fund) => (
              <tr key={fund.fund_code} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {fund.fund_code}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {fund.confidence ? fund.confidence.toFixed(4) : 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {fund.confidence && (
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getConfidenceColor(fund.confidence)}`}>
                      {fund.confidence >= 0.7 ? 'High' : fund.confidence >= 0.4 ? 'Medium' : 'Low'}
                    </span>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}

export default PoorPerformersTable

