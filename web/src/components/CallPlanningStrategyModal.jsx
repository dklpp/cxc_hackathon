import { useState } from 'react'
import { X } from 'lucide-react'
import ScriptTable from './ScriptTable'

export default function CallPlanningStrategyModal({ script, onClose }) {
  const [showRawJson, setShowRawJson] = useState(false)

  if (!script) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Call Planning Strategy</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          {script.suggested_time && (
            <div className="bg-tangerine-50 border border-tangerine-200 rounded-lg p-4">
              <p className="text-sm font-medium text-tangerine-900">
                Suggested Contact Time: {script.suggested_time}
                {script.suggested_day && ` on ${script.suggested_day}`}
              </p>
            </div>
          )}
          <ScriptTable
            content={script.strategy_content}
            showRawJson={showRawJson}
            onToggleRawJson={setShowRawJson}
          />
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
