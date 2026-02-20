import { X, Mail, Phone } from 'lucide-react'

export default function EmailModal({ isOpen, onClose, emailType, onEmailTypeChange, onSubmit, preparing }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Customize Email</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
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
                onClick={() => onEmailTypeChange('email')}
                className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                  emailType === 'email'
                    ? 'border-tangerine-500 bg-tangerine-50 text-tangerine-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Mail className="h-4 w-4 mx-auto mb-1" />
                Email
              </button>
              <button
                onClick={() => onEmailTypeChange('sms')}
                className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                  emailType === 'sms'
                    ? 'border-tangerine-500 bg-tangerine-50 text-tangerine-700'
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
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={preparing}
            className="px-4 py-2 bg-tangerine-500 text-white rounded-full hover:bg-tangerine-600 transition-colors disabled:opacity-50"
          >
            {preparing ? 'Preparing...' : `Create ${emailType === 'email' ? 'Email' : 'SMS'}`}
          </button>
        </div>
      </div>
    </div>
  )
}
