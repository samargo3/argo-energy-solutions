import { Link } from 'react-router-dom'
import { useCustomers } from '../hooks/useCustomerData'
import './Customers.css'

export default function Customers() {
  const { data: customersData, isLoading, error } = useCustomers()

  if (isLoading) {
    return (
      <div className="customers-page">
        <div className="container">
          <div className="loading">Loading customers...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="customers-page">
        <div className="container">
          <div className="error">Error loading customers. Please check your API connection.</div>
        </div>
      </div>
    )
  }

  const customers = customersData?.items || []

  return (
    <div className="customers-page">
      <div className="container">
        <h1 className="page-title">Customers</h1>
        
        {customers.length === 0 ? (
          <div className="empty-state">
            <p>No customers found. Connect to the Best.Energy API to see customer data.</p>
          </div>
        ) : (
          <div className="customers-grid">
            {customers.map(customer => (
              <Link 
                key={customer.id} 
                to={`/customers/${customer.id}`}
                className="customer-card"
              >
                <h3>{customer.name}</h3>
                {customer.email && <p className="customer-email">{customer.email}</p>}
                {customer.address && <p className="customer-address">{customer.address}</p>}
                {customer.sites && customer.sites.length > 0 && (
                  <p className="customer-sites">{customer.sites.length} site(s)</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

