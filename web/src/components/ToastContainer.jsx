import { useState, useCallback } from 'react'
import Toast from './Toast'

let toastIdCounter = 0

export const useToast = () => {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toast) => {
    const id = ++toastIdCounter
    const newToast = {
      id,
      type: 'info',
      message: '',
      title: null,
      duration: 5000,
      autoClose: true,
      dismissible: true,
      ...toast,
    }
    setToasts((prev) => [...prev, newToast])
    return id
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const success = useCallback((message, options = {}) => {
    return addToast({ ...options, type: 'success', message })
  }, [addToast])

  const error = useCallback((message, options = {}) => {
    return addToast({ ...options, type: 'error', message })
  }, [addToast])

  const info = useCallback((message, options = {}) => {
    return addToast({ ...options, type: 'info', message })
  }, [addToast])

  const loading = useCallback((message, options = {}) => {
    return addToast({ ...options, type: 'loading', message, autoClose: false, dismissible: false })
  }, [addToast])

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    loading,
  }
}

const ToastContainer = ({ toasts, onClose }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col items-end">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  )
}

export default ToastContainer
