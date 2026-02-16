import { createContext, useContext } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import CustomerList from './pages/CustomerList'
import CustomerDetail from './pages/CustomerDetail'
import CallHistory from './pages/CallHistory'
import ToastContainer, { useToast } from './components/ToastContainer'

const ToastContext = createContext(null)

export const useToastContext = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToastContext must be used within ToastProvider')
  }
  return context
}

function ToastProvider({ children }) {
  const toast = useToast()
  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toast.toasts} onClose={toast.removeToast} />
    </ToastContext.Provider>
  )
}

function App() {
  return (
    <Router>
      <ToastProvider>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center space-x-8">
                  <Link to="/" className="flex items-center">
                    <img src="/image.png" alt="Logo" className="h-8" />
                  </Link>
                  <div className="hidden md:flex items-center space-x-6">
                    <Link
                      to="/"
                      className="text-gray-700 hover:text-tangerine-500 px-1 py-2 text-sm font-semibold transition-colors border-b-2 border-transparent hover:border-tangerine-500"
                    >
                      Customers
                    </Link>
                    <span className="text-gray-700 hover:text-tangerine-500 px-1 py-2 text-sm font-semibold transition-colors border-b-2 border-transparent hover:border-tangerine-500 cursor-pointer">
                      Reports
                    </span>
                    <span className="text-gray-700 hover:text-tangerine-500 px-1 py-2 text-sm font-semibold transition-colors border-b-2 border-transparent hover:border-tangerine-500 cursor-pointer">
                      Settings
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main>
            <Routes>
              <Route path="/" element={<CustomerList />} />
              <Route path="/customer/:id" element={<CustomerDetail />} />
              <Route path="/customer/:id/call-history" element={<CallHistory />} />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="bg-gray-900 text-gray-400 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="flex items-center justify-between">
                <p className="text-sm">&copy; 2026 Customer Debt Management. All rights reserved.</p>
                <div className="flex items-center space-x-6 text-sm">
                  <span className="hover:text-white cursor-pointer">Privacy</span>
                  <span className="hover:text-white cursor-pointer">Terms</span>
                  <span className="hover:text-white cursor-pointer">Contact</span>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </ToastProvider>
    </Router>
  )
}

export default App
