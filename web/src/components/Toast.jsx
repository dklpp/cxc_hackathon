import { useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info, Loader } from 'lucide-react'

const Toast = ({ toast, onClose }) => {
  useEffect(() => {
    if (toast.autoClose) {
      const timer = setTimeout(() => {
        onClose(toast.id)
      }, toast.duration || 5000)
      return () => clearTimeout(timer)
    }
  }, [toast, onClose])

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-500" />,
    error: <AlertCircle className="h-5 w-5 text-red-500" />,
    info: <Info className="h-5 w-5 text-tangerine-500" />,
    loading: <Loader className="h-5 w-5 text-tangerine-500 animate-spin" />,
  }

  const bgColors = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-tangerine-50 border-tangerine-200',
    loading: 'bg-tangerine-50 border-tangerine-200',
  }

  const textColors = {
    success: 'text-green-800',
    error: 'text-red-800',
    info: 'text-tangerine-800',
    loading: 'text-tangerine-800',
  }

  return (
    <div
      className={`${bgColors[toast.type]} ${textColors[toast.type]} border rounded-xl shadow-lg p-4 mb-3 flex items-start gap-3 min-w-[300px] max-w-[500px] animate-slide-in`}
    >
      <div className="flex-shrink-0 mt-0.5">
        {icons[toast.type]}
      </div>
      <div className="flex-1">
        {toast.title && (
          <h4 className="font-semibold text-sm mb-1">{toast.title}</h4>
        )}
        <p className="text-sm">{toast.message}</p>
      </div>
      {toast.dismissible !== false && (
        <button
          onClick={() => onClose(toast.id)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

export default Toast
