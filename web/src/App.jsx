import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import CustomerList from './pages/CustomerList'
import CustomerDetail from './pages/CustomerDetail'
import CallHistory from './pages/CallHistory'
import { Users, Phone } from 'lucide-react'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/" className="flex items-center space-x-2">
                  <Phone className="h-6 w-6 text-primary-600" />
                  <span className="text-xl font-bold text-gray-900">Customer Debt Management</span>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-1"
                >
                  <Users className="h-4 w-4" />
                  <span>Customers</span>
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<CustomerList />} />
            <Route path="/customer/:id" element={<CustomerDetail />} />
            <Route path="/customer/:id/call-history" element={<CallHistory />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
