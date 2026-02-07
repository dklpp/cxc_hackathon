# Transcript Analysis Module

This module analyzes call transcripts from ElevenLabs (or any source) and extracts key information for dashboard tracking and customer profile updates.

## Overview

After a call is completed with a customer, you'll have a transcript file. This module:
1. Reads the transcript file
2. Analyzes it using AI (Gemini via OpenRouter)
3. Extracts structured information (payment promises, sentiment, outcomes, etc.)
4. Saves results as JSON
5. Optionally updates the database with the analysis

## Features

- **AI-Powered Analysis**: Uses Gemini 2.5 Pro to extract structured information
- **Customer Context**: Automatically fetches customer data from database for better analysis
- **Structured Output**: Returns JSON with standardized fields
- **Database Integration**: Can update communication logs, customer notes, and payment records
- **Multiple File Formats**: Supports .txt, .json, and .md transcript files

## Setup

1. **Install dependencies:**
   ```bash
   uv add requests python-dotenv
   ```

2. **Set environment variable:**
   Add to your `.env` file:
   ```
   OPENROUTERS_API_KEY=your_api_key_here
   ```
   Get an API key from [OpenRouter](https://openrouter.ai/keys)

## Usage

### Command Line

```bash
# Basic analysis
python transcript_analysis/transcript_analyzer.py transcript.txt

# With customer context from database
python transcript_analysis/transcript_analyzer.py transcript.txt --customer-id 1

# Save results to JSON file
python transcript_analysis/transcript_analyzer.py transcript.txt --customer-id 1 --output results.json

# Update database with results
python transcript_analysis/transcript_analyzer.py transcript.txt --customer-id 1 --update-db

# Full example
python transcript_analysis/transcript_analyzer.py transcript.txt \
    --customer-id 1 \
    --call-id "call_001" \
    --output analysis_results.json \
    --update-db
```

### Python API

```python
from transcript_analysis.transcript_analyzer import TranscriptAnalyzer
from DB.db_manager import DatabaseManager

# Initialize
db = DatabaseManager()
analyzer = TranscriptAnalyzer(db_manager=db)

# Analyze a transcript file
result = analyzer.analyze_transcript_file(
    transcript_path="transcript.txt",
    customer_id=1,
    call_id="call_001",
    output_path="results.json"
)

# Access results
print(f"Outcome: {result['call_outcome']['primary_outcome']}")
print(f"Success Score: {result['call_outcome']['success_score']}")
print(f"Payment Promised: {result['payment_info']['payment_promised']}")

# Update database
analyzer.update_database(result)
```

### Analyze Transcript String Directly

```python
transcript = """
Agent: Hello, this is Alex from First National Bank...
Customer: Yes, this is Maria...
"""

result = analyzer.analyze_transcript(
    transcript=transcript,
    customer_id=1
)
```

## Output Schema

The analysis returns a JSON object with the following structure:

```json
{
  "call_metadata": {
    "call_id": "string",
    "customer_id": "string",
    "customer_name": "string",
    "call_timestamp": "ISO8601 datetime",
    "call_duration_seconds": "integer",
    "agent_name": "string"
  },
  "call_outcome": {
    "primary_outcome": "payment_promised | payment_made | payment_plan_agreed | ...",
    "secondary_outcomes": ["list"],
    "success_score": 0.0-1.0,
    "follow_up_required": true/false
  },
  "customer_info_extracted": {
    "current_situation": "string",
    "employment_status_update": "string or null",
    "financial_hardship_indicators": ["list"],
    "reason_for_non_payment": "string or null",
    "life_events_mentioned": ["job_loss", "medical", etc.]
  },
  "payment_info": {
    "payment_promised": true/false,
    "payment_amount": "float or null",
    "payment_date": "YYYY-MM-DD or null",
    "payment_method": "string or null",
    "payment_plan_details": {
      "monthly_amount": "float or null",
      "start_date": "YYYY-MM-DD or null",
      "duration_months": "integer or null"
    }
  },
  "customer_sentiment": {
    "overall_sentiment": "positive | neutral | frustrated | angry | etc.",
    "sentiment_progression": "improved | stable | worsened",
    "key_emotions_detected": ["list"],
    "rapport_level": "high | medium | low"
  },
  "action_items": {
    "immediate_actions": ["list"],
    "follow_up_date": "YYYY-MM-DD or null",
    "follow_up_type": "call | email | sms | letter",
    "notes_for_next_contact": "string"
  },
  "compliance_flags": {
    "legal_representation_mentioned": true/false,
    "dispute_requested": true/false,
    "cease_contact_requested": true/false,
    "mental_health_concerns": true/false,
    "recording_consent_given": true/false
  },
  "key_quotes": [
    {
      "speaker": "customer | agent",
      "quote": "exact quote",
      "significance": "why this matters"
    }
  ],
  "conversation_summary": "2-3 sentence summary",
  "recommendations": {
    "profile_type_update": "1-5 or null",
    "risk_level_update": "low | moderate | high | severe",
    "strategy_adjustment": "recommended approach"
  }
}
```

## Call Outcomes

The analyzer identifies these possible outcomes:

- `payment_promised` - Customer committed to making a payment
- `payment_made` - Payment was processed during the call
- `payment_plan_agreed` - Payment plan was established
- `hardship_reported` - Customer reported financial hardship
- `dispute_filed` - Customer disputes the debt
- `callback_requested` - Customer requested a callback
- `no_commitment` - No payment commitment made
- `refused_to_pay` - Customer refused to pay
- `wrong_number` - Wrong number reached
- `voicemail` - Call went to voicemail
- `no_answer` - No answer
- `escalation_needed` - Situation requires escalation
- `legal_mention` - Legal representation mentioned

## Database Updates

When `--update-db` flag is used or `update_database()` is called, the module:

1. **Creates CommunicationLog entry** - Records the call with outcome and notes
2. **Updates Customer notes** - Adds employment status changes and situation updates
3. **Creates Payment record** - If payment was promised/made, creates a payment record

## Supported Transcript Formats

### Plain Text (.txt)
```
Agent: Hello, this is Alex...
Customer: Yes, this is Maria...
```

### JSON (.json)
```json
{
  "transcript": "Agent: Hello...\nCustomer: Yes...",
  "call_id": "call_001"
}
```

Or with messages array:
```json
{
  "messages": [
    {"speaker": "agent", "text": "Hello..."},
    {"speaker": "customer", "text": "Yes..."}
  ]
}
```

### Markdown (.md)
Standard markdown format with speaker labels.

## Example Workflow

1. **Call completes** → ElevenLabs provides transcript file
2. **Analyze transcript:**
   ```bash
   python transcript_analysis/transcript_analyzer.py \
       transcripts/call_001.txt \
       --customer-id 1 \
       --call-id "call_001" \
       --output analysis/call_001.json \
       --update-db
   ```
3. **Results saved** → JSON file ready for dashboard
4. **Database updated** → Communication log, customer notes, payment records updated
5. **Dashboard displays** → Results shown in web interface

## Error Handling

The analyzer includes robust error handling:
- Validates AI response structure
- Falls back to template if parsing fails
- Logs warnings for validation errors
- Continues even if database update fails

## Future Enhancements

- Batch processing multiple transcripts
- Integration with ElevenLabs API for automatic transcript retrieval
- Real-time analysis during calls
- Custom extraction rules per customer profile type
- Sentiment analysis visualization
- Payment prediction based on conversation patterns
