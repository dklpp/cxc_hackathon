import { Link } from 'react-router-dom'
import { Info } from 'lucide-react'

export function formatScriptKey(key) {
  return key.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

export function renderScriptValue(value, key) {
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
    return (
      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${colors[v] || 'bg-gray-100 text-gray-700 border border-gray-200'}`}>
        {value}
      </span>
    )
  }

  if (key === 'communication_channel') {
    return (
      <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize bg-tangerine-100 text-tangerine-800 border border-tangerine-200">
        {value}
      </span>
    )
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
    return (
      <span className="font-semibold text-gray-900">
        ${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
    )

  if (typeof value === 'boolean')
    return value ? (
      <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-tangerine-100 text-tangerine-800 border border-tangerine-200">Yes</span>
    ) : (
      <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">No</span>
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
    return (
      <pre className="text-xs whitespace-pre-wrap break-words bg-gray-50 p-2 rounded">
        {JSON.stringify(value, null, 2)}
      </pre>
    )

  return <span className="whitespace-pre-wrap">{String(value)}</span>
}

function parseContent(content) {
  try {
    let raw = typeof content === 'string' ? content : JSON.stringify(content)
    raw = raw.replace(/^```[\w]*\n?/, '').replace(/\n?```$/, '').trim()
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function getCleanRaw(content) {
  return (typeof content === 'string' ? content : JSON.stringify(content, null, 2))
    .replace(/^```[\w]*\n?/, '')
    .replace(/\n?```$/, '')
    .trim()
}

export default function ScriptTable({ content, showRawJson, onToggleRawJson }) {
  const parsed = parseContent(content)

  if (!parsed || showRawJson) {
    return (
      <div>
        <pre className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-xs overflow-auto whitespace-pre-wrap break-words">
          {getCleanRaw(content)}
        </pre>
        {parsed && (
          <button
            onClick={() => onToggleRawJson(false)}
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
      <div className="border border-tangerine-100 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-tangerine-100">
          <tbody className="divide-y divide-tangerine-50">
            {Object.entries(parsed).map(([key, value], idx) => (
              <tr
                key={key}
                className={idx % 2 === 0 ? 'bg-white hover:bg-tangerine-50/30' : 'bg-tangerine-50/20 hover:bg-tangerine-50/50'}
              >
                <td className="px-4 py-3 text-sm font-medium text-tangerine-700 w-2/5 align-top whitespace-nowrap">
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
        onClick={() => onToggleRawJson(true)}
        className="mt-3 text-xs text-gray-400 hover:text-gray-600 underline"
      >
        View Raw JSON
      </button>
    </div>
  )
}
