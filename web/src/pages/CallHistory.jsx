import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import {
  ArrowLeft,
  Phone,
  Upload,
  FileText,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { format } from 'date-fns'

function CallHistory() {
  const { id } = useParams()
  const [calls, setCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)

  useEffect(() => {
    fetchCallHistory()
  }, [id])

  const fetchCallHistory = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/customers/${id}/call-history`)
      setCalls(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load call history')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Please select a file')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      setUploading(true)
      const response = await api.post(`/customers/${id}/upload-transcript`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      alert('Transcript uploaded and analyzed successfully!')
      setShowUploadModal(false)
      setSelectedFile(null)
      fetchCallHistory() // Refresh call history
    } catch (err) {
      alert('Failed to upload transcript')
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const getOutcomeIcon = (outcome) => {
    if (!outcome) return null
    if (outcome.includes('payment') || outcome.includes('promised')) {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    }
    if (outcome.includes('refused') || outcome.includes('no_answer')) {
      return <XCircle className="h-5 w-5 text-red-500" />
    }
    return <AlertCircle className="h-5 w-5 text-yellow-500" />
  }

  const getOutcomeColor = (outcome) => {
    if (!outcome) return 'bg-gray-100 text-gray-800'
    if (outcome.includes('payment') || outcome.includes('promised')) {
      return 'bg-green-100 text-green-800'
    }
    if (outcome.includes('refused') || outcome.includes('no_answer')) {
      return 'bg-red-100 text-red-800'
    }
    return 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link
          to={`/customer/${id}`}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customer Details
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Call History</h1>
            <p className="text-gray-600 mt-1">View and manage call transcripts</p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Transcript
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Loading call history...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Call History List */}
      {!loading && !error && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {calls.length === 0 ? (
            <div className="text-center py-12">
              <Phone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">No call history found</p>
              <p className="text-sm text-gray-500">
                Upload a transcript to get started
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {calls.map((call) => (
                <div key={call.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="bg-primary-100 rounded-full p-3">
                        <Phone className="h-5 w-5 text-primary-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {call.direction === 'outbound' ? 'Outbound' : 'Inbound'} Call
                          </h3>
                          {getOutcomeIcon(call.outcome)}
                          {call.outcome && (
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded ${getOutcomeColor(
                                call.outcome
                              )}`}
                            >
                              {call.outcome}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-2" />
                            {format(new Date(call.timestamp), 'MMM d, yyyy')}
                          </div>
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-2" />
                            {format(new Date(call.timestamp), 'h:mm a')}
                          </div>
                          {call.duration_seconds && (
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-2" />
                              {Math.floor(call.duration_seconds / 60)}m{' '}
                              {call.duration_seconds % 60}s
                            </div>
                          )}
                        </div>
                        {call.notes && (
                          <p className="mt-3 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                            {call.notes}
                          </p>
                        )}
                      </div>
                    </div>
                    <Link
                      to={`/customer/${id}/transcript/${call.id}`}
                      className="ml-4 text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      View Details →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload Transcript</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Transcript File
                </label>
                <input
                  type="file"
                  accept=".txt,.json,.md"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {selectedFile && (
                  <p className="mt-2 text-sm text-gray-600">
                    Selected: {selectedFile.name}
                  </p>
                )}
              </div>
              <p className="text-sm text-gray-500">
                Supported formats: .txt, .json, .md
              </p>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setSelectedFile(null)
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Upload & Analyze'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CallHistory
