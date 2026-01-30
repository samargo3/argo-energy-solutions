import { useState } from 'react'
import { bestEnergyApi } from '../services/api/bestEnergyApi'
import { getDateRange } from '../utils/dateUtils'
import './ApiTest.css'

/**
 * Test component to verify API connection and data access
 * You can access this at /api-test route (add to router if needed)
 * Or temporarily add it to your App.tsx to test
 */
export default function ApiTest() {
  const [status, setStatus] = useState<string>('Ready to test')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const testCustomers = async () => {
    setLoading(true)
    setStatus('Testing: Fetching customers...')
    setError(null)
    setResults(null)

    try {
      const data = await bestEnergyApi.getCustomers()
      setResults({ type: 'customers', data })
      setStatus('✅ Success: Customers fetched!')
      console.log('Customers data:', data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customers')
      setStatus('❌ Error: Failed to fetch customers')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const testEnergyData = async () => {
    setLoading(true)
    setStatus('Testing: Fetching energy data...')
    setError(null)
    setResults(null)

    try {
      // First get a customer ID
      const customers = await bestEnergyApi.getCustomers()
      
      if (!customers.items || customers.items.length === 0) {
        setError('No customers found. Cannot test energy data.')
        setStatus('⚠️ Warning: No customers available')
        return
      }

      const customerId = customers.items[0].id
      const dateRange = getDateRange('month')
      
      setStatus(`Testing: Fetching energy data for customer ${customerId}...`)
      
      const data = await bestEnergyApi.getCustomerEnergyConsumption(
        customerId,
        dateRange
      )
      setResults({ type: 'energy', customerId, data })
      setStatus('✅ Success: Energy data fetched!')
      console.log('Energy data:', data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch energy data')
      setStatus('❌ Error: Failed to fetch energy data')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const testGroupedData = async () => {
    setLoading(true)
    setStatus('Testing: Fetching grouped energy data...')
    setError(null)
    setResults(null)

    try {
      // First get a customer ID
      const customers = await bestEnergyApi.getCustomers()
      
      if (!customers.items || customers.items.length === 0) {
        setError('No customers found. Cannot test grouped data.')
        setStatus('⚠️ Warning: No customers available')
        return
      }

      const customerId = customers.items[0].id
      const dateRange = getDateRange('month')
      
      setStatus(`Testing: Fetching grouped data for customer ${customerId}...`)
      
      const data = await bestEnergyApi.getGroupedEnergyConsumption(
        customerId,
        { ...dateRange, groupBy: 'day' }
      )
      setResults({ type: 'grouped', customerId, data })
      setStatus('✅ Success: Grouped energy data fetched!')
      console.log('Grouped data:', data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch grouped data')
      setStatus('❌ Error: Failed to fetch grouped data')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const clearResults = () => {
    setResults(null)
    setError(null)
    setStatus('Ready to test')
  }

  return (
    <div className="api-test">
      <div className="container">
        <h1>API Connection Test</h1>
        <p className="description">
          Use this page to test your Best.Energy API connection and verify data access.
        </p>

        <div className="test-controls">
          <button 
            onClick={testCustomers} 
            disabled={loading}
            className="test-btn"
          >
            Test Customers API
          </button>
          <button 
            onClick={testEnergyData} 
            disabled={loading}
            className="test-btn"
          >
            Test Energy Data API
          </button>
          <button 
            onClick={testGroupedData} 
            disabled={loading}
            className="test-btn"
          >
            Test Grouped Data API
          </button>
          <button 
            onClick={clearResults} 
            disabled={loading}
            className="test-btn secondary"
          >
            Clear Results
          </button>
        </div>

        <div className="status">
          <strong>Status:</strong> {status}
        </div>

        {loading && (
          <div className="loading">
            <p>Loading...</p>
          </div>
        )}

        {error && (
          <div className="error-box">
            <h3>Error:</h3>
            <p>{error}</p>
            <div className="error-tips">
              <h4>Common Issues:</h4>
              <ul>
                <li>Check your <code>.env</code> file has correct API URL and key</li>
                <li>Verify the API endpoints match your API documentation</li>
                <li>Check browser console (F12) for detailed error messages</li>
                <li>Ensure your API key is valid and not expired</li>
                <li>Check Network tab to see the actual API request/response</li>
              </ul>
            </div>
          </div>
        )}

        {results && (
          <div className="results">
            <h3>Results:</h3>
            <div className="results-info">
              <p><strong>Type:</strong> {results.type}</p>
              {results.customerId && (
                <p><strong>Customer ID:</strong> {results.customerId}</p>
              )}
              {results.data?.items && (
                <p><strong>Items Count:</strong> {results.data.items.length}</p>
              )}
              {Array.isArray(results.data) && (
                <p><strong>Items Count:</strong> {results.data.length}</p>
              )}
            </div>
            <div className="results-data">
              <h4>Data Preview:</h4>
              <pre>{JSON.stringify(results.data, null, 2)}</pre>
            </div>
            <p className="note">
              💡 Check the browser console (F12) for full data structure
            </p>
          </div>
        )}

        <div className="instructions">
          <h3>Next Steps:</h3>
          <ol>
            <li>Make sure your <code>.env</code> file is configured</li>
            <li>Update API endpoints in <code>src/services/api/bestEnergyApi.ts</code> if needed</li>
            <li>Click "Test Customers API" first to verify basic connection</li>
            <li>If successful, test energy data endpoints</li>
            <li>Check the data structure and update types if needed</li>
          </ol>
        </div>
      </div>
    </div>
  )
}



