import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useToastContext } from '../App'
import ConfirmModal from '../components/ConfirmModal'
import {
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  DollarSign,
  Calendar,
  Clock,
  FileText,
  Upload,
  CheckCircle,
  XCircle,
  User,
  Briefcase,
  CreditCard,
  X,
  BookOpen,
  Sparkles,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Edit,
  Check,
} from 'lucide-react'
import { format } from 'date-fns'
import ReactMarkdown from 'react-markdown'

function CustomerDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToastContext()
  const [customer, setCustomer] = useState(null)
  const [debts, setDebts] = useState([])
  const [scheduledCalls, setScheduledCalls] = useState([])
  const [callPlanningScripts, setCallPlanningScripts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scheduling, setScheduling] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [showPrepareModal, setShowPrepareModal] = useState(false)
  const [showPrepareConfirmModal, setShowPrepareConfirmModal] = useState(false)
  const [showScriptModal, setShowScriptModal] = useState(false)
  const [selectedScript, setSelectedScript] = useState(null)
  const [scheduleDateTime, setScheduleDateTime] = useState('')
  const [scheduleNotes, setScheduleNotes] = useState('')
  const [useAutoTime, setUseAutoTime] = useState(false)
  const [suggestedTime, setSuggestedTime] = useState(null)
  const [suggestedDay, setSuggestedDay] = useState(null)
  const [prepareResult, setPrepareResult] = useState(null)
  const [schedulingPlannedCallId, setSchedulingPlannedCallId] = useState(null)
  const [timeSlots, setTimeSlots] = useState([])
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false)
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null)
  const [prepareScriptExpanded, setPrepareScriptExpanded] = useState(false)
  const [viewScriptExpanded, setViewScriptExpanded] = useState(false)
  const [showCancelCallModal, setShowCancelCallModal] = useState(false)
  const [callToCancel, setCallToCancel] = useState(null)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailType, setEmailType] = useState('email') // 'email' or 'sms'
  const [preparingEmail, setPreparingEmail] = useState(false)
  const [plannedEmails, setPlannedEmails] = useState([])
  const [showEmailPreviewModal, setShowEmailPreviewModal] = useState(false)
  const [previewEmail, setPreviewEmail] = useState(null)
  const [editingEmail, setEditingEmail] = useState(false)
  const [editedEmailContent, setEditedEmailContent] = useState('')
  const [editedEmailSubject, setEditedEmailSubject] = useState('')
  const [savingEmail, setSavingEmail] = useState(false)
  const [checkingEmailStatus, setCheckingEmailStatus] = useState(false)

  useEffect(() => {
    fetchCustomerDetail()
  }, [id])
  
  // Poll for planning script updates
  useEffect(() => {
    if (!scheduledCalls || scheduledCalls.length === 0) return
    
    const interval = setInterval(() => {
      // Check if there are planned calls without planning scripts
      const hasPendingPlanning = scheduledCalls.some(
        call => call.status === 'planned' && !call.planning_script
      )
      if (hasPendingPlanning) {
        fetchCustomerDetail()
      }
    }, 5000) // Poll every 5 seconds
    
    return () => clearInterval(interval)
  }, [id, scheduledCalls])

  const fetchCustomerDetail = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/customers/${id}`)
      setCustomer(response.data.customer)
      setDebts(response.data.debts)
      setScheduledCalls(response.data.scheduled_calls)
      setCallPlanningScripts(response.data.call_planning_scripts || [])
      setPlannedEmails(response.data.planned_emails || [])
      setError(null)
    } catch (err) {
      setError('Failed to load customer details')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const openPrepareConfirmModal = () => {
    setShowPrepareConfirmModal(true)
  }

  const handlePrepareCall = async () => {
    try {
      setPreparing(true)
      setShowPrepareConfirmModal(false)
      const response = await api.post(`/customers/${id}/prepare-call`)
      if (response.data && response.data.success !== false) {
        // Show success message
        toast.success('Planning script generation started!', {
          title: 'Call Preparation',
          message: 'The planning script is being generated in the background. You can continue viewing other information while it processes.',
          duration: 6000,
        })
        // Refresh customer details to show the new planned call
        await fetchCustomerDetail()
        // Don't show modal immediately - user can check call history or refresh later
      } else {
        toast.error('Failed to prepare call strategy: ' + (response.data?.error || 'Unknown error'), {
          title: 'Error',
        })
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to prepare call strategy'
      toast.error(`Failed to prepare call strategy: ${errorMsg}`, {
        title: 'Error',
      })
      console.error('Prepare call error:', err)
    } finally {
      setPreparing(false)
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
      
      // If scheduling a planned call, use the schedule endpoint
      if (schedulingPlannedCallId) {
        const response = await api.post(`/scheduled-calls/${schedulingPlannedCallId}/schedule`, {
          scheduled_time: finalDateTime || null,
          use_auto_time: useAutoTime && !finalDateTime,
        })
        toast.success('Call scheduled successfully!', {
          title: 'Call Scheduled',
          message: 'Strategy planning has started in the background. The planning file will be available shortly.',
          duration: 6000,
        })
      } else {
        // Regular scheduling - convert to ISO string format
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
        
        const response = await api.post('/scheduled-calls', {
          customer_id: parseInt(id),
          scheduled_time: scheduledTimeForAPI,
          notes: scheduleNotes,
          agent_id: 'current_user',
          use_auto_time: useAutoTime && !finalDateTime,
        })
        
        toast.success('Call scheduled successfully!', {
          title: 'Call Scheduled',
          message: 'Strategy planning has started in the background. The planning file will be available shortly.',
          duration: 6000,
        })
      }
      
      setShowScheduleModal(false)
      setScheduleDateTime('')
      setScheduleNotes('')
      setUseAutoTime(false)
      setSchedulingPlannedCallId(null)
      setSuggestedTime(null)
      setSuggestedDay(null)
      setSelectedTimeSlot(null)
      setTimeSlots([])
      fetchCustomerDetail()
    } catch (err) {
      toast.error('Failed to schedule call: ' + (err.response?.data?.detail || err.message), {
        title: 'Scheduling Failed',
      })
      console.error(err)
    } finally {
      setScheduling(false)
    }
  }

  const handleCancelCallClick = (callId) => {
    setCallToCancel(callId)
    setShowCancelCallModal(true)
  }

  const handleCancelCall = async () => {
    if (!callToCancel) return

    try {
      await api.delete(`/scheduled-calls/${callToCancel}`)
      toast.success('Call cancelled successfully', {
        title: 'Call Cancelled',
      })
      setShowCancelCallModal(false)
      setCallToCancel(null)
      fetchCustomerDetail()
    } catch (err) {
      toast.error('Failed to cancel call: ' + (err.response?.data?.detail || err.message), {
        title: 'Cancel Failed',
      })
      console.error(err)
    }
  }

  const handleViewScript = async (scriptId) => {
    try {
      const response = await api.get(`/call-planning-scripts/${scriptId}`)
      setSelectedScript(response.data)
      setShowScriptModal(true)
    } catch (err) {
      toast.error('Failed to load script', {
        title: 'Error',
      })
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

  const openScheduleModal = async () => {
    // Fetch suggested time slots when opening modal
    setShowScheduleModal(true)
    setLoadingTimeSlots(true)
    setSelectedTimeSlot(null)
    
    try {
      const response = await api.get(`/customers/${id}/suggested-time-slots`)
      setTimeSlots(response.data.slots || [])
    } catch (err) {
      console.error('Failed to load time slots:', err)
      setTimeSlots([])
    } finally {
      setLoadingTimeSlots(false)
    }
  }

  const handlePrepareEmail = async () => {
    try {
      setPreparingEmail(true)
      setShowEmailModal(false)
      const response = await api.post(`/customers/${id}/prepare-email`, {
        communication_type: emailType
      })
      
      const emailId = response.data.email_id
      
      const loadingToastId = toast.loading('Generating email content...', {
        title: 'Email Generation',
      })
      
      setCheckingEmailStatus(true)
      
      // Poll for email content generation completion
      let checkCount = 0
      const maxChecks = 60 // Maximum 60 checks (120 seconds) - email generation can take longer
      
      const checkEmailReady = async () => {
        checkCount++
        try {
          const emailResponse = await api.get(`/customers/${id}/planned-email/${emailId}`)
          const email = emailResponse.data
          
          // Check if content is generated (not just placeholder)
          if (email.content && email.content !== 'Generating email content...' && email.status === 'planned') {
            // Check if there's an error in the content
            if (email.content.startsWith('Error:')) {
              toast.removeToast(loadingToastId)
              toast.error(email.content, {
                title: 'Generation Failed',
              })
              setCheckingEmailStatus(false)
              return
            }
            
            toast.removeToast(loadingToastId)
            setPreviewEmail(email)
            setEditedEmailContent(email.content)
            setEditedEmailSubject(email.subject || '')
            setShowEmailPreviewModal(true)
            setEditingEmail(false)
            setCheckingEmailStatus(false)
            fetchCustomerDetail()
          } else if (checkCount < maxChecks) {
            // Check again in 2 seconds
            setTimeout(checkEmailReady, 2000)
          } else {
            // Timeout - stop checking
            toast.removeToast(loadingToastId)
            // Check if there's an error message in notes or content
            if (email.notes && email.notes.includes('Error')) {
              toast.error(email.notes, {
                title: 'Generation Failed',
              })
            } else if (email.content && email.content.includes('Error:')) {
              toast.error(email.content, {
                title: 'Generation Failed',
              })
            } else {
              toast.error('Email generation is taking longer than expected. The email may still be generating in the background. Check the "Last Interactions" section.', {
                title: 'Generation Timeout',
              })
            }
            setCheckingEmailStatus(false)
          }
        } catch (err) {
          console.error('Error checking email status:', err)
          if (checkCount < maxChecks) {
            setTimeout(checkEmailReady, 2000)
          } else {
            toast.removeToast(loadingToastId)
            toast.error('Failed to check email status', {
              title: 'Error',
            })
            setCheckingEmailStatus(false)
          }
        }
      }
      
      // Start checking after 3 seconds
      setTimeout(checkEmailReady, 3000)
    } catch (err) {
      toast.remove()
      toast.error('Failed to prepare email: ' + (err.response?.data?.detail || err.message), {
        title: 'Email Preparation Failed',
      })
      console.error(err)
    } finally {
      setPreparingEmail(false)
    }
  }

  const handleSendEmail = async (emailId) => {
    try {
      await api.post(`/customers/${id}/send-email/${emailId}`)
      toast.success('Email sent successfully', {
        title: 'Email Sent',
      })
      setShowEmailPreviewModal(false)
      setPreviewEmail(null)
      fetchCustomerDetail()
    } catch (err) {
      toast.error('Failed to send email: ' + (err.response?.data?.detail || err.message), {
        title: 'Send Failed',
      })
      console.error(err)
    }
  }

  const handleDeclineEmail = async () => {
    if (!previewEmail) return
    
    try {
      await api.delete(`/customers/${id}/planned-email/${previewEmail.id}`)
      toast.success('Email cancelled', {
        title: 'Email Cancelled',
      })
      setShowEmailPreviewModal(false)
      setPreviewEmail(null)
      fetchCustomerDetail()
    } catch (err) {
      toast.error('Failed to cancel email: ' + (err.response?.data?.detail || err.message), {
        title: 'Cancel Failed',
      })
      console.error(err)
    }
  }

  const handleSaveEditedEmail = async () => {
    if (!previewEmail) return
    
    try {
      setSavingEmail(true)
      await api.put(`/customers/${id}/planned-email/${previewEmail.id}`, {
        subject: editedEmailSubject,
        content: editedEmailContent
      })
      
      toast.success('Email updated successfully', {
        title: 'Email Updated',
      })
      
      // Update preview email with edited content
      setPreviewEmail({
        ...previewEmail,
        subject: editedEmailSubject,
        content: editedEmailContent
      })
      setEditingEmail(false)
      fetchCustomerDetail()
    } catch (err) {
      toast.error('Failed to save email: ' + (err.response?.data?.detail || err.message), {
        title: 'Save Failed',
      })
      console.error(err)
    } finally {
      setSavingEmail(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-gray-600">Loading customer details...</p>
      </div>
    )
  }

  if (error || !customer) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error || 'Customer not found'}
      </div>
    )
  }

  const totalDebt = debts.reduce((sum, debt) => sum + (debt.current_balance || 0), 0)
  const pendingCalls = scheduledCalls.filter((call) => call.status === 'pending')

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customers
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {customer.first_name} {customer.middle_name && `${customer.middle_name} `}
              {customer.last_name}
            </h1>
            <p className="text-gray-600 mt-1">Customer ID: {customer.id}</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={openPrepareConfirmModal}
              disabled={preparing}
              className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {preparing ? 'Preparing...' : 'Create Customer Strategy'}
            </button>
            <button
              onClick={openScheduleModal}
              className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Phone className="h-4 w-4 mr-2" />
              Schedule Automatic Call
            </button>
            <button
              onClick={() => setShowEmailModal(true)}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="h-4 w-4 mr-2" />
              Prepare Email
            </button>
          </div>
        </div>
      </div>

      {/* Customer Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Debt</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                ${totalDebt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Credit Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {customer.credit_score || 'N/A'}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Days Past Due</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {customer?.max_days_past_due || Math.max(...debts.map(d => d.days_past_due || 0), 0)}
              </p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Calls</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">{pendingCalls.length}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Customer Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Customer Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {customer.date_of_birth && (
                <div className="flex items-center text-gray-700">
                  <Calendar className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Date of Birth</p>
                    <p className="font-medium">
                      {format(new Date(customer.date_of_birth), 'MMM d, yyyy')}
                    </p>
                  </div>
                </div>
              )}
              {customer.ssn && (
                <div className="flex items-center text-gray-700">
                  <CreditCard className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">SSN</p>
                    <p className="font-medium">{customer.ssn}</p>
                  </div>
                </div>
              )}
              {customer.phone_primary && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Primary Phone</p>
                    <p className="font-medium">{customer.phone_primary}</p>
                  </div>
                </div>
              )}
              {customer.phone_secondary && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Secondary Phone</p>
                    <p className="font-medium">{customer.phone_secondary}</p>
                  </div>
                </div>
              )}
              {customer.email && (
                <div className="flex items-center text-gray-700">
                  <Mail className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium">{customer.email}</p>
                  </div>
                </div>
              )}
              {customer.address_line1 && (
                <div className="flex items-center text-gray-700">
                  <MapPin className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Address</p>
                    <p className="font-medium">
                      {customer.address_line1}
                      {customer.address_line2 && `, ${customer.address_line2}`}
                      {customer.city && `, ${customer.city}`}
                      {customer.state && ` ${customer.state}`}
                      {customer.zip_code && ` ${customer.zip_code}`}
                      {customer.country && `, ${customer.country}`}
                    </p>
                  </div>
                </div>
              )}
              {customer.employer_name && (
                <div className="flex items-center text-gray-700">
                  <Briefcase className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Employer</p>
                    <p className="font-medium">{customer.employer_name}</p>
                  </div>
                </div>
              )}
              {customer.employment_status && (
                <div className="flex items-center text-gray-700">
                  <User className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Employment Status</p>
                    <p className="font-medium">{customer.employment_status}</p>
                  </div>
                </div>
              )}
              {customer.annual_income && (
                <div className="flex items-center text-gray-700">
                  <DollarSign className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Annual Income</p>
                    <p className="font-medium">
                      ${customer.annual_income.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              )}
              {customer.preferred_communication_method && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Preferred Contact Method</p>
                    <p className="font-medium capitalize">{customer.preferred_communication_method}</p>
                  </div>
                </div>
              )}
              {(customer.preferred_contact_time || customer.preferred_contact_days) && (
                <div className="flex items-center text-gray-700">
                  <Clock className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Preferred Contact Time</p>
                    <p className="font-medium">
                      {customer.preferred_contact_time && customer.preferred_contact_days
                        ? `${customer.preferred_contact_time}, ${customer.preferred_contact_days}`
                        : customer.preferred_contact_time || customer.preferred_contact_days}
                    </p>
                  </div>
                </div>
              )}
            </div>
            {customer.notes && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500 mb-1">Notes</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{customer.notes}</p>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Last Interactions</h2>
              <Link
                to={`/customer/${id}/call-history`}
                className="inline-flex items-center px-3 py-1.5 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-4 w-4 mr-2" />
                View All
              </Link>
            </div>
            {scheduledCalls.length === 0 && plannedEmails.length === 0 ? (
              <p className="text-gray-500 text-sm">No interactions</p>
            ) : (
              <div className="space-y-3">
                {[
                  ...scheduledCalls.map(call => ({ ...call, interactionType: 'call' })),
                  ...plannedEmails.map(email => ({ ...email, interactionType: 'email' }))
                ]
                  .filter(item => item.status !== 'cancelled') // Filter out cancelled interactions
                  .sort((a, b) => {
                    // Sort by scheduled_time/sent_at or created_at, most recent first
                    const dateA = a.scheduled_time ? new Date(a.scheduled_time) 
                      : a.sent_at ? new Date(a.sent_at)
                      : new Date(a.created_at)
                    const dateB = b.scheduled_time ? new Date(b.scheduled_time)
                      : b.sent_at ? new Date(b.sent_at)
                      : new Date(b.created_at)
                    return dateB - dateA
                  })
                  .slice(0, 3)
                  .map((item) => {
                    if (item.interactionType === 'email') {
                      const email = item
                      return (
                        <div
                          key={`email_${email.id}`}
                          className={`border border-gray-200 rounded-lg p-3 ${
                            email.status === 'planned' ? 'bg-purple-50' 
                            : email.status === 'sent' ? 'bg-green-50'
                            : 'bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center space-x-2">
                              <Mail className="h-4 w-4 text-gray-500" />
                              <span className="text-sm font-medium text-gray-900">
                                {email.sent_at
                                  ? format(new Date(email.sent_at), 'MMM d, yyyy h:mm a')
                                  : email.scheduled_send_time
                                  ? format(new Date(email.scheduled_send_time), 'MMM d, yyyy h:mm a')
                                  : email.created_at
                                  ? format(new Date(email.created_at), 'MMM d, yyyy h:mm a')
                                  : 'Not scheduled yet'}
                              </span>
                              <span className="text-xs text-gray-500 uppercase">
                                {email.communication_type}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(
                                  email.status
                                )}`}
                              >
                                {email.status}
                              </span>
                              {email.status === 'planned' && (
                                <button
                                  onClick={() => handleSendEmail(email.id)}
                                  className="text-primary-600 hover:text-primary-800 text-xs font-medium"
                                  title="Send email"
                                >
                                  Send
                                </button>
                              )}
                              {email.status === 'planned' && (
                                <button
                                  onClick={() => handleCancelCallClick(`email_${email.id}`)}
                                  className="text-red-600 hover:text-red-800"
                                  title="Cancel email"
                                >
                                  <X className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </div>
                          {email.subject && (
                            <p className="text-xs font-medium text-gray-700 mt-1">Subject: {email.subject}</p>
                          )}
                          {email.content && (
                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{email.content.substring(0, 100)}...</p>
                          )}
                        </div>
                      )
                    } else {
                      const call = item
                      return (
                        <div
                          key={call.id}
                          className={`border border-gray-200 rounded-lg p-3 ${
                            call.status === 'planned' ? 'bg-purple-50' 
                            : call.status === 'pending' ? 'bg-yellow-50'
                            : call.status === 'completed' ? 'bg-green-50'
                            : 'bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center space-x-2">
                              <Phone className="h-4 w-4 text-gray-500" />
                              <span className="text-sm font-medium text-gray-900">
                                {call.scheduled_time
                                  ? format(new Date(call.scheduled_time), 'MMM d, yyyy h:mm a')
                                  : call.created_at
                                  ? format(new Date(call.created_at), 'MMM d, yyyy h:mm a')
                                  : 'Not scheduled yet'}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(
                                  call.status
                                )}`}
                              >
                                {call.status === 'pending' ? 'automatic' : call.status}
                              </span>
                              {call.status === 'planned' && (
                                <button
                                  onClick={async () => {
                                    // Get planning script for this call
                                    try {
                                      const scriptsResponse = await api.get(`/customers/${id}/call-planning-scripts`, {
                                        params: { scheduled_call_id: call.id }
                                      })
                                      if (scriptsResponse.data.length > 0) {
                                        const script = scriptsResponse.data[0]
                                        setSuggestedTime(script.suggested_time)
                                        setSuggestedDay(script.suggested_day)
                                      }
                                      setSchedulingPlannedCallId(call.id)
                                      setShowScheduleModal(true)
                                      setScheduleNotes(`Scheduling planned call ${call.id}`)
                                    } catch (err) {
                                      setSchedulingPlannedCallId(call.id)
                                      setShowScheduleModal(true)
                                    }
                                  }}
                                  className="text-primary-600 hover:text-primary-800 text-xs font-medium"
                                  title="Schedule this call"
                                >
                                  Schedule
                                </button>
                              )}
                              {(call.status === 'pending' || call.status === 'planned') && (
                                <button
                                  onClick={() => handleCancelCallClick(call.id)}
                                  className="text-red-600 hover:text-red-800"
                                  title="Cancel call"
                                >
                                  <X className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </div>
                          {call.planning_script || call.planning_file_path ? (
                            <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-medium text-gray-700">Planning Script</span>
                                {call.planning_script && (
                                  <button
                                    onClick={() => {
                                      setSelectedScript(call.planning_script)
                                      setShowScriptModal(true)
                                    }}
                                    className="text-xs text-primary-600 hover:text-primary-700"
                                  >
                                    View
                                  </button>
                                )}
                              </div>
                              {call.planning_script?.suggested_time && (
                                <p className="text-xs text-gray-500">
                                  Suggested: {call.planning_script.suggested_time}
                                  {call.planning_script.suggested_day && ` on ${call.planning_script.suggested_day}`}
                                </p>
                              )}
                            </div>
                          ) : call.status === 'planned' && (
                            <div className="mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
                              <div className="flex items-center space-x-2">
                                <Clock className="h-3 w-3 text-yellow-600 animate-spin" />
                                <span className="text-xs text-yellow-700">Generating planning script...</span>
                              </div>
                            </div>
                          )}
                          {call.notes && (
                            <p className="text-xs text-gray-600 mt-1">{call.notes}</p>
                          )}
                        </div>
                      )
                    }
                  })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Debts Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Debts</h2>
        {debts.length === 0 ? (
          <p className="text-gray-500">No debts found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Original Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Past Due
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Due Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {debts.map((debt) => (
                  <tr key={debt.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {debt.debt_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      ${debt.original_amount?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-red-600">
                      ${debt.current_balance?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          debt.status === 'active'
                            ? 'bg-red-100 text-red-800'
                            : debt.status === 'paid_off'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {debt.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {debt.days_past_due || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {debt.due_date
                        ? format(new Date(debt.due_date), 'MMM d, yyyy')
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Prepare Call Modal */}
      {showPrepareModal && prepareResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Call Preparation Script</h3>
              <button
                onClick={() => {
                  setShowPrepareModal(false)
                  setPrepareResult(null)
                  setPrepareScriptExpanded(false)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="space-y-4">
              {prepareResult.suggested_time && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-900">
                    Suggested Contact Time: {prepareResult.suggested_time}
                    {prepareResult.suggested_day && ` on ${prepareResult.suggested_day}`}
                  </p>
                </div>
              )}
              <div>
                <button
                  onClick={() => setPrepareScriptExpanded(!prepareScriptExpanded)}
                  className="w-full flex items-center text-left mb-2"
                >
                  {prepareScriptExpanded ? (
                    <ChevronDown className="h-4 w-4 text-gray-400 mr-2" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-gray-400 mr-2" />
                  )}
                  <span className="text-sm font-medium text-gray-700">Call Preparation Script</span>
                </button>
                {prepareScriptExpanded && (
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="prose max-w-none">
                      <ReactMarkdown>{prepareResult.strategy}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowPrepareModal(false)
                  setPrepareResult(null)
                  setPrepareScriptExpanded(false)
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Modal */}
      {showEmailModal && customer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Customize Email</h3>
              <button
                onClick={() => setShowEmailModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Communication Type
                </label>
                <div className="flex space-x-4">
                  <button
                    onClick={() => setEmailType('email')}
                    className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                      emailType === 'email'
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Mail className="h-4 w-4 mx-auto mb-1" />
                    Email
                  </button>
                  <button
                    onClick={() => setEmailType('sms')}
                    className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                      emailType === 'sms'
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Phone className="h-4 w-4 mx-auto mb-1" />
                    SMS
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                This will generate a personalized {emailType === 'email' ? 'email' : 'SMS'} using AI strategy planning.
              </p>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowEmailModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePrepareEmail}
                disabled={preparingEmail}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {preparingEmail ? 'Preparing...' : `Create ${emailType === 'email' ? 'Email' : 'SMS'}`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Prepare Call Confirmation Modal */}
      {showPrepareConfirmModal && customer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Create Call Strategy</h3>
              <button
                onClick={() => setShowPrepareConfirmModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-gray-700">
                Do you want to create a call strategy for{' '}
                <span className="font-semibold text-gray-900">
                  {customer.first_name} {customer.last_name}
                </span>?
              </p>
              <p className="text-sm text-gray-500">
                This will generate a personalized planning script that you can use to prepare for the call. 
                The script will be generated in the background and will be available shortly.
              </p>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowPrepareConfirmModal(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePrepareCall}
                disabled={preparing}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center"
              >
                {preparing ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Create Strategy
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Call Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {schedulingPlannedCallId ? 'Schedule Planned Call' : 'Schedule Automatic Call'}
            </h3>
            {suggestedTime && (
              <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-900">
                  <strong>Suggested from planning:</strong> {suggestedTime}
                  {suggestedDay && ` on ${suggestedDay}`}
                </p>
              </div>
            )}
            <div className="space-y-4">
              {/* Suggested Time Slots */}
              {!schedulingPlannedCallId && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Suggested Time Slots (10-minute windows)
                  </label>
                  {loadingTimeSlots ? (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
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
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-900">{slot.display}</p>
                              <p className="text-xs text-gray-500 mt-1">10-minute window</p>
                            </div>
                            {selectedTimeSlot?.start_time === slot.start_time && (
                              <CheckCircle className="h-5 w-5 text-primary-600" />
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No time slots available</p>
                  )}
                </div>
              )}
              
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
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
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="useAutoTime" className="ml-2 block text-sm text-gray-700">
                  {schedulingPlannedCallId 
                    ? 'Use time from planning file'
                    : 'Let AI choose the best time automatically'}
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {scheduling ? 'Scheduling...' : 'Schedule Call'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Script Modal */}
      {showScriptModal && selectedScript && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Call Planning Script</h3>
              <button
                onClick={() => {
                  setShowScriptModal(false)
                  setSelectedScript(null)
                  setViewScriptExpanded(false)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="space-y-4">
              {selectedScript.suggested_time && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-900">
                    Suggested Contact Time: {selectedScript.suggested_time}
                    {selectedScript.suggested_day && ` on ${selectedScript.suggested_day}`}
                  </p>
                </div>
              )}
              <div>
                <button
                  onClick={() => setViewScriptExpanded(!viewScriptExpanded)}
                  className="w-full flex items-center text-left mb-2"
                >
                  {viewScriptExpanded ? (
                    <ChevronDown className="h-4 w-4 text-gray-400 mr-2" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-gray-400 mr-2" />
                  )}
                  <span className="text-sm font-medium text-gray-700">Strategy Content</span>
                </button>
                {viewScriptExpanded && (
                  <div className="prose max-w-none bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <ReactMarkdown>{selectedScript.strategy_content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowScriptModal(false)
                  setSelectedScript(null)
                  setViewScriptExpanded(false)
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Close
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

      {/* Email Preview Modal */}
      {showEmailPreviewModal && previewEmail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">
                {previewEmail.communication_type === 'email' ? 'Email' : 'SMS'} Preview
              </h3>
              <button
                onClick={() => {
                  setShowEmailPreviewModal(false)
                  setPreviewEmail(null)
                  setEditingEmail(false)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              {previewEmail.communication_type === 'email' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject
                  </label>
                  {editingEmail ? (
                    <input
                      type="text"
                      value={editedEmailSubject}
                      onChange={(e) => setEditedEmailSubject(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Email subject"
                    />
                  ) : (
                    <p className="text-sm font-medium text-gray-900 bg-gray-50 p-3 rounded-lg">
                      {previewEmail.subject || 'No subject'}
                    </p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {previewEmail.communication_type === 'email' ? 'Email' : 'SMS'} Content
                </label>
                {editingEmail ? (
                  <textarea
                    value={editedEmailContent}
                    onChange={(e) => setEditedEmailContent(e.target.value)}
                    rows={15}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                    placeholder="Email content"
                  />
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="prose max-w-none whitespace-pre-wrap text-sm">
                      {previewEmail.content}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
              {editingEmail ? (
                <>
                  <button
                    onClick={() => {
                      setEditingEmail(false)
                      setEditedEmailContent(previewEmail.content)
                      setEditedEmailSubject(previewEmail.subject || '')
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEditedEmail}
                    disabled={savingEmail}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                  >
                    {savingEmail ? (
                      <>
                        <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4" />
                        <span>Save</span>
                      </>
                    )}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleDeclineEmail}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
                  >
                    <X className="h-4 w-4" />
                    <span>Decline</span>
                  </button>
                  <button
                    onClick={() => {
                      setEditingEmail(true)
                      setEditedEmailContent(previewEmail.content)
                      setEditedEmailSubject(previewEmail.subject || '')
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2"
                  >
                    <Edit className="h-4 w-4" />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => handleSendEmail(previewEmail.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                  >
                    <Check className="h-4 w-4" />
                    <span>Confirm & Send</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomerDetail
