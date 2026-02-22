import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { Search, User, Phone, Mail, DollarSign, PhoneCall } from 'lucide-react'


function CustomerList() {
  const [customers, setCustomers] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [callStatuses, setCallStatuses] = useState({}) // { [customerId]: 'pending' | 'calling' | 'done' | 'error' }
  const [bulkCalling, setBulkCalling] = useState(false)

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

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === customers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(customers.map((c) => c.id)))
    }
  }

  const handleBulkAiCall = async () => {
    if (selectedIds.size === 0) return
    setBulkCalling(true)

    const ids = Array.from(selectedIds)
    // Mark all as pending
    setCallStatuses((prev) => {
      const next = { ...prev }
      ids.forEach((id) => { next[id] = 'pending' })
      return next
    })

    // Fire calls sequentially to avoid hammering the server
    for (const id of ids) {
      setCallStatuses((prev) => ({ ...prev, [id]: 'calling' }))
      try {
        await api.post(`/customers/${id}/make-call`)
        setCallStatuses((prev) => ({ ...prev, [id]: 'done' }))
      } catch {
        setCallStatuses((prev) => ({ ...prev, [id]: 'error' }))
      }
    }

    setBulkCalling(false)
  }

  const allSelected = customers.length > 0 && selectedIds.size === customers.length
  const someSelected = selectedIds.size > 0 && !allSelected

  return (
    <div>
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-tangerine-500 to-tangerine-400 py-10 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold mb-2">Customers</h1>
          <p className="text-tangerine-100 text-lg">Manage customer accounts and debt tracking</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">

        {/* Search + Bulk Action Bar */}
        <div className="mb-6 flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search by name, phone, or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-full focus:ring-2 focus:ring-tangerine-500 focus:border-transparent shadow-sm"
            />
          </div>
          <button
            onClick={handleBulkAiCall}
            disabled={selectedIds.size === 0 || bulkCalling}
            className="flex items-center gap-2 px-5 py-3 bg-tangerine-500 hover:bg-tangerine-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-full shadow-sm transition-colors whitespace-nowrap"
          >
            <PhoneCall className="h-4 w-4" />
            {bulkCalling
              ? 'Calling...'
              : selectedIds.size > 0
                ? `Make AI Call (${selectedIds.size})`
                : 'Make AI Call'}
          </button>
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

        {/* Customer Table */}
        {!loading && !error && customers.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3 text-center">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => { if (el) el.indeterminate = someSelected }}
                      onChange={toggleSelectAll}
                      className="h-4 w-4 rounded border-gray-300 text-tangerine-500 focus:ring-tangerine-500 cursor-pointer"
                    />
                  </th>
                  <th className="px-6 py-3">Customer</th>
                  <th className="px-6 py-3">Phone</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3">Location</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Total Debt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {customers.map((customer) => {
                  const status = callStatuses[customer.id]
                  const isSelected = selectedIds.has(customer.id)
                  return (
                    <tr
                      key={customer.id}
                      className={`transition-colors group ${isSelected ? 'bg-tangerine-50' : 'hover:bg-gray-50'}`}
                    >
                      <td className="px-4 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          {status && (
                            <span className={`text-xs font-medium ${
                              status === 'calling' ? 'text-tangerine-500' :
                              status === 'done' ? 'text-green-600' :
                              status === 'error' ? 'text-red-500' :
                              'text-gray-400'
                            }`}>
                              {status === 'calling' ? '📞' :
                               status === 'done' ? '✓' :
                               status === 'error' ? '✗' :
                               '⏳'}
                            </span>
                          )}
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(customer.id)}
                            className="h-4 w-4 rounded border-gray-300 text-tangerine-500 focus:ring-tangerine-500 cursor-pointer"
                          />
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Link to={`/customer/${customer.id}`} className="flex items-center space-x-3">
                          <div className="bg-tangerine-100 rounded-full p-2 group-hover:bg-tangerine-200 transition-colors shrink-0">
                            <User className="h-4 w-4 text-tangerine-600" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 group-hover:text-tangerine-600 transition-colors">
                              {customer.first_name} {customer.last_name}
                            </p>
                            <p className="text-xs text-gray-400">ID: {customer.id}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {customer.phone_primary ? (
                          <span className="flex items-center gap-1.5">
                            <Phone className="h-3.5 w-3.5 text-tangerine-400" />
                            {customer.phone_primary}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {customer.email ? (
                          <span className="flex items-center gap-1.5">
                            <Mail className="h-3.5 w-3.5 text-tangerine-400" />
                            {customer.email}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {customer.city && customer.state ? `${customer.city}, ${customer.state}` : '—'}
                      </td>
                      <td className="px-6 py-4">
                        {customer.account_status ? (
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            customer.account_status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {customer.account_status}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold text-tangerine-600">
                        <span className="flex items-center justify-end gap-0.5">
                          <DollarSign className="h-3.5 w-3.5" />
                          {customer.total_debt?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
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
