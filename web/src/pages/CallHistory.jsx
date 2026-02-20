import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import { useToastContext } from '../App'
import ConfirmModal from '../components/ConfirmModal'
import {
  ArrowLeft,
  Phone,
  Mail,
  Upload,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  X,
  ChevronRight,
  ChevronDown,
  Trash2,
  Edit,
  Check,
  Send,
  Info,
} from 'lucide-react'
import { format } from 'date-fns'

function CallHistory() {
  console.log('CallHistory component rendering')
  const { id } = useParams()
  console.log('Customer ID from params:', id)
  const toast = useToastContext()
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
  const [transcriptExpanded, setTranscriptExpanded] = useState(false)
  const [showCancelCallModal, setShowCancelCallModal] = useState(false)
  const [callToCancel, setCallToCancel] = useState(null)
  const [showDeleteFileModal, setShowDeleteFileModal] = useState(false)
  const [fileToDelete, setFileToDelete] = useState(null)
  const [editingEmail, setEditingEmail] = useState(false)
  const [editedEmailContent, setEditedEmailContent] = useState('')
  const [editedEmailSubject, setEditedEmailSubject] = useState('')
  const [savingEmail, setSavingEmail] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [scheduleDateTime, setScheduleDateTime] = useState('')
  const [scheduleNotes, setScheduleNotes] = useState('')
  const [useAutoTime, setUseAutoTime] = useState(false)
  const [suggestedTime, setSuggestedTime] = useState(null)
  const [suggestedDay, setSuggestedDay] = useState(null)
  const [schedulingPlannedCallId, setSchedulingPlannedCallId] = useState(null)
  const [timeSlots, setTimeSlots] = useState([])
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false)
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null)
  const [scheduling, setScheduling] = useState(false)
  const [showRawJson, setShowRawJson] = useState(false)
  const isPollingRef = useRef(false)

  const formatScriptKey = (key) =>
    key.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

  const renderScriptValue = (value, key) => {
    if (value === null || value === undefined)
      return <span className="text-gray-400 italic">N/A</span>

    if (key === 'risk_level') {
      const colors = {
        low: 'bg-green-100 text-green-800 border border-green-200',
        moderate: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
        high: 'bg-red-100 text-red-800 border border-red-200',
        vip: 'bg-purple-100 text-purple-800 border border-purple-200',
      }
      const v = String(value).toLowerCase()
      return <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${colors[v] || 'bg-gray-100 text-gray-700 border border-gray-200'}`}>{value}</span>
    }

    if (key === 'communication_channel') {
      const colors = {
        call: 'bg-blue-100 text-blue-800 border border-blue-200',
        email: 'bg-indigo-100 text-indigo-800 border border-indigo-200',
        sms: 'bg-orange-100 text-orange-800 border border-orange-200',
      }
      const v = String(value).toLowerCase()
      return <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${colors[v] || 'bg-gray-100 text-gray-700 border border-gray-200'}`}>{value}</span>
    }

    if (key === 'tone_recommendation' && typeof value === 'string' && value.includes('|')) {
      return (
        <div className="flex flex-wrap gap-1.5">
          {value.split('|').map((t, i) => (
            <span key={i} className="px-2 py-0.5 bg-tangerine-50 text-tangerine-700 border border-tangerine-200 rounded-full text-xs font-medium capitalize">
              {t.trim().replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )
    }

    if ((key === 'best_contact_time' || key === 'best_contact_day') && typeof value === 'string')
      return <span className="capitalize font-medium text-gray-800">{value}</span>

    if (key === 'suggested_payment_amount' && typeof value === 'number')
      return <span className="font-semibold text-gray-900">${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>

    if (typeof value === 'boolean')
      return value ? (
        <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">Yes</span>
      ) : (
        <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">No</span>
      )
    if (Array.isArray(value)) {
      if (value.length === 0) return <span className="text-gray-400 italic">None</span>
      return (
        <ul className="space-y-1.5">
          {value.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-tangerine-400 flex-shrink-0" />
              {String(item)}
            </li>
          ))}
        </ul>
      )
    }
    if (typeof value === 'number') return value.toLocaleString()
    if (typeof value === 'object')
      return <pre className="text-xs whitespace-pre-wrap break-words bg-gray-50 p-2 rounded">{JSON.stringify(value, null, 2)}</pre>
    return <span className="whitespace-pre-wrap">{String(value)}</span>
  }

  const fetchCallHistory = async () => {
    if (!id) {
      setError('Customer ID is required')
      setLoading(false)
      return Promise.resolve()
    }
    
    try {
      // Don't set loading to true if we're just polling (to avoid scroll reset)
      // Only show loading on initial load or manual refresh
      // Only show loading spinner on initial load
      const isInitialLoad = loading && plannedCalls.length === 0 && automaticCalls.length === 0 && completedCalls.length === 0
      if (isInitialLoad) {
        setLoading(true)
      }
      setError(null)
      const response = await api.get(`/customers/${id}/call-history`)
      console.log('Call history response:', response.data)
      
      // Ensure we have arrays
      const planned = Array.isArray(response.data?.planned) ? response.data.planned : []
      const automatic = Array.isArray(response.data?.automatic) ? response.data.automatic : []
      const completed = Array.isArray(response.data?.completed) ? response.data.completed : []
      
      // Only update state if data actually changed (to prevent unnecessary re-renders and scroll reset)
      setPlannedCalls(prev => {
        const prevStr = JSON.stringify(prev)
        const newStr = JSON.stringify(planned)
        return prevStr === newStr ? prev : planned
      })
      setAutomaticCalls(prev => {
        const prevStr = JSON.stringify(prev)
        const newStr = JSON.stringify(automatic)
        return prevStr === newStr ? prev : automatic
      })
      setCompletedCalls(prev => {
        const prevStr = JSON.stringify(prev)
        const newStr = JSON.stringify(completed)
        return prevStr === newStr ? prev : completed
      })
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load call history'
      setError(errorMessage)
      console.error('Error loading call history:', err)
      console.error('Error response:', err.response)
      
      // Set empty arrays on error so UI still renders
      setPlannedCalls([])
      setAutomaticCalls([])
      setCompletedCalls([])
    } finally {
      setLoading(false)
    }
    return Promise.resolve()
  }

  useEffect(() => {
    if (id) {
      fetchCallHistory()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])
  
  // Poll for planning script updates (only when there are planned calls without scripts)
  useEffect(() => {
    // Don't poll if loading, no planned calls, or already polling
    if (loading || !plannedCalls || plannedCalls.length === 0 || isPollingRef.current) return
    
    const interval = setInterval(() => {
      // Check if there are planned calls without planning scripts
      const hasPendingPlanning = plannedCalls.some(
        call => !call.planning_script
      )
      if (hasPendingPlanning && !loading && !isPollingRef.current) {
        isPollingRef.current = true
        fetchCallHistory().finally(() => {
          isPollingRef.current = false
        })
      }
    }, 5000) // Poll every 5 seconds
    
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, plannedCalls, loading])

  const handleViewDetails = async (call) => {
    setSelectedCall(call)
    setShowDetailsModal(true)
    setLoadingDetails(true)
    setPlanningContent(null)
    setTranscriptContent(null)
    setTranscriptExpanded(false)
    setShowRawJson(false)
    setEditingEmail(false)
    setEditedEmailContent('')
    setEditedEmailSubject('')

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
              : call.id.startsWith('email_')
              ? call.id.replace('email_', '')
              : call.scheduled_call_id || call.id
            const response = await api.get(`/call-history/scheduled_${planningId}/planning-file`)
            setPlanningContent(response.data.content)
          }
        } catch (err) {
          console.warn('Could not load planning file:', err)
        }
      }
      
      // For emails, content is shown separately in the email content section

      // Load transcript — use the value already in the call object (no extra API call needed)
      if (call.transcript) {
        setTranscriptContent(call.transcript)
        setTranscriptExpanded(true)
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
      toast.info('Please select a file and ensure a call is selected', {
        title: 'File Selection Required',
      })
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
      toast.success('File uploaded successfully!', {
        title: 'Upload Complete',
      })
      setShowUploadModal(false)
      setSelectedFile(null)
      setFileType('transcript')
      handleViewDetails(selectedCall) // Refresh details
      fetchCallHistory()
    } catch (err) {
      toast.error('Failed to upload file', {
        title: 'Upload Failed',
      })
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteFileClick = (fileType) => {
    setFileToDelete(fileType)
    setShowDeleteFileModal(true)
  }

  const handleDeleteFile = async () => {
    if (!selectedCall || !fileToDelete) return

    try {
      // Determine call_id for the API
      let callId = selectedCall.id
      if (callId.startsWith('scheduled_')) {
        callId = callId.replace('scheduled_', '')
      } else if (selectedCall.scheduled_call_id) {
        callId = selectedCall.scheduled_call_id.toString()
      } else if (fileToDelete === 'transcript' && selectedCall.type === 'completed') {
        callId = selectedCall.id.toString()
      }

      await api.delete(`/call-history/${callId}/file`, {
        params: { file_type: fileToDelete }
      })
      
      toast.success(`${fileToDelete.charAt(0).toUpperCase() + fileToDelete.slice(1)} file deleted successfully!`, {
        title: 'File Deleted',
      })
      
      // Clear the content from state
      if (fileToDelete === 'planning') {
        setPlanningContent(null)
      } else if (fileToDelete === 'transcript') {
        setTranscriptContent(null)
      }
      
      // Refresh call history and details
      setShowDeleteFileModal(false)
      setFileToDelete(null)
      fetchCallHistory()
      handleViewDetails(selectedCall)
    } catch (err) {
      toast.error(`Failed to delete ${fileToDelete} file`, {
        title: 'Delete Failed',
      })
      console.error(err)
    }
  }

  const handleSendEmail = async (emailId) => {
    try {
      await api.post(`/customers/${id}/send-email/${emailId}`)
      toast.success('Email sent successfully', {
        title: 'Email Sent',
      })
      fetchCallHistory()
      handleViewDetails(selectedCall) // Refresh details
    } catch (err) {
      toast.error('Failed to send email: ' + (err.response?.data?.detail || err.message), {
        title: 'Send Failed',
      })
      console.error(err)
    }
  }

  const handleSaveEditedEmail = async () => {
    if (!selectedCall) return
    
    // Extract email ID from call
    const callIdStr = String(selectedCall.id || '')
    let emailId = null
    if (callIdStr.startsWith('email_')) {
      emailId = callIdStr.replace('email_', '')
    } else if (selectedCall.communication_type === 'email' || selectedCall.communication_type === 'sms') {
      // If it's an email but doesn't have email_ prefix, try to get ID from the call object
      emailId = selectedCall.id
    }
    
    if (!emailId) {
      toast.error('Could not determine email ID', {
        title: 'Error',
      })
      return
    }
    
    try {
      setSavingEmail(true)
      await api.put(`/customers/${id}/planned-email/${emailId}`, {
        subject: editedEmailSubject,
        content: editedEmailContent
      })
      
      toast.success('Email updated successfully', {
        title: 'Email Updated',
      })
      
      // Update selected call with edited content
      setSelectedCall({
        ...selectedCall,
        subject: editedEmailSubject,
        content: editedEmailContent
      })
      setEditingEmail(false)
      fetchCallHistory()
      handleViewDetails(selectedCall) // Refresh details
    } catch (err) {
      toast.error('Failed to save email: ' + (err.response?.data?.detail || err.message), {
        title: 'Save Failed',
      })
      console.error(err)
    } finally {
      setSavingEmail(false)
    }
  }

  const openScheduleModal = async (callId) => {
    setSchedulingPlannedCallId(callId)
    setShowScheduleModal(true)
    setLoadingTimeSlots(true)
    setSelectedTimeSlot(null)
    
    try {
      // Fetch suggested time slots
      const response = await api.get(`/customers/${id}/suggested-time-slots`)
      setTimeSlots(response.data.time_slots || [])
      
      // Get planning script for this call to extract suggested time
      try {
        const scriptsResponse = await api.get(`/customers/${id}/call-planning-scripts`, {
          params: { scheduled_call_id: callId }
        })
        if (scriptsResponse.data.length > 0) {
          const script = scriptsResponse.data[0]
          setSuggestedTime(script.suggested_time)
          setSuggestedDay(script.suggested_day)
        }
      } catch (err) {
        // Planning script might not exist yet, that's okay
        console.warn('Could not load planning script:', err)
      }
    } catch (err) {
      toast.error('Failed to load time slots: ' + (err.response?.data?.detail || err.message), {
        title: 'Error',
      })
      console.error(err)
    } finally {
      setLoadingTimeSlots(false)
    }
  }

  const handleScheduleCall = async () => {
    // Determine the scheduled time: selected slot > manual input > auto
    let finalDateTime = null
    if (selectedTimeSlot) {
      finalDateTime = selectedTimeSlot.start_time
    } else if (scheduleDateTime) {
      finalDateTime = scheduleDateTime
    } else if (useAutoTime) {
      // Will be handled by backend
    } else {
      toast.info('Please select a time slot, enter a date/time manually, or choose automatic time selection', {
        title: 'Time Selection Required',
      })
      return
    }

    try {
      setScheduling(true)
      
      // Convert to ISO string format if needed
      let scheduledTimeForAPI = null
      if (finalDateTime) {
        // If it's already an ISO string from time slot, use as-is
        if (finalDateTime.includes('T') && finalDateTime.includes('Z')) {
          scheduledTimeForAPI = finalDateTime
        } else if (finalDateTime.includes('T')) {
          // ISO string without Z, add it
          scheduledTimeForAPI = finalDateTime + 'Z'
        } else {
          // Convert datetime-local to ISO
          scheduledTimeForAPI = new Date(finalDateTime).toISOString()
        }
      }
      
      await api.post(`/scheduled-calls/${schedulingPlannedCallId}/schedule`, {
        scheduled_time: scheduledTimeForAPI || null,
        use_auto_time: useAutoTime && !finalDateTime,
      })
      
      toast.success('Call scheduled successfully!', {
        title: 'Call Scheduled',
        message: 'Strategy planning has started in the background. The planning file will be available shortly.',
        duration: 6000,
      })
      
      setShowScheduleModal(false)
      setScheduleDateTime('')
      setScheduleNotes('')
      setUseAutoTime(false)
      setSchedulingPlannedCallId(null)
      setSuggestedTime(null)
      setSuggestedDay(null)
      setSelectedTimeSlot(null)
      setTimeSlots([])
      fetchCallHistory()
    } catch (err) {
      toast.error('Failed to schedule call: ' + (err.response?.data?.detail || err.message), {
        title: 'Scheduling Failed',
      })
      console.error(err)
    } finally {
      setScheduling(false)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-800',
      planned: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      done: 'bg-green-100 text-green-800',
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

  const handleCancelCallClick = (callId) => {
    setCallToCancel(callId)
    setShowCancelCallModal(true)
  }

  const handleCancelCall = async () => {
    if (!callToCancel) return

    try {
      const callIdStr = String(callToCancel)
      
      // Check if it's an email (starts with "email_")
      if (callIdStr.startsWith('email_')) {
        const emailId = callIdStr.replace('email_', '')
        await api.delete(`/customers/${id}/planned-email/${emailId}`)
        
        toast.success('Email cancelled successfully', {
          title: 'Email Cancelled',
        })
      } else {
        // It's a scheduled call
        let scheduledCallId = callToCancel
        if (callToCancel.startsWith('scheduled_')) {
          scheduledCallId = callToCancel.replace('scheduled_', '')
        }
        
        await api.delete(`/scheduled-calls/${scheduledCallId}`)
        
        toast.success('Call cancelled successfully', {
          title: 'Call Cancelled',
        })
      }
      
      setShowCancelCallModal(false)
      setCallToCancel(null)
      fetchCallHistory()
    } catch (err) {
      toast.error('Failed to cancel: ' + (err.response?.data?.detail || err.message), {
        title: 'Cancel Failed',
      })
      console.error(err)
    }
  }

  const CallCard = ({ call }) => {
    // Safety check
    if (!call || call.id === undefined || call.id === null) {
      return null
    }
    
    // Determine the call ID for cancellation
    const getCallId = () => {
      const idStr = String(call.id) // Convert to string for safe string operations
      if (idStr.startsWith('scheduled_')) {
        return idStr
      } else if (idStr.startsWith('email_')) {
        // Keep the full email_ prefix for emails so we can identify them
        return idStr
      } else if (call.scheduled_call_id) {
        return `scheduled_${call.scheduled_call_id}`
      }
      return idStr
    }

    const canCancel = call.status === 'pending' || call.status === 'planned'
    const callId = getCallId()
    const idStr = String(call.id || '')
    const isEmail = call.communication_type === 'email' || call.communication_type === 'sms' || idStr.startsWith('email_')
    const Icon = isEmail ? Mail : Phone

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <Icon className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-900">
                {call.scheduled_time 
                  ? format(new Date(call.scheduled_time), 'MMM d, h:mm a')
                  : call.sent_at
                  ? format(new Date(call.sent_at), 'MMM d, h:mm a')
                  : call.timestamp
                  ? format(new Date(call.timestamp), 'MMM d, h:mm a')
                  : 'Date not available'}
              </span>
              {call.outcome && getOutcomeIcon(call.outcome)}
              {isEmail && (
                <span className="text-xs text-gray-500 uppercase">
                  {call.communication_type || 'email'}
                </span>
              )}
            </div>
            {call.subject && (
              <p className="text-xs font-medium text-gray-700 mb-1">Subject: {call.subject}</p>
            )}
            {call.planning_script?.suggested_time && (
              <p className="text-xs text-gray-500 mb-1">
                Suggested: {call.planning_script.suggested_time}
                {call.planning_script.suggested_day && ` on ${call.planning_script.suggested_day}`}
              </p>
            )}
            {(call.notes || call.content) && (
              <p className="text-xs text-gray-600 line-clamp-2">{call.content || call.notes}</p>
            )}
            {call.status === 'planned' && (
              // For emails, check if content exists and is not the placeholder
              // For calls, check if planning_script or planning_file_path exists
              (isEmail 
                ? (!call.content || call.content === 'Generating email content...')
                : (!call.planning_script && !call.planning_file_path)
              ) && (
                <div className="mt-1 flex items-center space-x-1">
                  <Clock className="h-3 w-3 text-yellow-600 animate-spin" />
                  <span className="text-xs text-yellow-600">
                    {isEmail ? 'Generating email content...' : 'Generating planning script...'}
                  </span>
                </div>
              )
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(call.status)}`}>
              {call.status === 'pending' ? 'automatic' : call.status}
            </span>
            {call.status === 'planned' && !isEmail && (
              <button
                onClick={async (e) => {
                  e.stopPropagation()
                  // Extract call ID (remove scheduled_ prefix if present)
                  const callIdStr = String(call.id || '')
                  const actualCallId = callIdStr.startsWith('scheduled_') 
                    ? callIdStr.replace('scheduled_', '')
                    : call.scheduled_call_id || callIdStr
                  await openScheduleModal(parseInt(actualCallId))
                }}
                className="px-2 py-1 text-xs font-medium text-tangerine-500 hover:text-tangerine-600 hover:bg-tangerine-50 rounded transition-colors"
                title="Schedule this call"
              >
                Schedule
              </button>
            )}
            {canCancel && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleCancelCallClick(callId)
                }}
                className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                title={`Cancel ${isEmail ? 'email' : 'call'}`}
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <button
          onClick={() => handleViewDetails(call)}
          className="w-full mt-2 flex items-center justify-center space-x-1 text-sm text-tangerine-500 hover:text-tangerine-600 font-medium"
        >
          <span>View Details</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    )
  }

  // Safety check for id - after all hooks
  console.log('Rendering with id:', id)
  
  if (!id) {
    console.log('No ID found, showing error')
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Invalid customer ID
        </div>
        <Link
          to="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mt-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customers
        </Link>
      </div>
    )
  }

  console.log('Rendering main content')
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            <h1 className="text-3xl font-bold text-gray-900">Interaction History</h1>
            <p className="text-gray-600 mt-1">Manage planned, scheduled, and completed interactions (calls, emails, SMS)</p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500"></div>
          <p className="mt-2 text-gray-600">Loading interaction history...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* JIRA-like 3 Column Layout */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Planned Calls Column */}
          <div>
            <div className="bg-purple-50 border border-purple-200 rounded-t-lg p-4">
              <h2 className="text-lg font-semibold text-purple-900">Planned Interactions</h2>
              <p className="text-sm text-purple-700">{plannedCalls.length} items</p>
            </div>
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 h-[calc(100vh-18rem)] overflow-y-auto">
              {plannedCalls.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No planned interactions</p>
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
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 h-[calc(100vh-18rem)] overflow-y-auto">
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
              <h2 className="text-lg font-semibold text-green-900">Completed Interactions</h2>
              <p className="text-sm text-green-700">{completedCalls.length} items</p>
            </div>
            <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 h-[calc(100vh-18rem)] overflow-y-auto">
              {completedCalls.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No completed interactions</p>
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
              <h3 className="text-xl font-semibold text-gray-900">Interaction Details</h3>
              <button
                onClick={() => {
                  setShowDetailsModal(false)
                  setSelectedCall(null)
                  setPlanningContent(null)
                  setTranscriptContent(null)
                  setTranscriptExpanded(false)
                  setShowRawJson(false)
                  setEditingEmail(false)
                  setEditedEmailContent('')
                  setEditedEmailSubject('')
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {loadingDetails ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500"></div>
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
                          : selectedCall.sent_at
                          ? format(new Date(selectedCall.sent_at), 'MMM d, yyyy h:mm a')
                          : selectedCall.timestamp
                          ? format(new Date(selectedCall.timestamp), 'MMM d, yyyy h:mm a')
                          : 'Date not available'}
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
                    {selectedCall.conversation_id && (
                      <div className="col-span-2">
                        <span className="text-gray-500">Conversation ID:</span>
                        <span className="ml-2 font-mono text-xs text-gray-700 break-all">{selectedCall.conversation_id}</span>
                      </div>
                    )}
                    {selectedCall.call_sid && (
                      <div className="col-span-2">
                        <span className="text-gray-500">Call SID:</span>
                        <span className="ml-2 font-mono text-xs text-gray-700 break-all">{selectedCall.call_sid}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Email Content (for emails/SMS) */}
                {(selectedCall.communication_type === 'email' || selectedCall.communication_type === 'sms') && selectedCall.content && (
                  <div>
                    <div className="w-full flex items-center justify-between mb-2">
                      <h4 className="text-lg font-semibold text-gray-900">
                        {selectedCall.communication_type === 'email' ? 'Email' : 'SMS'} Content
                      </h4>
                      {(selectedCall.status === 'planned' || selectedCall.status === 'pending') && (
                        <div className="flex items-center space-x-2">
                          {editingEmail ? (
                            <>
                              <button
                                onClick={() => {
                                  setEditingEmail(false)
                                  setEditedEmailContent(selectedCall.content || '')
                                  setEditedEmailSubject(selectedCall.subject || '')
                                }}
                                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                              >
                                Cancel
                              </button>
                              <button
                                onClick={handleSaveEditedEmail}
                                disabled={savingEmail}
                                className="px-3 py-1 text-sm bg-tangerine-500 text-white rounded hover:bg-tangerine-600 disabled:opacity-50 flex items-center space-x-1"
                              >
                                {savingEmail ? (
                                  <>
                                    <div className="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                                    <span>Saving...</span>
                                  </>
                                ) : (
                                  <>
                                    <Check className="h-3 w-3" />
                                    <span>Save</span>
                                  </>
                                )}
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditingEmail(true)
                                  setEditedEmailContent(selectedCall.content || '')
                                  setEditedEmailSubject(selectedCall.subject || '')
                                }}
                                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center space-x-1"
                                title="Edit email"
                              >
                                <Edit className="h-3 w-3" />
                                <span>Edit</span>
                              </button>
                              {selectedCall.status === 'planned' && (
                                <button
                                  onClick={() => {
                                    const callIdStr = String(selectedCall.id || '')
                                    const emailId = callIdStr.startsWith('email_') 
                                      ? callIdStr.replace('email_', '') 
                                      : selectedCall.id
                                    handleSendEmail(emailId)
                                  }}
                                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center space-x-1"
                                  title="Send email"
                                >
                                  <Send className="h-3 w-3" />
                                  <span>Send</span>
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                    {selectedCall.subject && (
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Subject
                        </label>
                        {editingEmail ? (
                          <input
                            type="text"
                            value={editedEmailSubject}
                            onChange={(e) => setEditedEmailSubject(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
                            placeholder="Email subject"
                          />
                        ) : (
                          <p className="text-sm font-medium text-gray-900 bg-gray-50 p-3 rounded-lg">
                            {selectedCall.subject || 'No subject'}
                          </p>
                        )}
                      </div>
                    )}
                    {editingEmail ? (
                      <textarea
                        value={editedEmailContent}
                        onChange={(e) => setEditedEmailContent(e.target.value)}
                        rows={15}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent font-mono text-sm"
                        placeholder="Email content"
                      />
                    ) : (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <div className="prose max-w-none whitespace-pre-wrap text-sm">
                          {selectedCall.content}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* AI Summary */}
                {selectedCall.notes && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">AI Summary</h4>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-gray-800 whitespace-pre-wrap">
                      {selectedCall.notes}
                    </div>
                  </div>
                )}
                
                {/* Planning File */}
                {planningContent && (
                  <div>
                    <div className="w-full flex items-center justify-between mb-3">
                      <h4 className="text-lg font-semibold text-gray-900">Call Planning Strategy</h4>
                      <button
                        onClick={() => handleDeleteFileClick('planning')}
                        className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                        title="Delete planning file"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                    {(() => {
                      let parsed = null
                      try {
                        let raw = typeof planningContent === 'string'
                          ? planningContent
                          : JSON.stringify(planningContent)
                        raw = raw.replace(/^```[\w]*\n?/, '').replace(/\n?```$/, '').trim()
                        parsed = JSON.parse(raw)
                      } catch (e) {}

                      if (!parsed || showRawJson) {
                        return (
                          <div>
                            <pre className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-xs overflow-auto whitespace-pre-wrap break-words">
                              {(typeof planningContent === 'string'
                                ? planningContent
                                : JSON.stringify(planningContent, null, 2)
                              ).replace(/^```[\w]*\n?/, '').replace(/\n?```$/, '').trim()}
                            </pre>
                            {parsed && (
                              <button
                                onClick={() => setShowRawJson(false)}
                                className="mt-2 text-xs text-tangerine-500 hover:text-tangerine-600 underline"
                              >
                                View Formatted Table
                              </button>
                            )}
                          </div>
                        )
                      }

                      return (
                        <div>
                          <div className="border border-gray-200 rounded-lg overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                              <tbody className="divide-y divide-gray-100">
                                {Object.entries(parsed).map(([key, value], idx) => (
                                  <tr key={key} className={idx % 2 === 0 ? 'bg-white hover:bg-gray-50' : 'bg-gray-50/50 hover:bg-gray-100/60'}>
                                    <td className="px-4 py-3 text-sm font-medium text-gray-500 w-2/5 align-top whitespace-nowrap">
                                      <span className="inline-flex items-center gap-1.5">
                                        {formatScriptKey(key)}
                                        {key === 'profile_type' && (
                                          <Link
                                            to="/profile-types"
                                            target="_blank"
                                            title="Learn about profile types"
                                            className="text-gray-400 hover:text-tangerine-500 transition-colors"
                                          >
                                            <Info className="h-3.5 w-3.5" />
                                          </Link>
                                        )}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-900 align-top">
                                      {renderScriptValue(value, key)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <button
                            onClick={() => setShowRawJson(true)}
                            className="mt-3 text-xs text-gray-400 hover:text-gray-600 underline"
                          >
                            View Raw JSON
                          </button>
                        </div>
                      )
                    })()}
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
                        onClick={() => handleDeleteFileClick('transcript')}
                        className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                        title="Delete transcript file"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                    {transcriptExpanded && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm space-y-1 max-h-96 overflow-y-auto">
                        {transcriptContent.split('\n').filter(Boolean).map((line, i) => {
                          const isAgent = line.startsWith('Agent:')
                          const isUser = line.startsWith('User:') || line.startsWith('Customer:')
                          return (
                            <p key={i} className={`${isAgent ? 'text-blue-800' : isUser ? 'text-gray-800' : 'text-gray-500'}`}>
                              {line}
                            </p>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Upload Files Button */}
                {selectedCall.status !== 'done' && selectedCall.status !== 'completed' && (
                <div className="flex justify-end">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="inline-flex items-center px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Files
                  </button>
                </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Schedule Call Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Schedule Planned Call
            </h3>
            {suggestedTime && (
              <div className="mb-4 bg-tangerine-50 border border-tangerine-200 rounded-lg p-3">
                <p className="text-sm text-tangerine-900">
                  <strong>Suggested from planning:</strong> {suggestedTime}
                  {suggestedDay && ` on ${suggestedDay}`}
                </p>
              </div>
            )}
            <div className="space-y-4">
              {/* Suggested Time Slots */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Suggested Time Slots (10-minute windows)
                </label>
                {loadingTimeSlots ? (
                  <div className="text-center py-4">
                    <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-tangerine-500"></div>
                    <p className="text-xs text-gray-500 mt-2">Loading time slots...</p>
                  </div>
                ) : timeSlots.length > 0 ? (
                  <div className="space-y-2">
                    {timeSlots.map((slot, index) => (
                      <button
                        key={index}
                        type="button"
                        onClick={() => {
                          setSelectedTimeSlot(slot)
                          setScheduleDateTime('')
                          setUseAutoTime(false)
                        }}
                        className={`w-full text-left px-4 py-3 border-2 rounded-lg transition-colors ${
                          selectedTimeSlot?.start_time === slot.start_time
                            ? 'border-tangerine-500 bg-tangerine-50'
                            : 'border-gray-200 hover:border-tangerine-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{slot.display}</p>
                            <p className="text-xs text-gray-500 mt-1">10-minute window</p>
                          </div>
                          {selectedTimeSlot?.start_time === slot.start_time && (
                            <CheckCircle className="h-5 w-5 text-tangerine-500" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No time slots available</p>
                )}
              </div>
              
              {/* Manual Date & Time Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Or Enter Date & Time Manually
                </label>
                <input
                  type="datetime-local"
                  value={scheduleDateTime}
                  onChange={(e) => {
                    setScheduleDateTime(e.target.value)
                    setSelectedTimeSlot(null)
                    setUseAutoTime(false)
                  }}
                  disabled={useAutoTime}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>
              
              {/* Automatic Time Selection */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="useAutoTime"
                  checked={useAutoTime}
                  onChange={(e) => {
                    setUseAutoTime(e.target.checked)
                    if (e.target.checked) {
                      setScheduleDateTime('')
                      setSelectedTimeSlot(null)
                    }
                  }}
                  className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500 border-gray-300 rounded"
                />
                <label htmlFor="useAutoTime" className="ml-2 block text-sm text-gray-700">
                  Use time from planning file
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={scheduleNotes}
                  onChange={(e) => setScheduleNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
                  placeholder="Add any notes about this call..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowScheduleModal(false)
                  setScheduleDateTime('')
                  setScheduleNotes('')
                  setUseAutoTime(false)
                  setSchedulingPlannedCallId(null)
                  setSuggestedTime(null)
                  setSuggestedDay(null)
                  setSelectedTimeSlot(null)
                  setTimeSlots([])
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleScheduleCall}
                disabled={scheduling}
                className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 disabled:opacity-50"
              >
                {scheduling ? 'Scheduling...' : 'Schedule Call'}
              </button>
            </div>
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
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
                      className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500"
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
                      className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500"
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
                      className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500"
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
                className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Call Confirmation Modal */}
      <ConfirmModal
        isOpen={showCancelCallModal}
        onClose={() => {
          setShowCancelCallModal(false)
          setCallToCancel(null)
        }}
        onConfirm={handleCancelCall}
        title="Cancel Scheduled Call"
        message="Are you sure you want to cancel this scheduled call? This action cannot be undone."
        confirmText="Cancel Call"
        cancelText="Keep Scheduled"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        isLoading={false}
      />

      {/* Delete File Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteFileModal}
        onClose={() => {
          setShowDeleteFileModal(false)
          setFileToDelete(null)
        }}
        onConfirm={handleDeleteFile}
        title={`Delete ${fileToDelete ? fileToDelete.charAt(0).toUpperCase() + fileToDelete.slice(1) : ''} File`}
        message={fileToDelete ? `Are you sure you want to delete this ${fileToDelete} file? This action cannot be undone.` : ''}
        confirmText="Delete File"
        cancelText="Keep File"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        isLoading={false}
      />
    </div>
  )
}

export default CallHistory
