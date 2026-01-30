import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Customers from './pages/Customers'
import CustomerPortal from './pages/CustomerPortal'
import Reports from './pages/Reports'
import WilsonCenterReport from './pages/WilsonCenterReport'
import ApiTest from './pages/ApiTest'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="customers" element={<Customers />} />
          <Route path="customers/:id" element={<CustomerPortal />} />
          <Route path="reports" element={<Reports />} />
          <Route path="reports/wilson-center" element={<WilsonCenterReport />} />
          <Route path="api-test" element={<ApiTest />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

