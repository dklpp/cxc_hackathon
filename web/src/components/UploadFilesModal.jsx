import { useState } from 'react'
import { X } from 'lucide-react'

export default function UploadFilesModal({ isOpen, onClose, onUpload, uploading }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileType, setFileType] = useState('transcript')

  if (!isOpen) return null

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile, fileType)
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    setFileType('transcript')
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Upload File</h3>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select File</label>
            <input
              type="file"
              accept=".txt,.json,.md"
              onChange={(e) => setSelectedFile(e.target.files[0] || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">Selected: {selectedFile.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">File Type</label>
            <div className="space-y-2">
              {[
                { value: 'transcript', label: 'Transcript' },
                { value: 'planning_notes', label: 'Planning Notes' },
                { value: 'other', label: 'Other Info' },
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center">
                  <input
                    type="radio"
                    name="fileType"
                    value={value}
                    checked={fileType === value}
                    onChange={(e) => setFileType(e.target.value)}
                    className="h-4 w-4 text-tangerine-500 focus:ring-tangerine-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={handleClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedFile || uploading}
            className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  )
}
