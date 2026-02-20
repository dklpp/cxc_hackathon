import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api from "../api/client";
import { useToastContext } from "../App";
import ConfirmModal from "../components/ConfirmModal";
import ScheduleCallModal from "../components/ScheduleCallModal";
import CallPlanningStrategyModal from "../components/CallPlanningStrategyModal";
import EmailModal from "../components/EmailModal";
import EmailPreviewModal from "../components/EmailPreviewModal";
import {
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  DollarSign,
  Calendar,
  Clock,
  FileText,
  CheckCircle,
  User,
  Briefcase,
  CreditCard,
  X,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { format } from "date-fns";

function CustomerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToastContext();
  const [customer, setCustomer] = useState(null);
  const [debts, setDebts] = useState([]);
  const [scheduledCalls, setScheduledCalls] = useState([]);
  const [callPlanningScripts, setCallPlanningScripts] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scheduling, setScheduling] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showPrepareConfirmModal, setShowPrepareConfirmModal] = useState(false);
  const [showScriptModal, setShowScriptModal] = useState(false);
  const [selectedScript, setSelectedScript] = useState(null);
  const [scheduleDateTime, setScheduleDateTime] = useState("");
  const [scheduleNotes, setScheduleNotes] = useState("");
  const [useAutoTime, setUseAutoTime] = useState(false);
  const [suggestedTime, setSuggestedTime] = useState(null);
  const [suggestedDay, setSuggestedDay] = useState(null);
  const [schedulingPlannedCallId, setSchedulingPlannedCallId] = useState(null);
  const [timeSlots, setTimeSlots] = useState([]);
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);
  const [showCancelCallModal, setShowCancelCallModal] = useState(false);
  const [callToCancel, setCallToCancel] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailType, setEmailType] = useState("email");
  const [preparingEmail, setPreparingEmail] = useState(false);
  const [plannedEmails, setPlannedEmails] = useState([]);
  const [showEmailPreviewModal, setShowEmailPreviewModal] = useState(false);
  const [previewEmail, setPreviewEmail] = useState(null);
  const [editingEmail, setEditingEmail] = useState(false);
  const [editedEmailContent, setEditedEmailContent] = useState("");
  const [editedEmailSubject, setEditedEmailSubject] = useState("");
  const [savingEmail, setSavingEmail] = useState(false);

  useEffect(() => {
    fetchCustomerDetail();
  }, [id]);

  useEffect(() => {
    if (!scheduledCalls || scheduledCalls.length === 0) return;
    const interval = setInterval(() => {
      const hasPendingPlanning = scheduledCalls.some(
        (call) => call.status === "planned" && !call.planning_script,
      );
      if (hasPendingPlanning) fetchCustomerDetail(false);
    }, 5000);
    return () => clearInterval(interval);
  }, [id, scheduledCalls]);

  const fetchCustomerDetail = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const response = await api.get(`/customers/${id}`);
      setCustomer(response.data.customer);
      setDebts(response.data.debts);
      setScheduledCalls(response.data.scheduled_calls);
      setCallPlanningScripts(response.data.call_planning_scripts || []);
      setCommunications(response.data.communications || []);
      setPlannedEmails(response.data.planned_emails || []);
      setError(null);
    } catch (err) {
      if (showLoading) setError("Failed to load customer details");
      console.error(err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleMakeCall = async () => {
    try {
      const response = await api.post(`/customers/${id}/make-call`);
      if (response.data?.success) {
        toast.success(
          "Call initiated! Transcript will be saved automatically when the call ends.",
          { title: "Make a Call", duration: 6000 },
        );
      } else {
        throw new Error("Call request failed");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to initiate the call", { title: "Make a Call", duration: 4000 });
    }
  };

  const handlePrepareCall = async () => {
    try {
      setPreparing(true);
      setShowPrepareConfirmModal(false);
      const response = await api.post(`/customers/${id}/prepare-call`);
      if (response.data && response.data.success !== false) {
        toast.success("Planning script generation started!", {
          title: "Call Preparation",
          message:
            "The planning script is being generated in the background. You can continue viewing other information while it processes.",
          duration: 6000,
        });
        await fetchCustomerDetail(false);
      } else {
        toast.error(
          "Failed to prepare call strategy: " + (response.data?.error || "Unknown error"),
          { title: "Error" },
        );
      }
    } catch (err) {
      toast.error(
        `Failed to prepare call strategy: ${err.response?.data?.detail || err.message || "Failed to prepare call strategy"}`,
        { title: "Error" },
      );
      console.error("Prepare call error:", err);
    } finally {
      setPreparing(false);
    }
  };

  const handleScheduleCall = async () => {
    let finalDateTime = null;
    if (selectedTimeSlot) {
      finalDateTime = selectedTimeSlot.start_time;
    } else if (scheduleDateTime) {
      finalDateTime = scheduleDateTime;
    } else if (useAutoTime) {
      // handled by backend
    } else {
      toast.info(
        "Please select a time slot, enter a date/time manually, or choose automatic time selection",
        { title: "Time Selection Required" },
      );
      return;
    }

    try {
      setScheduling(true);
      if (schedulingPlannedCallId) {
        await api.post(`/scheduled-calls/${schedulingPlannedCallId}/schedule`, {
          scheduled_time: finalDateTime || null,
          use_auto_time: useAutoTime && !finalDateTime,
        });
      } else {
        let scheduledTimeForAPI = null;
        if (finalDateTime) {
          if (finalDateTime.includes("T") && finalDateTime.includes("Z")) {
            scheduledTimeForAPI = finalDateTime;
          } else if (finalDateTime.includes("T")) {
            scheduledTimeForAPI = finalDateTime + "Z";
          } else {
            scheduledTimeForAPI = new Date(finalDateTime).toISOString();
          }
        }
        await api.post("/scheduled-calls", {
          customer_id: parseInt(id),
          scheduled_time: scheduledTimeForAPI,
          notes: scheduleNotes,
          agent_id: "current_user",
          use_auto_time: useAutoTime && !finalDateTime,
        });
      }

      toast.success("Call scheduled successfully!", {
        title: "Call Scheduled",
        message:
          "Strategy planning has started in the background. The planning file will be available shortly.",
        duration: 6000,
      });
      closeScheduleModal();
      fetchCustomerDetail(false);
    } catch (err) {
      toast.error(
        "Failed to schedule call: " + (err.response?.data?.detail || err.message),
        { title: "Scheduling Failed" },
      );
      console.error(err);
    } finally {
      setScheduling(false);
    }
  };

  const closeScheduleModal = () => {
    setShowScheduleModal(false);
    setScheduleDateTime("");
    setScheduleNotes("");
    setUseAutoTime(false);
    setSchedulingPlannedCallId(null);
    setSuggestedTime(null);
    setSuggestedDay(null);
    setSelectedTimeSlot(null);
    setTimeSlots([]);
  };

  const handleCancelCallClick = (callId) => {
    setCallToCancel(callId);
    setShowCancelCallModal(true);
  };

  const handleCancelCall = async () => {
    if (!callToCancel) return;
    try {
      await api.delete(`/scheduled-calls/${callToCancel}`);
      toast.success("Call cancelled successfully", { title: "Call Cancelled" });
      setShowCancelCallModal(false);
      setCallToCancel(null);
      fetchCustomerDetail(false);
    } catch (err) {
      toast.error(
        "Failed to cancel call: " + (err.response?.data?.detail || err.message),
        { title: "Cancel Failed" },
      );
      console.error(err);
    }
  };

  const handleViewScript = async (scriptId) => {
    try {
      const response = await api.get(`/call-planning-scripts/${scriptId}`);
      setSelectedScript(response.data);
      setShowScriptModal(true);
    } catch (err) {
      toast.error("Failed to load script", { title: "Error" });
      console.error(err);
    }
  };

  const openScheduleModal = async () => {
    setShowScheduleModal(true);
    setLoadingTimeSlots(true);
    setSelectedTimeSlot(null);
    try {
      const response = await api.get(`/customers/${id}/suggested-time-slots`);
      setTimeSlots(response.data.slots || []);
    } catch (err) {
      console.error("Failed to load time slots:", err);
      setTimeSlots([]);
    } finally {
      setLoadingTimeSlots(false);
    }
  };

  const handlePrepareEmail = async () => {
    try {
      setPreparingEmail(true);
      setShowEmailModal(false);
      const response = await api.post(`/customers/${id}/prepare-email`, {
        communication_type: emailType,
      });
      const emailId = response.data.email_id;
      const typeLabel = emailType === "sms" ? "SMS" : "Email";
      const loadingToastId = toast.loading(`Generating ${typeLabel.toLowerCase()} content...`, {
        title: `${typeLabel} Generation`,
      });

      let checkCount = 0;
      const maxChecks = 60;

      const checkEmailReady = async () => {
        checkCount++;
        try {
          const emailResponse = await api.get(`/customers/${id}/planned-email/${emailId}`);
          const email = emailResponse.data;

          if (
            email.content &&
            email.content !== "Generating email content..." &&
            email.status === "planned"
          ) {
            if (email.content.startsWith("Error:")) {
              toast.removeToast(loadingToastId);
              toast.error(email.content, { title: "Generation Failed" });
              return;
            }
            toast.removeToast(loadingToastId);
            setPreviewEmail(email);
            setEditedEmailContent(email.content);
            setEditedEmailSubject(email.subject || "");
            setShowEmailPreviewModal(true);
            setEditingEmail(false);
            fetchCustomerDetail(false);
          } else if (checkCount < maxChecks) {
            setTimeout(checkEmailReady, 2000);
          } else {
            toast.removeToast(loadingToastId);
            if (email.notes?.includes("Error")) {
              toast.error(email.notes, { title: "Generation Failed" });
            } else if (email.content?.includes("Error:")) {
              toast.error(email.content, { title: "Generation Failed" });
            } else {
              toast.error(
                'Email generation is taking longer than expected. Check the "Last Interactions" section.',
                { title: "Generation Timeout" },
              );
            }
          }
        } catch (err) {
          console.error("Error checking email status:", err);
          if (checkCount < maxChecks) {
            setTimeout(checkEmailReady, 2000);
          } else {
            toast.removeToast(loadingToastId);
            toast.error("Failed to check email status", { title: "Error" });
          }
        }
      };

      setTimeout(checkEmailReady, 3000);
    } catch (err) {
      toast.error(
        "Failed to prepare email: " + (err.response?.data?.detail || err.message),
        { title: "Email Preparation Failed" },
      );
      console.error(err);
    } finally {
      setPreparingEmail(false);
    }
  };

  const handleSendEmail = async (emailId) => {
    try {
      await api.post(`/customers/${id}/send-email/${emailId}`);
      toast.success("Email sent successfully", { title: "Email Sent" });
      setShowEmailPreviewModal(false);
      setPreviewEmail(null);
      fetchCustomerDetail(false);
    } catch (err) {
      toast.error(
        "Failed to send email: " + (err.response?.data?.detail || err.message),
        { title: "Send Failed" },
      );
      console.error(err);
    }
  };

  const handleDeclineEmail = async () => {
    if (!previewEmail) return;
    try {
      await api.delete(`/customers/${id}/planned-email/${previewEmail.id}`);
      toast.success("Email cancelled", { title: "Email Cancelled" });
      setShowEmailPreviewModal(false);
      setPreviewEmail(null);
      fetchCustomerDetail(false);
    } catch (err) {
      toast.error(
        "Failed to cancel email: " + (err.response?.data?.detail || err.message),
        { title: "Cancel Failed" },
      );
      console.error(err);
    }
  };

  const handleSaveEditedEmail = async () => {
    if (!previewEmail) return;
    try {
      setSavingEmail(true);
      await api.put(`/customers/${id}/planned-email/${previewEmail.id}`, {
        subject: editedEmailSubject,
        content: editedEmailContent,
      });
      toast.success("Email updated successfully", { title: "Email Updated" });
      setPreviewEmail({ ...previewEmail, subject: editedEmailSubject, content: editedEmailContent });
      setEditingEmail(false);
      fetchCustomerDetail(false);
    } catch (err) {
      toast.error(
        "Failed to save email: " + (err.response?.data?.detail || err.message),
        { title: "Save Failed" },
      );
      console.error(err);
    } finally {
      setSavingEmail(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: "bg-yellow-100 text-yellow-800",
      planned: "bg-purple-100 text-purple-800",
      completed: "bg-green-100 text-green-800",
      cancelled: "bg-red-100 text-red-800",
      missed: "bg-gray-100 text-gray-800",
      no_answer: "bg-red-100 text-red-800",
      "no answer": "bg-red-100 text-red-800",
    };
    return badges[status] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-tangerine-500" />
        <p className="mt-2 text-gray-600">Loading customer details...</p>
      </div>
    );
  }

  if (error || !customer) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error || "Customer not found"}
        </div>
      </div>
    );
  }

  const totalDebt = debts.reduce((sum, debt) => sum + (debt.current_balance || 0), 0);
  const pendingCalls = scheduledCalls.filter((call) => call.status === "pending");

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link to="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customers
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {customer.first_name}{" "}
              {customer.middle_name && `${customer.middle_name} `}
              {customer.last_name}
            </h1>
            <p className="text-gray-600 mt-1">Customer ID: {customer.id}</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleMakeCall}
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg font-medium shadow-sm hover:bg-green-700 transition-all"
            >
              <Phone className="h-4 w-4 mr-2" />
              Make AI Call
            </button>
            <button
              onClick={() => setShowPrepareConfirmModal(true)}
              disabled={preparing}
              className="inline-flex items-center px-4 py-2 bg-tangerine-500 text-white rounded-lg font-medium shadow-sm hover:bg-tangerine-600 transition-all disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {preparing ? "Preparing..." : "Create Customer Strategy"}
            </button>
            <button
              onClick={openScheduleModal}
              className="inline-flex items-center px-4 py-2 bg-tangerine-500 text-white rounded-lg font-medium shadow-sm hover:bg-tangerine-600 transition-all"
            >
              <Phone className="h-4 w-4 mr-2" />
              Schedule Automatic Call
            </button>
            <button
              onClick={() => setShowEmailModal(true)}
              className="inline-flex items-center px-4 py-2 bg-tangerine-500 text-white rounded-lg font-medium shadow-sm hover:bg-tangerine-600 transition-all"
            >
              <Mail className="h-4 w-4 mr-2" />
              Prepare Email
            </button>
          </div>
        </div>
      </div>

      {/* Customer Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Debt</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                ${totalDebt.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-red-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Credit Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {customer.credit_score || "N/A"}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Days Past Due</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {customer?.max_days_past_due || Math.max(...debts.map((d) => d.days_past_due || 0), 0)}
              </p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Calls</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">{pendingCalls.length}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Customer Details + Last Interactions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Customer Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {customer.date_of_birth && (
                <div className="flex items-center text-gray-700">
                  <Calendar className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Date of Birth</p>
                    <p className="font-medium">{format(new Date(customer.date_of_birth), "MMM d, yyyy")}</p>
                  </div>
                </div>
              )}
              {customer.ssn && (
                <div className="flex items-center text-gray-700">
                  <CreditCard className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">SSN</p>
                    <p className="font-medium">{customer.ssn}</p>
                  </div>
                </div>
              )}
              {customer.phone_primary && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Primary Phone</p>
                    <p className="font-medium">{customer.phone_primary}</p>
                  </div>
                </div>
              )}
              {customer.phone_secondary && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Secondary Phone</p>
                    <p className="font-medium">{customer.phone_secondary}</p>
                  </div>
                </div>
              )}
              {customer.email && (
                <div className="flex items-center text-gray-700">
                  <Mail className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium">{customer.email}</p>
                  </div>
                </div>
              )}
              {customer.address_line1 && (
                <div className="flex items-center text-gray-700">
                  <MapPin className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Address</p>
                    <p className="font-medium">
                      {customer.address_line1}
                      {customer.address_line2 && `, ${customer.address_line2}`}
                      {customer.city && `, ${customer.city}`}
                      {customer.state && ` ${customer.state}`}
                      {customer.zip_code && ` ${customer.zip_code}`}
                      {customer.country && `, ${customer.country}`}
                    </p>
                  </div>
                </div>
              )}
              {customer.employer_name && (
                <div className="flex items-center text-gray-700">
                  <Briefcase className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Employer</p>
                    <p className="font-medium">{customer.employer_name}</p>
                  </div>
                </div>
              )}
              {customer.employment_status && (
                <div className="flex items-center text-gray-700">
                  <User className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Employment Status</p>
                    <p className="font-medium">{customer.employment_status}</p>
                  </div>
                </div>
              )}
              {customer.annual_income && (
                <div className="flex items-center text-gray-700">
                  <DollarSign className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Annual Income</p>
                    <p className="font-medium">
                      ${customer.annual_income.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              )}
              {customer.preferred_communication_method && (
                <div className="flex items-center text-gray-700">
                  <Phone className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Preferred Contact Method</p>
                    <p className="font-medium capitalize">{customer.preferred_communication_method}</p>
                  </div>
                </div>
              )}
              {(customer.preferred_contact_time || customer.preferred_contact_days) && (
                <div className="flex items-center text-gray-700">
                  <Clock className="h-5 w-5 mr-3 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Preferred Contact Time</p>
                    <p className="font-medium">
                      {customer.preferred_contact_time && customer.preferred_contact_days
                        ? `${customer.preferred_contact_time}, ${customer.preferred_contact_days}`
                        : customer.preferred_contact_time || customer.preferred_contact_days}
                    </p>
                  </div>
                </div>
              )}
            </div>
            {customer.notes && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-500 mb-1">Notes</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{customer.notes}</p>
              </div>
            )}
          </div>
        </div>

        {/* Last Interactions */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Last Interactions</h2>
              <Link
                to={`/customer/${id}/call-history`}
                className="inline-flex items-center px-3 py-1.5 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-4 w-4 mr-2" />
                View All
              </Link>
            </div>
            {scheduledCalls.length === 0 && plannedEmails.length === 0 && communications.length === 0 ? (
              <p className="text-gray-500 text-sm">No interactions</p>
            ) : (
              <div className="space-y-3">
                {[
                  ...scheduledCalls.map((call) => ({ ...call, interactionType: "call" })),
                  ...plannedEmails.map((email) => ({ ...email, interactionType: "email" })),
                  ...communications.map((comm) => ({ ...comm, interactionType: "communication" })),
                ]
                  .filter((item) => item.status !== "cancelled")
                  .sort((a, b) => {
                    const getDate = (item) =>
                      item.scheduled_time
                        ? new Date(item.scheduled_time)
                        : item.sent_at
                        ? new Date(item.sent_at)
                        : item.timestamp
                        ? new Date(item.timestamp)
                        : new Date(item.created_at);
                    return getDate(b) - getDate(a);
                  })
                  .slice(0, 3)
                  .map((item) => {
                    if (item.interactionType === "email") {
                      return <EmailInteractionCard key={`email_${item.id}`} email={item} onSend={handleSendEmail} onCancel={handleCancelCallClick} getStatusBadge={getStatusBadge} />;
                    }
                    if (item.interactionType === "communication") {
                      return <CommunicationCard key={`comm_${item.id}`} comm={item} getStatusBadge={getStatusBadge} />;
                    }
                    return (
                      <ScheduledCallCard
                        key={item.id}
                        call={item}
                        onCancel={handleCancelCallClick}
                        onSchedule={async (callId) => {
                          try {
                            const scriptsResponse = await api.get(`/customers/${id}/call-planning-scripts`, { params: { scheduled_call_id: callId } });
                            if (scriptsResponse.data.length > 0) {
                              setSuggestedTime(scriptsResponse.data[0].suggested_time);
                              setSuggestedDay(scriptsResponse.data[0].suggested_day);
                            }
                          } catch {}
                          setSchedulingPlannedCallId(callId);
                          setShowScheduleModal(true);
                          setScheduleNotes(`Scheduling planned call ${callId}`);
                        }}
                        onViewScript={(script) => {
                          setSelectedScript(script);
                          setShowScriptModal(true);
                        }}
                        getStatusBadge={getStatusBadge}
                      />
                    );
                  })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Debts Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Debts</h2>
        {debts.length === 0 ? (
          <p className="text-gray-500">No debts found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {["Type", "Original Amount", "Current Balance", "Status", "Days Past Due", "Due Date"].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {debts.map((debt) => (
                  <tr key={debt.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{debt.debt_type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      ${debt.original_amount?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-red-600">
                      ${debt.current_balance?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        debt.status === "active" ? "bg-red-100 text-red-800"
                        : debt.status === "paid_off" ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                      }`}>
                        {debt.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{debt.days_past_due || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {debt.due_date ? format(new Date(debt.due_date), "MMM d, yyyy") : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      <CallPlanningStrategyModal
        script={showScriptModal ? selectedScript : null}
        onClose={() => { setShowScriptModal(false); setSelectedScript(null); }}
      />

      <ScheduleCallModal
        isOpen={showScheduleModal}
        onClose={closeScheduleModal}
        onSchedule={handleScheduleCall}
        suggestedTime={suggestedTime}
        suggestedDay={suggestedDay}
        timeSlots={timeSlots}
        loadingTimeSlots={loadingTimeSlots}
        selectedTimeSlot={selectedTimeSlot}
        onSelectTimeSlot={(slot) => { setSelectedTimeSlot(slot); setScheduleDateTime(""); setUseAutoTime(false); }}
        scheduleDateTime={scheduleDateTime}
        onScheduleDateTimeChange={(val) => { setScheduleDateTime(val); setSelectedTimeSlot(null); setUseAutoTime(false); }}
        scheduleNotes={scheduleNotes}
        onScheduleNotesChange={setScheduleNotes}
        useAutoTime={useAutoTime}
        onUseAutoTimeChange={(val) => { setUseAutoTime(val); if (val) { setScheduleDateTime(""); setSelectedTimeSlot(null); } }}
        scheduling={scheduling}
        title={schedulingPlannedCallId ? "Schedule Planned Call" : "Schedule Automatic Call"}
        showTimeSlots={!schedulingPlannedCallId}
        autoTimeLabel={schedulingPlannedCallId ? "Use time from planning file" : "Let AI choose the best time automatically"}
      />

      <EmailModal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
        emailType={emailType}
        onEmailTypeChange={setEmailType}
        onSubmit={handlePrepareEmail}
        preparing={preparingEmail}
      />

      <EmailPreviewModal
        email={showEmailPreviewModal ? previewEmail : null}
        editing={editingEmail}
        editedContent={editedEmailContent}
        editedSubject={editedEmailSubject}
        saving={savingEmail}
        onClose={() => { setShowEmailPreviewModal(false); setPreviewEmail(null); setEditingEmail(false); }}
        onDecline={handleDeclineEmail}
        onSend={handleSendEmail}
        onStartEdit={() => { setEditingEmail(true); setEditedEmailContent(previewEmail?.content || ""); setEditedEmailSubject(previewEmail?.subject || ""); }}
        onCancelEdit={() => { setEditingEmail(false); setEditedEmailContent(previewEmail?.content || ""); setEditedEmailSubject(previewEmail?.subject || ""); }}
        onSave={handleSaveEditedEmail}
        onContentChange={setEditedEmailContent}
        onSubjectChange={setEditedEmailSubject}
      />

      {/* Create Strategy Confirmation */}
      {showPrepareConfirmModal && customer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowPrepareConfirmModal(false)}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Create Call Strategy</h3>
              <button onClick={() => setShowPrepareConfirmModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-gray-700">
                Do you want to create a call strategy for{" "}
                <span className="font-semibold text-gray-900">{customer.first_name} {customer.last_name}</span>?
              </p>
              <p className="text-sm text-gray-500">
                This will generate a personalized planning script in the background.
              </p>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowPrepareConfirmModal(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePrepareCall}
                disabled={preparing}
                className="px-4 py-2 bg-tangerine-500 text-white rounded-lg hover:bg-tangerine-600 disabled:opacity-50 flex items-center"
              >
                {preparing ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Create Strategy
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmModal
        isOpen={showCancelCallModal}
        onClose={() => { setShowCancelCallModal(false); setCallToCancel(null); }}
        onConfirm={handleCancelCall}
        title="Cancel Scheduled Call"
        message="Are you sure you want to cancel this scheduled call? This action cannot be undone."
        confirmText="Cancel Call"
        cancelText="Keep Scheduled"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        isLoading={false}
      />
    </div>
  );
}

// ── Small inline sub-components for the Last Interactions sidebar ──────────

function EmailInteractionCard({ email, onSend, onCancel, getStatusBadge }) {
  return (
    <div className={`border border-gray-200 rounded-lg p-3 ${
      email.status === "planned" ? "bg-purple-50" : email.status === "sent" ? "bg-green-50" : "bg-gray-50"
    }`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center space-x-2">
          <Mail className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-900">
            {email.sent_at
              ? format(new Date(email.sent_at), "MMM d, yyyy h:mm a")
              : email.scheduled_send_time
              ? format(new Date(email.scheduled_send_time), "MMM d, yyyy h:mm a")
              : email.created_at
              ? format(new Date(email.created_at), "MMM d, yyyy h:mm a")
              : "Not scheduled yet"}
          </span>
          <span className="text-xs text-gray-500 uppercase">{email.communication_type}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(email.status)}`}>
            {email.status}
          </span>
          {email.status === "planned" && (
            <button onClick={() => onSend(email.id)} className="text-tangerine-500 hover:text-tangerine-600 text-xs font-medium">
              Send
            </button>
          )}
          {email.status === "planned" && (
            <button onClick={() => onCancel(`email_${email.id}`)} className="text-red-600 hover:text-red-800">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      {email.subject && <p className="text-xs font-medium text-gray-700 mt-1">Subject: {email.subject}</p>}
      {email.content && <p className="text-xs text-gray-600 mt-1 line-clamp-2">{email.content.substring(0, 100)}...</p>}
    </div>
  );
}

function CommunicationCard({ comm, getStatusBadge }) {
  const isNoAnswer = comm.outcome === "no_answer" || comm.outcome === "no answer";
  return (
    <div className={`border border-gray-200 rounded-lg p-3 ${isNoAnswer ? "bg-red-50" : "bg-green-50"}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center space-x-2">
          <Phone className={`h-4 w-4 ${isNoAnswer ? "text-red-600" : "text-green-600"}`} />
          <span className="text-sm font-medium text-gray-900">
            {comm.timestamp ? format(new Date(comm.timestamp), "MMM d, yyyy h:mm a") : "Unknown time"}
          </span>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(comm.outcome)}`}>
          {comm.outcome || "completed"}
        </span>
      </div>
      {comm.notes && <p className="text-xs text-gray-600 mt-1 line-clamp-5">{comm.notes}</p>}
    </div>
  );
}

function ScheduledCallCard({ call, onCancel, onSchedule, onViewScript, getStatusBadge }) {
  return (
    <div className={`border border-gray-200 rounded-lg p-3 ${
      call.status === "planned" ? "bg-purple-50"
      : call.status === "pending" ? "bg-yellow-50"
      : call.status === "completed" ? "bg-green-50"
      : "bg-gray-50"
    }`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center space-x-2">
          <Phone className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-900">
            {call.scheduled_time
              ? format(new Date(call.scheduled_time), "MMM d, yyyy h:mm a")
              : call.created_at
              ? format(new Date(call.created_at), "MMM d, yyyy h:mm a")
              : "Not scheduled yet"}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(call.status)}`}>
            {call.status === "pending" ? "automatic" : call.status}
          </span>
          {call.status === "planned" && (
            <button
              onClick={() => onSchedule(call.id)}
              className="text-tangerine-500 hover:text-tangerine-600 text-xs font-medium"
            >
              Schedule
            </button>
          )}
          {(call.status === "pending" || call.status === "planned") && (
            <button onClick={() => onCancel(call.id)} className="text-red-600 hover:text-red-800">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      {call.planning_script || call.planning_file_path ? (
        <div className="mt-2 p-2 bg-white rounded border border-gray-200">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-gray-700">Planning Script</span>
            {call.planning_script && (
              <button onClick={() => onViewScript(call.planning_script)} className="text-xs text-tangerine-500 hover:text-tangerine-700">
                View
              </button>
            )}
          </div>
          {call.planning_script?.suggested_time && (
            <p className="text-xs text-gray-500">
              Suggested: {call.planning_script.suggested_time}
              {call.planning_script.suggested_day && ` on ${call.planning_script.suggested_day}`}
            </p>
          )}
        </div>
      ) : (
        call.status === "planned" && !call.planning_script && !call.planning_file_path && (
          <div className="mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
            <div className="flex items-center space-x-2">
              <Clock className="h-3 w-3 text-yellow-600 animate-spin" />
              <span className="text-xs text-yellow-700">Generating planning script...</span>
            </div>
          </div>
        )
      )}
      {call.notes && <p className="text-xs text-gray-600 mt-1 line-clamp-5">{call.notes}</p>}
    </div>
  );
}

export default CustomerDetail;
