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
  BookOpen,
  Eye,
  X,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
} from 'lucide-react'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'

function CallHistory() {
  const { id } = useParams()
  const [plannedCalls, setPlannedCalls] = useState([])
  const [automaticCalls, setAutomaticCalls] = useState([])
  const [completedCalls, setCompletedCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCall, setSelectedCall] = useState(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileType, setFileType] = useState('transcript')
  const [planningContent, setPlanningContent] = useState(null)
  const [transcriptContent, setTranscriptContent] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [planningExpanded, setPlanningExpanded] = useState(false)
  const [transcriptExpanded, setTranscriptExpanded] = useState(false)

  useEffect(() => {
    fetchCallHistory()
  }, [id])
  
  // Poll for planning script updates
  useEffect(() => {
    if (!plannedCalls || plannedCalls.length === 0) return
    
    const interval = setInterval(() => {
      // Check if there are planned calls without planning scripts
      const hasPendingPlanning = plannedCalls.some(
        call => !call.planning_script
      )
      if (hasPendingPlanning) {
        fetchCallHistory()
      }
    }, 5000) // Poll every 5 seconds
    
    return () => clearInterval(interval)
  }, [id, plannedCalls])

  const fetchCallHistory = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/customers/${id}/call-history`)
      setPlannedCalls(response.data.planned || [])
      setAutomaticCalls(response.data.automatic || [])
      setCompletedCalls(response.data.completed || [])
      setError(null)
    } catch (err) {
      setError('Failed to load call history')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetails = async (call) => {
    setSelectedCall(call)
    setShowDetailsModal(true)
    setLoadingDetails(true)
    setPlanningContent(null)
    setTranscriptContent(null)
    setPlanningExpanded(false)
    setTranscriptExpanded(false)

    try {
      // Load planning file if exists
      if (call.planning_file_path || call.planning_script) {
        try {
          // Try to get from planning_script first (already loaded)
          if (call.planning_script?.strategy_content) {
            setPlanningContent(call.planning_script.strategy_content)
          } else if (call.planning_file_path) {
            // Fallback to loading from file
            const planningId = call.id.startsWith('scheduled_') 
              ? call.id.replace('scheduled_', '')
              : call.scheduled_call_id || call.id
            const response = await api.get(`/call-history/scheduled_${planningId}/planning-file`)
            setPlanningContent(response.data.content)
          }
        } catch (err) {
          console.warn('Could not load planning file:', err)
        }
      }

      // Load transcript if exists
      if (call.transcript_file_path || (call.type === 'completed' && !call.planning_script)) {
        try {
          const transcriptId = call.type === 'completed' ? call.id : (call.scheduled_call_id || call.id.replace('scheduled_', ''))
          if (transcriptId) {
            const response = await api.get(`/call-history/${transcriptId}/transcript-file`)
            setTranscriptContent(response.data.content)
          }
        } catch (err) {
          console.warn('Could not load transcript:', err)
        }
      }
    } catch (err) {
      console.error('Error loading call details:', err)
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !selectedCall) {
      alert('Please select a file and ensure a call is selected')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('file_type', fileType)
    if (selectedCall.scheduled_call_id) {
      formData.append('scheduled_call_id', selectedCall.scheduled_call_id.toString())
    }

    try {
      setUploading(true)
      await api.post(`/customers/${id}/upload-transcript`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      alert('File uploaded successfully!')
      setShowUploadModal(false)
      setSelectedFile(null)
      setFileType('transcript')
      handleViewDetails(selectedCall) // Refresh details
      fetchCallHistory()
    } catch (err) {
      alert('Failed to upload file')
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteFile = async (fileType) => {
    if (!selectedCall) return
    
    if (!window.confirm(`Are you sure you want to delete this ${fileType} file?`)) {
      return
    }

    try {
      // Determine call_id for the API
      let callId = selectedCall.id
      if (callId.startsWith('scheduled_')) {
        callId = callId.replace('scheduled_', '')
      } else if (selectedCall.scheduled_call_id) {
        callId = selectedCall.scheduled_call_id.toString()
      } else if (fileType === 'transcript' && selectedCall.type === 'completed') {
        callId = selectedCall.id.toString()
      }

      await api.delete(`/call-history/${callId}/file`, {
        params: { file_type: fileType }
      })
      
      alert(`${fileType.charAt(0).toUpperCase() + fileType.slice(1)} file deleted successfully!`)
      
      // Clear the content from state
      if (fileType === 'planning') {
        setPlanningContent(null)
      } else if (fileType === 'transcript') {
        setTranscriptContent(null)
      }
      
      // Refresh call history and details
      fetchCallHistory()
      handleViewDetails(selectedCall)
    } catch (err) {
      alert(`Failed to delete ${fileType} file`)
      console.error(err)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-800',
      planned: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      missed: 'bg-gray-100 text-gray-800',
    }
    return badges[status] || 'bg-gray-100 text-gray-800'
  }

  const getOutcomeIcon = (outcome) => {
    if (!outcome) return null
    if (outcome.includes('payment') || outcome.includes('promised')) {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    }
    if (outcome.includes('refused') || outcome.includes('no_answer')) {
      return <XCircle className="h-4 w-4 text-red-500" />
    }
    return <AlertCircle className="h-4 w-4 text-yellow-500" />
  }

  const CallCard = ({ call }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <Phone className="h-4 w-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-900">
              {call.scheduled_time 
                ? format(new Date(call.scheduled_time), 'MMM d, h:mm a')
                : format(new Date(call.timestamp), 'MMM d, h:mm a')}
            </span>
            {call.outcome && getOutcomeIcon(call.outcome)}
          </div>
          {call.planning_script?.suggested_time && (
            <p className="text-xs text-gray-500 mb-1">
              Suggested: {call.planning_script.suggested_time}
              {call.planning_script.suggested_day && ` on ${call.planning_script.suggested_day}`}
            </p>
          )}
          {call.notes && (
            <p className="text-xs text-gray-600 line-clamp-2">{call.notes}</p>
          )}
          {call.status === 'planned' && !call.planning_script && (
            <div className="mt-1 flex items-center space-x-1">
              <Clock className="h-3 w-3 text-yellow-600 animate-spin" />
              <span className="text-xs text-yellow-600">Generating planning script...</span>
            </div>
          )}
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(call.status)}`}>
          {call.status === 'pending' ? 'automatic' : call.status}
        </span>
      </div>
      <button
        onClick={() => handleViewDetails(call)}
        className="w-full mt-2 flex items-center justify-center space-x-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
      >
        <span>View Details</span>
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )

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
            <p className="text-gray-600 mt-1">Manage planned, scheduled, and completed calls</p>
          </div>
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

      {/* JIRA-like 3 Column Layout */}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Planned Calls Column */}
          <div>
            <div className="bg-purple-50 border border-purple-200 rounded-t-lg p-4">
              <h2 className="text-lg font-semibold text-purple-900">Planned Calls</h2>
              <p className="text-sm text-purple-700">{plannedCalls.length} calls</p>
            </div>
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 min-h-[400px]">
              {plannedCalls.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No planned calls</p>
              ) : (
                plannedCalls.map((call) => <CallCard key={call.id} call={call} />)
              )}
            </div>
          </div>

          {/* Automatic Calls Column */}
          <div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-t-lg p-4">
              <h2 className="text-lg font-semibold text-yellow-900">Scheduled Automatic Calls</h2>
              <p className="text-sm text-yellow-700">{automaticCalls.length} calls</p>
            </div>
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 min-h-[400px]">
              {automaticCalls.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No automatic calls</p>
              ) : (
                automaticCalls.map((call) => <CallCard key={call.id} call={call} />)
              )}
            </div>
          </div>

          {/* Completed Calls Column */}
          <div>
            <div className="bg-green-50 border border-green-200 rounded-t-lg p-4">
              <h2 className="text-lg font-semibold text-green-900">Completed Calls</h2>
              <p className="text-sm text-green-700">{completedCalls.length} calls</p>
            </div>
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 min-h-[400px]">
              {completedCalls.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No completed calls</p>
              ) : (
                completedCalls.map((call) => <CallCard key={call.id} call={call} />)
              )}
            </div>
          </div>
        </div>
      )}

      {/* Call Details Modal */}
      {showDetailsModal && selectedCall && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Call Details</h3>
              <button
                onClick={() => {
                  setShowDetailsModal(false)
                  setSelectedCall(null)
                  setPlanningContent(null)
                  setTranscriptContent(null)
                  setPlanningExpanded(false)
                  setTranscriptExpanded(false)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {loadingDetails ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-2 text-gray-600">Loading details...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Call Info */}
                <div className="border-b border-gray-200 pb-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Date:</span>
                      <span className="ml-2 font-medium">
                        {selectedCall.scheduled_time
                          ? format(new Date(selectedCall.scheduled_time), 'MMM d, yyyy h:mm a')
                          : format(new Date(selectedCall.timestamp), 'MMM d, yyyy h:mm a')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Status:</span>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded ${getStatusBadge(selectedCall.status)}`}>
                        {selectedCall.status}
                      </span>
                    </div>
                    {selectedCall.duration_seconds && (
                      <div>
                        <span className="text-gray-500">Duration:</span>
                        <span className="ml-2 font-medium">
                          {Math.floor(selectedCall.duration_seconds / 60)}m {selectedCall.duration_seconds % 60}s
                        </span>
                      </div>
                    )}
                    {selectedCall.outcome && (
                      <div>
                        <span className="text-gray-500">Outcome:</span>
                        <span className="ml-2 font-medium">{selectedCall.outcome}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Planning File */}
                {planningContent && (
                  <div>
                    <div className="w-full flex items-center justify-between mb-2">
                      <button
                        onClick={() => setPlanningExpanded(!planningExpanded)}
                        className="flex items-center text-left flex-1"
                      >
                        {planningExpanded ? (
                          <ChevronDown className="h-5 w-5 text-gray-400 mr-2" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-400 mr-2" />
                        )}
                        <h4 className="text-lg font-semibold text-gray-900">Planning File</h4>
                      </button>
                      <button
                        onClick={() => handleDeleteFile('planning')}
                        className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                        title="Delete planning file"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                    {planningExpanded && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 prose max-w-none">
                        <ReactMarkdown>{planningContent}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}

                {/* Transcript */}
                {transcriptContent && (
                  <div>
                    <div className="w-full flex items-center justify-between mb-2">
                      <button
                        onClick={() => setTranscriptExpanded(!transcriptExpanded)}
                        className="flex items-center text-left flex-1"
                      >
                        {transcriptExpanded ? (
                          <ChevronDown className="h-5 w-5 text-gray-400 mr-2" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-400 mr-2" />
                        )}
                        <h4 className="text-lg font-semibold text-gray-900">Transcript</h4>
                      </button>
                      <button
                        onClick={() => handleDeleteFile('transcript')}
                        className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                        title="Delete transcript file"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                    {transcriptExpanded && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 prose max-w-none">
                        <ReactMarkdown>{transcriptContent}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}

                {/* Upload Files Button */}
                <div className="flex justify-end">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Files
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Files Modal */}
      {showUploadModal && selectedCall && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload File</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  accept=".txt,.json,.md"
                  onChange={handleFileSelect}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {selectedFile && (
                  <p className="mt-2 text-sm text-gray-600">Selected: {selectedFile.name}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Type
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="fileType"
                      value="transcript"
                      checked={fileType === 'transcript'}
                      onChange={(e) => setFileType(e.target.value)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Transcript</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="fileType"
                      value="planning_notes"
                      checked={fileType === 'planning_notes'}
                      onChange={(e) => setFileType(e.target.value)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Planning Notes</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="fileType"
                      value="other"
                      checked={fileType === 'other'}
                      onChange={(e) => setFileType(e.target.value)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Other Info</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setSelectedFile(null)
                  setFileType('transcript')
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
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CallHistory
