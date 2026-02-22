import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

const PROFILE_TYPES = [
  {
    type: 1,
    label: "Low-Risk Service Recovery",
    risk: "Low",
    riskColor: "bg-green-100 text-green-800",
    borderColor: "border-green-300",
    headerBg: "bg-green-50",
    criteria: "Credit score ≥ 700 and days past due ≤ 30",
    characteristics: [
      "High credit score (700+)",
      "Stable employment",
      "Excellent payment history",
      "Isolated incident — technical issue, temporary oversight, or life event (travel, card expiration)",
    ],
    tone: "Friendly, service-oriented, appreciative",
    approach: "Quick resolution, fee waivers, restore autopay",
    successRate: "85–90%",
  },
  {
    type: 2,
    label: "Early Financial Stress",
    risk: "Low",
    riskColor: "bg-green-100 text-green-800",
    borderColor: "border-blue-300",
    headerBg: "bg-blue-50",
    criteria: "Credit score ≥ 650 and days past due ≤ 60",
    characteristics: [
      "Good credit score (650+)",
      "Currently employed",
      "First-time delinquency",
      "Recent life change — new job, graduation, relocation",
    ],
    tone: "Helpful, educational, non-judgmental",
    approach: "Explain situation, set up payment systems, provide resources",
    successRate: "75–80%",
  },
  {
    type: 3,
    label: "Moderate Financial Hardship",
    risk: "Moderate",
    riskColor: "bg-yellow-100 text-yellow-800",
    borderColor: "border-yellow-300",
    headerBg: "bg-yellow-50",
    criteria: "Fair credit (580–650) and 60–120 days past due",
    characteristics: [
      "Fair credit score (580–650)",
      "Employment changes or instability",
      "Multiple missed payments",
      "Root cause: income reduction, unexpected expenses, or medical issues",
    ],
    tone: "Empathetic, problem-solving, realistic",
    approach: "Payment plans, hardship assessment, flexibility",
    successRate: "60–70%",
  },
  {
    type: 4,
    label: "Severe Financial Crisis",
    risk: "High",
    riskColor: "bg-red-100 text-red-800",
    borderColor: "border-red-300",
    headerBg: "bg-red-50",
    criteria: "Days past due ≥ 120, or credit score < 580",
    characteristics: [
      "Poor credit score (< 580)",
      "Unemployment or underemployment",
      "Multiple accounts in collection",
      "120+ days past due",
      "Root cause: major life disruption — job loss, divorce, health crisis, or mental health",
    ],
    tone: "Deeply compassionate, patient, no pressure",
    approach: "Listen first, offer minimal options, provide crisis resources if needed",
    successRate: "40–50%",
    warning: "Watch for mental health indicators and offer crisis resources if needed.",
  },
  {
    type: 5,
    label: "High-Value Relationship Priority",
    risk: "VIP",
    riskColor: "bg-purple-100 text-purple-800",
    borderColor: "border-purple-300",
    headerBg: "bg-purple-50",
    criteria: "Customer tenure ≥ 5 years (takes precedence over all other criteria)",
    characteristics: [
      "Long-term customer (5+ years)",
      "Historically profitable relationship",
      "Temporary difficulty — can have any current debt status",
    ],
    tone: "Premium, personalized, accommodating",
    approach: "VIP treatment, immediate fee waivers, relationship preservation focus",
    successRate: "80–85%",
  },
];

function ProfileTypes() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Customers
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Customer Profile Types</h1>
        <p className="text-gray-600 mt-2">
          Customers are classified into one of five profile types based on their credit score,
          days past due, and account tenure. Each type defines the recommended communication
          strategy and tone.
        </p>
      </div>

      <div className="space-y-6">
        {PROFILE_TYPES.map((p) => (
          <div
            key={p.type}
            className={`bg-white rounded-lg shadow-sm border ${p.borderColor} overflow-hidden`}
          >
            <div className={`${p.headerBg} px-6 py-4 flex items-center justify-between`}>
              <div className="flex items-center space-x-3">
                <span className="text-2xl font-bold text-gray-700">Type {p.type}</span>
                <span className="text-xl font-semibold text-gray-800">{p.label}</span>
              </div>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${p.riskColor}`}>
                {p.risk} Risk
              </span>
            </div>

            <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Classification Criteria
                </h3>
                <p className="text-sm text-gray-800">{p.criteria}</p>

                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-2">
                  Characteristics
                </h3>
                <ul className="space-y-1">
                  {p.characteristics.map((c, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start">
                      <span className="text-gray-400 mr-2 mt-0.5">•</span>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Contact Strategy
                </h3>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-gray-500">Tone: </span>
                    <span className="text-sm text-gray-800">{p.tone}</span>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-gray-500">Approach: </span>
                    <span className="text-sm text-gray-800">{p.approach}</span>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-gray-500">Success Rate: </span>
                    <span className="text-sm font-semibold text-gray-800">{p.successRate}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProfileTypes;
