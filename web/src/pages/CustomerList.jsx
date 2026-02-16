import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { Search, User, Phone, Mail, DollarSign, Calendar } from 'lucide-react'


function CustomerList() {
  const [customers, setCustomers] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCustomers()
  }, [searchTerm])

  const fetchCustomers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/customers', {
        params: searchTerm ? { search: searchTerm } : {},
      })
      setCustomers(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load customers')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Hero Section - full width, flush with navbar */}
      <div className="bg-gradient-to-r from-tangerine-500 to-tangerine-400 py-10 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold mb-2">Customers</h1>
          <p className="text-tangerine-100 text-lg">Manage customer accounts and debt tracking</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search by name, phone, or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-full focus:ring-2 focus:ring-tangerine-500 focus:border-transparent shadow-sm"
          />
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500"></div>
          <p className="mt-2 text-gray-600">Loading customers...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Customer Cards */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {customers.map((customer) => (
            <Link
              key={customer.id}
              to={`/customer/${customer.id}`}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-lg hover:border-tangerine-200 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-tangerine-100 rounded-full p-2 group-hover:bg-tangerine-200 transition-colors">
                    <User className="h-5 w-5 text-tangerine-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-tangerine-600 transition-colors">
                      {customer.first_name} {customer.last_name}
                    </h3>
                    <p className="text-sm text-gray-500">ID: {customer.id}</p>
                  </div>
                </div>
                {customer.account_status && (
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      customer.account_status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {customer.account_status}
                  </span>
                )}
              </div>

              <div className="space-y-2">
                {customer.phone_primary && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="h-4 w-4 mr-2 text-tangerine-400" />
                    {customer.phone_primary}
                  </div>
                )}
                {customer.email && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Mail className="h-4 w-4 mr-2 text-tangerine-400" />
                    {customer.email}
                  </div>
                )}
                {customer.city && customer.state && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="h-4 w-4 mr-2 text-tangerine-400" />
                    {customer.city}, {customer.state}
                  </div>
                )}
                <div className="flex items-center text-sm font-semibold text-tangerine-500 mt-3 pt-3 border-t border-gray-100">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Total Debt: ${customer.total_debt?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!loading && !error && customers.length === 0 && (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <User className="h-12 w-12 text-tangerine-300 mx-auto mb-4" />
          <p className="text-gray-600">No customers found</p>
        </div>
      )}
      </div>
    </div>
  )
}

export default CustomerList
