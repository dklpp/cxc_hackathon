import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X, ChevronDown, ChevronRight, Trash2, Edit, Check, Send, Upload } from 'lucide-react'
import { format } from 'date-fns'
import ScriptTable from './ScriptTable'
import UploadFilesModal from './UploadFilesModal'
import ConfirmModal from './ConfirmModal'
import api from '../api/client'
import { useToastContext } from '../App'

export default function CallDetailsModal({ call, isOpen, onClose, onRefresh, customerId }) {
  const toast = useToastContext()
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [planningContent, setPlanningContent] = useState(null)
  const [transcriptContent, setTranscriptContent] = useState(null)
  const [transcriptExpanded, setTranscriptExpanded] = useState(false)
  const [showRawJson, setShowRawJson] = useState(false)
  const [editingEmail, setEditingEmail] = useState(false)
  const [editedEmailContent, setEditedEmailContent] = useState('')
  const [editedEmailSubject, setEditedEmailSubject] = useState('')
  const [savingEmail, setSavingEmail] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showDeleteFileModal, setShowDeleteFileModal] = useState(false)
  const [fileToDelete, setFileToDelete] = useState(null)
  const [aiSummary, setAiSummary] = useState(null)
  const [loadingSummary, setLoadingSummary] = useState(false)

  useEffect(() => {
    if (call && isOpen) loadDetails(call)
  }, [call, isOpen])

  const loadDetails = async (selectedCall) => {
    setLoadingDetails(true)
    setPlanningContent(null)
    setTranscriptContent(null)
    setTranscriptExpanded(false)
    setShowRawJson(false)
    setEditingEmail(false)
    setEditedEmailContent('')
    setEditedEmailSubject('')
    setAiSummary(null)

    let resolvedPlanning = null
    let resolvedTranscript = null

    try {
      if (selectedCall.planning_file_path || selectedCall.planning_script) {
        if (selectedCall.planning_script?.strategy_content) {
          resolvedPlanning = selectedCall.planning_script.strategy_content
          setPlanningContent(resolvedPlanning)
        } else if (selectedCall.planning_file_path) {
          const planningId = String(selectedCall.id).startsWith('scheduled_')
            ? String(selectedCall.id).replace('scheduled_', '')
            : selectedCall.scheduled_call_id || selectedCall.id
          const response = await api.get(`/call-history/scheduled_${planningId}/planning-file`)
          resolvedPlanning = response.data.content
          setPlanningContent(resolvedPlanning)
        }
      }
      if (selectedCall.transcript) {
        resolvedTranscript = selectedCall.transcript
        setTranscriptContent(resolvedTranscript)
        setTranscriptExpanded(true)
      }
    } catch (err) {
      console.error('Error loading call details:', err)
    } finally {
      setLoadingDetails(false)
    }

    // Pick the best context for summary generation
    const isEmail = selectedCall.communication_type === 'email' || selectedCall.communication_type === 'sms'
    const PLACEHOLDERS = ['generating content', 'planned call -', 'planning script generated', 'ai call notes unavailable', 'generation failed']
    const isPlaceholder = (s) => !s || PLACEHOLDERS.some(p => s.toLowerCase().includes(p))

    let context = null
    let contextType = 'notes'

    if (resolvedTranscript) {
      context = resolvedTranscript
      contextType = 'transcript'
    } else if (isEmail && selectedCall.content && !isPlaceholder(selectedCall.content)) {
      context = (selectedCall.subject ? `Subject: ${selectedCall.subject}\n\n` : '') + selectedCall.content
      contextType = 'email'
    } else if (resolvedPlanning) {
      context = resolvedPlanning
      contextType = 'planning'
    } else if (!isPlaceholder(selectedCall.notes)) {
      context = selectedCall.notes
      contextType = 'notes'
    }

    if (context) {
      setLoadingSummary(true)
      try {
        const res = await api.post('/ai-summary', { context, context_type: contextType })
        setAiSummary(res.data.summary)
      } catch {
        // No summary available
      } finally {
        setLoadingSummary(false)
      }
    }
  }

  const handleSendEmail = async (emailId) => {
    try {
      await api.post(`/customers/${customerId}/send-email/${emailId}`)
      toast.success('Email sent successfully', { title: 'Email Sent' })
      onRefresh()
    } catch (err) {
      toast.error('Failed to send email: ' + (err.response?.data?.detail || err.message), {
        title: 'Send Failed',
      })
      console.error(err)
    }
  }

  const handleSaveEditedEmail = async () => {
    const callIdStr = String(call?.id || '')
    const emailId = callIdStr.startsWith('email_')
      ? callIdStr.replace('email_', '')
      : call?.id

    if (!emailId) {
      toast.error('Could not determine email ID', { title: 'Error' })
      return
    }

    try {
      setSavingEmail(true)
      await api.put(`/customers/${customerId}/planned-email/${emailId}`, {
        subject: editedEmailSubject,
        content: editedEmailContent,
      })
      toast.success('Email updated successfully', { title: 'Email Updated' })
      setEditingEmail(false)
      onRefresh()
    } catch (err) {
      toast.error('Failed to save email: ' + (err.response?.data?.detail || err.message), {
        title: 'Save Failed',
      })
      console.error(err)
    } finally {
      setSavingEmail(false)
    }
  }

  const handleDeleteFile = async () => {
    if (!call || !fileToDelete) return

    try {
      let callId = String(call.id)
      if (callId.startsWith('scheduled_')) {
        callId = callId.replace('scheduled_', '')
      } else if (call.scheduled_call_id) {
        callId = call.scheduled_call_id.toString()
      }

      await api.delete(`/call-history/${callId}/file`, { params: { file_type: fileToDelete } })
      toast.success(
        `${fileToDelete.charAt(0).toUpperCase() + fileToDelete.slice(1)} file deleted successfully!`,
        { title: 'File Deleted' },
      )

      if (fileToDelete === 'planning') setPlanningContent(null)
      else if (fileToDelete === 'transcript') setTranscriptContent(null)

      setShowDeleteFileModal(false)
      setFileToDelete(null)
      onRefresh()
    } catch (err) {
      toast.error(`Failed to delete ${fileToDelete} file`, { title: 'Delete Failed' })
      console.error(err)
    }
  }

  const handleUpload = async (file, fileType) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)
    if (call?.scheduled_call_id) {
      formData.append('scheduled_call_id', call.scheduled_call_id.toString())
    }

    try {
      setUploading(true)
      await api.post(`/customers/${customerId}/upload-transcript`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast.success('File uploaded successfully!', { title: 'Upload Complete' })
      setShowUploadModal(false)
      onRefresh()
      if (call) loadDetails(call)
    } catch (err) {
      toast.error('Failed to upload file', { title: 'Upload Failed' })
      console.error(err)
    } finally {
      setUploading(false)
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

  if (!isOpen || !call) return null

  const isEmail =
    call.communication_type === 'email' || call.communication_type === 'sms'

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-gray-900">Interaction Details</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-6 w-6" />
            </button>
          </div>

          {loadingDetails ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500" />
              <p className="mt-2 text-gray-600">Loading details...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Call Info */}
              <div className="border-b border-gray-200 pb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Date:</span>
                    <span className="ml-2 font-medium">
                      {call.scheduled_time
                        ? format(new Date(call.scheduled_time), 'MMM d, yyyy h:mm a')
                        : call.sent_at
                        ? format(new Date(call.sent_at), 'MMM d, yyyy h:mm a')
                        : call.timestamp
                        ? format(new Date(call.timestamp), 'MMM d, yyyy h:mm a')
                        : 'Date not available'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Status:</span>
                    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded ${getStatusBadge(call.status)}`}>
                      {call.status}
                    </span>
                  </div>
                  {call.duration_seconds && (
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <span className="ml-2 font-medium">
                        {Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s
                      </span>
                    </div>
                  )}
                  {call.outcome && (
                    <div>
                      <span className="text-gray-500">Outcome:</span>
                      <span className="ml-2 font-medium">{call.outcome}</span>
                    </div>
                  )}
                  {call.conversation_id && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Conversation ID:</span>
                      <span className="ml-2 font-mono text-xs text-gray-700 break-all">
                        {call.conversation_id}
                      </span>
                    </div>
                  )}
                  {call.call_sid && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Call SID:</span>
                      <span className="ml-2 font-mono text-xs text-gray-700 break-all">
                        {call.call_sid}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Email Content */}
              {isEmail && call.content && (
                <div>
                  <div className="w-full flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-gray-900">
                      {call.communication_type === 'email' ? 'Email' : 'SMS'} Content
                    </h4>
                    {(call.status === 'planned' || call.status === 'pending') && (
                      <div className="flex items-center space-x-2">
                        {editingEmail ? (
                          <>
                            <button
                              onClick={() => {
                                setEditingEmail(false)
                                setEditedEmailContent(call.content || '')
                                setEditedEmailSubject(call.subject || '')
                              }}
                              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={handleSaveEditedEmail}
                              disabled={savingEmail}
                              className="px-3 py-1 text-sm bg-tangerine-500 text-white rounded hover:bg-tangerine-600 disabled:opacity-50 flex items-center space-x-1"
                            >
                              {savingEmail ? (
                                <>
                                  <div className="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                                  <span>Saving...</span>
                                </>
                              ) : (
                                <>
                                  <Check className="h-3 w-3" />
                                  <span>Save</span>
                                </>
                              )}
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => {
                                setEditingEmail(true)
                                setEditedEmailContent(call.content || '')
                                setEditedEmailSubject(call.subject || '')
                              }}
                              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center space-x-1"
                            >
                              <Edit className="h-3 w-3" />
                              <span>Edit</span>
                            </button>
                            {call.status === 'planned' && (
                              <button
                                onClick={() => {
                                  const callIdStr = String(call.id || '')
                                  const emailId = callIdStr.startsWith('email_')
                                    ? callIdStr.replace('email_', '')
                                    : call.id
                                  handleSendEmail(emailId)
                                }}
                                className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center space-x-1"
                              >
                                <Send className="h-3 w-3" />
                                <span>Send</span>
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                  {call.subject && (
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                      {editingEmail ? (
                        <input
                          type="text"
                          value={editedEmailSubject}
                          onChange={(e) => setEditedEmailSubject(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent"
                        />
                      ) : (
                        <p className="text-sm font-medium text-gray-900 bg-gray-50 p-3 rounded-lg">
                          {call.subject || 'No subject'}
                        </p>
                      )}
                    </div>
                  )}
                  {editingEmail ? (
                    <textarea
                      value={editedEmailContent}
                      onChange={(e) => setEditedEmailContent(e.target.value)}
                      rows={15}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tangerine-500 focus:border-transparent font-mono text-sm"
                    />
                  ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="prose max-w-none whitespace-pre-wrap text-sm">{call.content}</div>
                    </div>
                  )}
                </div>
              )}

              {/* AI Summary */}
              {(loadingSummary || aiSummary) && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <h4 className="text-lg font-semibold text-gray-900">AI Summary</h4>
                    {loadingSummary && (
                      <div className="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-blue-400" />
                    )}
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-gray-800">
                    {loadingSummary && !aiSummary ? (
                      <span className="text-gray-400">Generating summary...</span>
                    ) : (
                      aiSummary
                    )}
                  </div>
                </div>
              )}

              {/* Planning File */}
              {planningContent && (
                <div>
                  <div className="w-full flex items-center justify-between mb-3">
                    <h4 className="text-lg font-semibold text-gray-900">Call Planning Strategy</h4>
                    <button
                      onClick={() => { setFileToDelete('planning'); setShowDeleteFileModal(true) }}
                      className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                      title="Delete planning file"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                  <ScriptTable
                    content={planningContent}
                    showRawJson={showRawJson}
                    onToggleRawJson={setShowRawJson}
                  />
                </div>
              )}

              {/* Transcript */}
              {transcriptContent && (
                <div>
                  <div className="w-full flex items-center justify-between mb-2">
                    <button
                      onClick={() => setTranscriptExpanded(!transcriptExpanded)}
                      className="flex items-center text-left flex-1"
                    >
                      {transcriptExpanded ? (
                        <ChevronDown className="h-5 w-5 text-gray-400 mr-2" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-gray-400 mr-2" />
                      )}
                      <h4 className="text-lg font-semibold text-gray-900">Transcript</h4>
                    </button>
                    <button
                      onClick={() => { setFileToDelete('transcript'); setShowDeleteFileModal(true) }}
                      className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                      title="Delete transcript file"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                  {transcriptExpanded && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm space-y-1 max-h-96 overflow-y-auto">
                      {transcriptContent.split('\n').filter(Boolean).map((line, i) => {
                        const isAgent = line.startsWith('Agent:')
                        const isUser = line.startsWith('User:') || line.startsWith('Customer:')
                        return (
                          <p key={i} className={isAgent ? 'text-blue-800' : isUser ? 'text-gray-800' : 'text-gray-500'}>
                            {line}
                          </p>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}

              {call.status !== 'done' && call.status !== 'completed' && (
                <div className="flex justify-end">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="inline-flex items-center px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Files
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <UploadFilesModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
        uploading={uploading}
      />

      <ConfirmModal
        isOpen={showDeleteFileModal}
        onClose={() => { setShowDeleteFileModal(false); setFileToDelete(null) }}
        onConfirm={handleDeleteFile}
        title={`Delete ${fileToDelete ? fileToDelete.charAt(0).toUpperCase() + fileToDelete.slice(1) : ''} File`}
        message={fileToDelete ? `Are you sure you want to delete this ${fileToDelete} file? This action cannot be undone.` : ''}
        confirmText="Delete File"
        cancelText="Keep File"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        isLoading={false}
      />
    </>
  )
}
