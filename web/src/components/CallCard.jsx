import { Phone, Mail, Clock, X, ChevronRight, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'

function getOutcomeIcon(outcome) {
  if (!outcome) return null
  if (outcome.includes('payment') || outcome.includes('promised'))
    return <CheckCircle className="h-4 w-4 text-green-500" />
  if (outcome.includes('refused') || outcome.includes('no_answer'))
    return <XCircle className="h-4 w-4 text-red-500" />
  return <AlertCircle className="h-4 w-4 text-yellow-500" />
}

export default function CallCard({ call, onViewDetails, onCancel, onSchedule, getStatusBadge }) {
  if (!call || call.id === undefined || call.id === null) return null

  const idStr = String(call.id || '')
  const isEmail =
    call.communication_type === 'email' ||
    call.communication_type === 'sms' ||
    idStr.startsWith('email_')
  const Icon = isEmail ? Mail : Phone
  const canCancel = call.status === 'pending' || call.status === 'planned'
  const canRemove = call.status === 'done' || call.status === 'completed'

  const getCallId = () => {
    if (idStr.startsWith('scheduled_')) return idStr
    if (idStr.startsWith('email_')) return idStr
    if (call.scheduled_call_id) return `scheduled_${call.scheduled_call_id}`
    return idStr
  }

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
          {call.status === 'planned' &&
            (isEmail
              ? !call.content || call.content === 'Generating email content...'
              : !call.planning_script && !call.planning_file_path) && (
              <div className="mt-1 flex items-center space-x-1">
                <Clock className="h-3 w-3 text-yellow-600 animate-spin" />
                <span className="text-xs text-yellow-600">
                  {isEmail ? 'Generating email content...' : 'Generating planning script...'}
                </span>
              </div>
            )}
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(call.status)}`}>
            {call.status === 'pending' ? 'automatic' : call.status}
          </span>
          {call.status === 'planned' && !isEmail && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                const actualCallId = idStr.startsWith('scheduled_')
                  ? idStr.replace('scheduled_', '')
                  : call.scheduled_call_id || idStr
                onSchedule(parseInt(actualCallId))
              }}
              className="px-2 py-1 text-xs font-medium text-tangerine-500 hover:text-tangerine-600 hover:bg-tangerine-50 rounded transition-colors"
              title="Schedule this call"
            >
              Schedule
            </button>
          )}
          {(canCancel || canRemove) && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCancel(getCallId())
              }}
              className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
              title={canRemove ? 'Remove from history' : `Cancel ${isEmail ? 'email' : 'call'}`}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <button
        onClick={() => onViewDetails(call)}
        className="w-full mt-2 flex items-center justify-center space-x-1 text-sm text-tangerine-500 hover:text-tangerine-600 font-medium"
      >
        <span>View Details</span>
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}
