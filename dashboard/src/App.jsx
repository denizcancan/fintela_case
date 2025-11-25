import { useState, useEffect } from 'react'
import axios from 'axios'
import SummaryCards from './components/SummaryCards'
import RiskChart from './components/RiskChart'
import HighRiskTable from './components/HighRiskTable'
import PoorPerformersTable from './components/PoorPerformersTable'

// Use environment variable or default
// In Docker, nginx proxies /api to FastAPI, so use relative URL
// For local dev, use localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : '/api')

function App() {
  const [portfolios, setPortfolios] = useState([])
  const [highRiskPortfolios, setHighRiskPortfolios] = useState([])
  const [poorPerformers, setPoorPerformers] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  const [riskDistribution, setRiskDistribution] = useState({ LOW: 0, MEDIUM: 0, HIGH: 0 })

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch all portfolios
      const portfoliosRes = await axios.get(`${API_BASE_URL}/portfolios`)
      const allPortfolios = portfoliosRes.data.portfolios || []
      setPortfolios(allPortfolios)
      
      // Fetch high-risk portfolios
      const highRiskRes = await axios.get(`${API_BASE_URL}/alerts/portfolios`)
      setHighRiskPortfolios(highRiskRes.data.portfolios || [])
      
      // Fetch poor performing funds
      const poorPerformersRes = await axios.get(`${API_BASE_URL}/alerts/funds`)
      setPoorPerformers(poorPerformersRes.data.funds || [])
      
      // Fetch risk for all portfolios to calculate distribution
      const riskPromises = allPortfolios.map(async (portfolio) => {
        try {
          const riskRes = await axios.get(`${API_BASE_URL}/portfolios/${portfolio.id}/risk`)
          return riskRes.data.risk
        } catch (error) {
          return 'UNKNOWN'
        }
      })
      
      const risks = await Promise.all(riskPromises)
      const distribution = risks
        .filter(risk => risk && risk !== 'UNKNOWN')
        .reduce((acc, risk) => {
          acc[risk] = (acc[risk] || 0) + 1
          return acc
        }, { LOW: 0, MEDIUM: 0, HIGH: 0 })
      setRiskDistribution(distribution)
      
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Fintela Risk Dashboard</h1>
            <div className="text-sm text-gray-500">
              {lastUpdate && `Last updated: ${lastUpdate.toLocaleTimeString()}`}
              {!lastUpdate && loading && 'Loading...'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading data...</p>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <SummaryCards
              totalPortfolios={portfolios.length}
              highRiskCount={highRiskPortfolios.length}
              poorPerformersCount={poorPerformers.length}
            />

            {/* Risk Distribution Chart */}
            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Distribution</h2>
              <RiskChart riskDistribution={riskDistribution} />
            </div>

            {/* High-Risk Portfolios Table */}
            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                High-Risk Portfolios ({highRiskPortfolios.length})
              </h2>
              <HighRiskTable portfolios={highRiskPortfolios} />
            </div>

            {/* Poor Performing Funds Table */}
            <div className="mt-8 bg-white rounded-lg shadow p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Poor Performing Funds ({poorPerformers.length})
              </h2>
              <PoorPerformersTable funds={poorPerformers} />
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App

