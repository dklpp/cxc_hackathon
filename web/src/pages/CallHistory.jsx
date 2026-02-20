import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import { useToastContext } from '../App'
import ConfirmModal from '../components/ConfirmModal'
import ScheduleCallModal from '../components/ScheduleCallModal'
import CallCard from '../components/CallCard'
import CallDetailsModal from '../components/CallDetailsModal'
import { ArrowLeft } from 'lucide-react'

function CallHistory() {
  const { id } = useParams()
  const toast = useToastContext()
  const [plannedCalls, setPlannedCalls] = useState([])
  const [automaticCalls, setAutomaticCalls] = useState([])
  const [completedCalls, setCompletedCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCall, setSelectedCall] = useState(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showCancelCallModal, setShowCancelCallModal] = useState(false)
  const [callToCancel, setCallToCancel] = useState(null)
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
  const isPollingRef = useRef(false)

  const fetchCallHistory = async () => {
    if (!id) {
      setError('Customer ID is required')
      setLoading(false)
      return
    }
    try {
      const isInitialLoad =
        loading && plannedCalls.length === 0 && automaticCalls.length === 0 && completedCalls.length === 0
      if (isInitialLoad) setLoading(true)
      setError(null)

      const response = await api.get(`/customers/${id}/call-history`)
      const planned = Array.isArray(response.data?.planned) ? response.data.planned : []
      const automatic = Array.isArray(response.data?.automatic) ? response.data.automatic : []
      const completed = Array.isArray(response.data?.completed) ? response.data.completed : []

      const setIfChanged = (setter, next) =>
        setter((prev) => (JSON.stringify(prev) === JSON.stringify(next) ? prev : next))
      setIfChanged(setPlannedCalls, planned)
      setIfChanged(setAutomaticCalls, automatic)
      setIfChanged(setCompletedCalls, completed)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load call history')
      setPlannedCalls([])
      setAutomaticCalls([])
      setCompletedCalls([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) fetchCallHistory()
  }, [id])

  useEffect(() => {
    if (loading || !plannedCalls.length || isPollingRef.current) return
    const interval = setInterval(() => {
      const hasPending = plannedCalls.some((c) => !c.planning_script)
      if (hasPending && !loading && !isPollingRef.current) {
        isPollingRef.current = true
        fetchCallHistory().finally(() => { isPollingRef.current = false })
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [id, plannedCalls, loading])

  const openScheduleModal = async (callId) => {
    setSchedulingPlannedCallId(callId)
    setShowScheduleModal(true)
    setLoadingTimeSlots(true)
    setSelectedTimeSlot(null)
    try {
      const response = await api.get(`/customers/${id}/suggested-time-slots`)
      setTimeSlots(response.data.time_slots || [])
      try {
        const scriptsResponse = await api.get(`/customers/${id}/call-planning-scripts`, {
          params: { scheduled_call_id: callId },
        })
        if (scriptsResponse.data.length > 0) {
          setSuggestedTime(scriptsResponse.data[0].suggested_time)
          setSuggestedDay(scriptsResponse.data[0].suggested_day)
        }
      } catch {}
    } catch (err) {
      toast.error('Failed to load time slots: ' + (err.response?.data?.detail || err.message), {
        title: 'Error',
      })
    } finally {
      setLoadingTimeSlots(false)
    }
  }

  const closeScheduleModal = () => {
    setShowScheduleModal(false)
    setScheduleDateTime('')
    setScheduleNotes('')
    setUseAutoTime(false)
    setSchedulingPlannedCallId(null)
    setSuggestedTime(null)
    setSuggestedDay(null)
    setSelectedTimeSlot(null)
    setTimeSlots([])
  }

  const handleScheduleCall = async () => {
    let finalDateTime = null
    if (selectedTimeSlot) {
      finalDateTime = selectedTimeSlot.start_time
    } else if (scheduleDateTime) {
      finalDateTime = scheduleDateTime
    } else if (useAutoTime) {
      // handled by backend
    } else {
      toast.info(
        'Please select a time slot, enter a date/time manually, or choose automatic time selection',
        { title: 'Time Selection Required' },
      )
      return
    }

    try {
      setScheduling(true)
      let scheduledTimeForAPI = null
      if (finalDateTime) {
        if (finalDateTime.includes('T') && finalDateTime.includes('Z')) {
          scheduledTimeForAPI = finalDateTime
        } else if (finalDateTime.includes('T')) {
          scheduledTimeForAPI = finalDateTime + 'Z'
        } else {
          scheduledTimeForAPI = new Date(finalDateTime).toISOString()
        }
      }
      await api.post(`/scheduled-calls/${schedulingPlannedCallId}/schedule`, {
        scheduled_time: scheduledTimeForAPI || null,
        use_auto_time: useAutoTime && !finalDateTime,
      })
      toast.success('Call scheduled successfully!', {
        title: 'Call Scheduled',
        message: 'Strategy planning has started in the background.',
        duration: 6000,
      })
      closeScheduleModal()
      fetchCallHistory()
    } catch (err) {
      toast.error('Failed to schedule call: ' + (err.response?.data?.detail || err.message), {
        title: 'Scheduling Failed',
      })
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
      const callIdStr = String(callToCancel)
      if (callIdStr.startsWith('email_')) {
        await api.delete(`/customers/${id}/planned-email/${callIdStr.replace('email_', '')}`)
        toast.success('Email cancelled successfully', { title: 'Email Cancelled' })
      } else if (callIdStr.startsWith('scheduled_')) {
        await api.delete(`/scheduled-calls/${callIdStr.replace('scheduled_', '')}`)
        toast.success('Call removed successfully', { title: 'Call Removed' })
      } else {
        // Direct communication log (orphaned completed call)
        await api.delete(`/communication-logs/${callIdStr}`)
        toast.success('Call removed from history', { title: 'Removed' })
      }
      setShowCancelCallModal(false)
      setCallToCancel(null)
      fetchCallHistory()
    } catch (err) {
      toast.error('Failed to remove: ' + (err.response?.data?.detail || err.message), {
        title: 'Remove Failed',
      })
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

  if (!id) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Invalid customer ID
        </div>
        <Link to="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customers
        </Link>
      </div>
    )
  }

  const columns = [
    {
      label: 'Planned Interactions',
      count: plannedCalls.length,
      calls: plannedCalls,
      headerClass: 'bg-purple-50 border-purple-200',
      textClass: 'text-purple-900',
      subTextClass: 'text-purple-700',
    },
    {
      label: 'Scheduled Automatic Calls',
      count: automaticCalls.length,
      calls: automaticCalls,
      headerClass: 'bg-yellow-50 border-yellow-200',
      textClass: 'text-yellow-900',
      subTextClass: 'text-yellow-700',
    },
    {
      label: 'Completed Interactions',
      count: completedCalls.length,
      calls: completedCalls,
      headerClass: 'bg-green-50 border-green-200',
      textClass: 'text-green-900',
      subTextClass: 'text-green-700',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <Link
          to={`/customer/${id}`}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customer Details
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Interaction History</h1>
        <p className="text-gray-600 mt-1">
          Manage planned, scheduled, and completed interactions (calls, emails, SMS)
        </p>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500" />
          <p className="mt-2 text-gray-600">Loading interaction history...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {columns.map(({ label, count, calls, headerClass, textClass, subTextClass }) => (
            <div key={label}>
              <div className={`border rounded-t-lg p-4 ${headerClass}`}>
                <h2 className={`text-lg font-semibold ${textClass}`}>{label}</h2>
                <p className={`text-sm ${subTextClass}`}>{count} items</p>
              </div>
              <div className="bg-gray-50 border-x border-b border-gray-200 rounded-b-lg p-4 space-y-3 h-[calc(100vh-18rem)] overflow-y-auto">
                {calls.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-8">No {label.toLowerCase()}</p>
                ) : (
                  calls.map((call) => (
                    <CallCard
                      key={call.id}
                      call={call}
                      onViewDetails={(c) => { setSelectedCall(c); setShowDetailsModal(true) }}
                      onCancel={handleCancelCallClick}
                      onSchedule={openScheduleModal}
                      getStatusBadge={getStatusBadge}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <CallDetailsModal
        call={selectedCall}
        isOpen={showDetailsModal}
        onClose={() => { setShowDetailsModal(false); setSelectedCall(null) }}
        onRefresh={fetchCallHistory}
        customerId={id}
      />

      <ScheduleCallModal
        isOpen={showScheduleModal}
        onClose={closeScheduleModal}
        onSchedule={handleScheduleCall}
        suggestedTime={suggestedTime}
        suggestedDay={suggestedDay}
        timeSlots={timeSlots}
        loadingTimeSlots={loadingTimeSlots}
        selectedTimeSlot={selectedTimeSlot}
        onSelectTimeSlot={(slot) => { setSelectedTimeSlot(slot); setScheduleDateTime(''); setUseAutoTime(false) }}
        scheduleDateTime={scheduleDateTime}
        onScheduleDateTimeChange={(val) => { setScheduleDateTime(val); setSelectedTimeSlot(null); setUseAutoTime(false) }}
        scheduleNotes={scheduleNotes}
        onScheduleNotesChange={setScheduleNotes}
        useAutoTime={useAutoTime}
        onUseAutoTimeChange={(val) => { setUseAutoTime(val); if (val) { setScheduleDateTime(''); setSelectedTimeSlot(null) } }}
        scheduling={scheduling}
        title="Schedule Planned Call"
        autoTimeLabel="Use time from planning file"
      />

      <ConfirmModal
        isOpen={showCancelCallModal}
        onClose={() => { setShowCancelCallModal(false); setCallToCancel(null) }}
        onConfirm={handleCancelCall}
        title="Remove Interaction"
        message="Are you sure you want to remove this interaction? This action cannot be undone."
        confirmText="Remove"
        cancelText="Keep"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        isLoading={false}
      />
    </div>
  )
}

export default CallHistory
