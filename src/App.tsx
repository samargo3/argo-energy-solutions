import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Customers from './pages/Customers'
import CustomerPortal from './pages/CustomerPortal'
import Reports from './pages/Reports'
import WilsonCenterReport from './pages/WilsonCenterReport'
import WeeklyReport from './pages/WeeklyReport'
import ApiTest from './pages/ApiTest'
import EnergyHistory from './pages/EnergyHistory'
import LoginPage from './pages/LoginPage'
import './App.css'

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="customers" element={<Customers />} />
        <Route path="customers/:id" element={<CustomerPortal />} />
        <Route path="reports" element={<Reports />} />
        <Route path="reports/wilson-center" element={<WilsonCenterReport />} />
        <Route path="reports/weekly" element={<WeeklyReport />} />
        <Route path="api-test" element={<ApiTest />} />
        <Route path="energy-history" element={<EnergyHistory />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
