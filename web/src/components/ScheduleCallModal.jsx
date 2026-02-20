import { CheckCircle } from 'lucide-react'

export default function ScheduleCallModal({
  isOpen,
  onClose,
  onSchedule,
  suggestedTime,
  suggestedDay,
  timeSlots = [],
  loadingTimeSlots = false,
  selectedTimeSlot,
  onSelectTimeSlot,
  scheduleDateTime,
  onScheduleDateTimeChange,
  scheduleNotes,
  onScheduleNotesChange,
  useAutoTime,
  onUseAutoTimeChange,
  scheduling = false,
  title = 'Schedule Call',
  showTimeSlots = true,
  autoTimeLabel = 'Let AI choose the best time automatically',
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">{title}</h3>

        {suggestedTime && (
          <div className="mb-4 bg-tangerine-50 border border-tangerine-200 rounded-lg p-3">
            <p className="text-sm text-tangerine-900">
              <strong>Suggested from planning:</strong> {suggestedTime}
              {suggestedDay && ` on ${suggestedDay}`}
            </p>
          </div>
        )}

        <div className="space-y-4">
          {showTimeSlots && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Suggested Time Slots (10-minute windows)
              </label>
              {loadingTimeSlots ? (
                <div className="text-center py-4">
                  <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-tangerine-500" />
                  <p className="text-xs text-gray-500 mt-2">Loading time slots...</p>
                </div>
              ) : timeSlots.length > 0 ? (
                <div className="space-y-2">
                  {timeSlots.map((slot, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => onSelectTimeSlot(slot)}
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
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Or Enter Date & Time Manually
            </label>
            <input
              type="datetime-local"
              value={scheduleDateTime}
              onChange={(e) => onScheduleDateTimeChange(e.target.value)}
              disabled={useAutoTime}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="useAutoTime"
              checked={useAutoTime}
              onChange={(e) => onUseAutoTimeChange(e.target.checked)}
              className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500 border-gray-300 rounded"
            />
            <label htmlFor="useAutoTime" className="ml-2 block text-sm text-gray-700">
              {autoTimeLabel}
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={scheduleNotes}
              onChange={(e) => onScheduleNotesChange(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
              placeholder="Add any notes about this call..."
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onSchedule}
            disabled={scheduling}
            className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 disabled:opacity-50"
          >
            {scheduling ? 'Scheduling...' : 'Schedule Call'}
          </button>
        </div>
      </div>
    </div>
  )
}
