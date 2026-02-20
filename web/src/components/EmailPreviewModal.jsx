import { X, Edit, Check } from 'lucide-react'

export default function EmailPreviewModal({
  email,
  editing,
  editedContent,
  editedSubject,
  saving,
  onClose,
  onDecline,
  onSend,
  onStartEdit,
  onCancelEdit,
  onSave,
  onContentChange,
  onSubjectChange,
}) {
  if (!email) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">
            {email.communication_type === 'email' ? 'Email' : 'SMS'} Preview
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          {email.communication_type === 'email' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
              {editing ? (
                <input
                  type="text"
                  value={editedSubject}
                  onChange={(e) => onSubjectChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
                  placeholder="Email subject"
                />
              ) : (
                <p className="text-sm font-medium text-gray-900 bg-gray-50 p-3 rounded-lg">
                  {email.subject || 'No subject'}
                </p>
              )}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {email.communication_type === 'email' ? 'Email' : 'SMS'} Content
            </label>
            {editing ? (
              <textarea
                value={editedContent}
                onChange={(e) => onContentChange(e.target.value)}
                rows={15}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent font-mono text-sm"
                placeholder="Email content"
              />
            ) : (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="prose max-w-none whitespace-pre-wrap text-sm">{email.content}</div>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
          {editing ? (
            <>
              <button
                onClick={onCancelEdit}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={onSave}
                disabled={saving}
                className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
              >
                {saving ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
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
                onClick={onDecline}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <X className="h-4 w-4" />
                <span>Decline</span>
              </button>
              <button
                onClick={onStartEdit}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2"
              >
                <Edit className="h-4 w-4" />
                <span>Edit</span>
              </button>
              <button
                onClick={() => onSend(email.id)}
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
  )
}
