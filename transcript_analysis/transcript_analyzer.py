"""
Transcript Analyzer for Customer Engagement Calls

This module analyzes call transcripts from ElevenLabs and extracts
key information for dashboard tracking and customer profile updates.
"""

import json
import re
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. Install with: uv add requests")


class CallOutcome(Enum):
    """Possible outcomes of a customer call"""
    PAYMENT_PROMISED = "payment_promised"
    PAYMENT_MADE = "payment_made"
    PAYMENT_PLAN_AGREED = "payment_plan_agreed"
    HARDSHIP_REPORTED = "hardship_reported"
    DISPUTE_FILED = "dispute_filed"
    CALLBACK_REQUESTED = "callback_requested"
    NO_COMMITMENT = "no_commitment"
    REFUSED_TO_PAY = "refused_to_pay"
    WRONG_NUMBER = "wrong_number"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    ESCALATION_NEEDED = "escalation_needed"
    LEGAL_MENTION = "legal_mention"


class CustomerSentiment(Enum):
    """Customer sentiment during the call"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    DISTRESSED = "distressed"
    COOPERATIVE = "cooperative"
    CONFUSED = "confused"


# JSON Output Schema
TRANSCRIPT_ANALYSIS_SCHEMA = {
    "call_metadata": {
        "call_id": "string",
        "customer_id": "string",
        "customer_name": "string",
        "call_timestamp": "ISO8601 datetime",
        "call_duration_seconds": "integer",
        "agent_name": "string"
    },
    "call_outcome": {
        "primary_outcome": "CallOutcome enum value",
        "secondary_outcomes": ["list of additional outcomes"],
        "success_score": "float 0-1 (1 = fully successful)",
        "follow_up_required": "boolean"
    },
    "customer_info_extracted": {
        "current_situation": "string - summary of customer's situation",
        "employment_status_update": "string or null",
        "financial_hardship_indicators": ["list of indicators"],
        "reason_for_non_payment": "string or null",
        "life_events_mentioned": ["job loss", "medical", "divorce", etc.]
    },
    "payment_info": {
        "payment_promised": "boolean",
        "payment_amount": "float or null",
        "payment_date": "date string or null",
        "payment_method": "string or null",
        "payment_plan_details": {
            "monthly_amount": "float or null",
            "start_date": "date or null",
            "duration_months": "integer or null"
        }
    },
    "customer_sentiment": {
        "overall_sentiment": "CustomerSentiment enum value",
        "sentiment_progression": "improved | stable | worsened",
        "key_emotions_detected": ["list of emotions"],
        "rapport_level": "high | medium | low"
    },
    "action_items": {
        "immediate_actions": ["list of actions to take now"],
        "follow_up_date": "date or null",
        "follow_up_type": "call | email | sms | letter",
        "notes_for_next_contact": "string"
    },
    "compliance_flags": {
        "legal_representation_mentioned": "boolean",
        "dispute_requested": "boolean",
        "cease_contact_requested": "boolean",
        "mental_health_concerns": "boolean",
        "recording_consent_given": "boolean"
    },
    "key_quotes": [
        {
            "speaker": "customer | agent",
            "quote": "exact quote",
            "significance": "why this quote matters"
        }
    ],
    "conversation_summary": "string - brief summary of the call",
    "recommendations": {
        "profile_type_update": "1-5 or null if no change",
        "risk_level_update": "low | moderate | high | severe",
        "strategy_adjustment": "string - recommended next approach"
    }
}


def get_analysis_prompt(transcript: str, customer_context: Optional[Dict] = None) -> str:
    """
    Build the prompt for AI to analyze the transcript.

    Args:
        transcript: The call transcript text
        customer_context: Optional dict with customer info for context

    Returns:
        Formatted prompt string for AI analysis
    """
    context_section = ""
    if customer_context:
        context_section = f"""
## CUSTOMER CONTEXT (Pre-Call Information)
- Customer ID: {customer_context.get('customer_id', 'Unknown')}
- Name: {customer_context.get('name', 'Unknown')}
- Total Debt: {customer_context.get('total_debt', 'Unknown')}
- Days Past Due: {customer_context.get('days_past_due', 'Unknown')}
- Profile Type: {customer_context.get('profile_type', 'Unknown')}
- Previous Outcome: {customer_context.get('last_contact_outcome', 'None')}
"""

    prompt = f"""You are an expert call transcript analyzer for a financial services customer engagement platform.

Analyze the following call transcript and extract all relevant information for our customer tracking dashboard.

{context_section}

## TRANSCRIPT
```
{transcript}
```

## ANALYSIS TASK

Extract and return a JSON object with the following structure:

{{
    "call_metadata": {{
        "call_id": "generate unique ID if not provided",
        "customer_id": "extract from context or transcript",
        "customer_name": "extract from transcript",
        "call_duration_seconds": "estimate from transcript length or extract if mentioned",
        "agent_name": "extract from transcript"
    }},
    "call_outcome": {{
        "primary_outcome": "one of: payment_promised, payment_made, payment_plan_agreed, hardship_reported, dispute_filed, callback_requested, no_commitment, refused_to_pay, wrong_number, voicemail, no_answer, escalation_needed, legal_mention",
        "secondary_outcomes": ["any additional outcomes"],
        "success_score": 0.0 to 1.0,
        "follow_up_required": true/false
    }},
    "customer_info_extracted": {{
        "current_situation": "summarize what customer shared about their situation",
        "employment_status_update": "employed/unemployed/new_job/etc or null",
        "financial_hardship_indicators": ["list any hardship indicators mentioned"],
        "reason_for_non_payment": "why they haven't paid",
        "life_events_mentioned": ["job_loss", "medical", "divorce", "relocation", etc.]
    }},
    "payment_info": {{
        "payment_promised": true/false,
        "payment_amount": amount or null,
        "payment_date": "YYYY-MM-DD" or null,
        "payment_method": "bank_transfer/card/check/etc" or null,
        "payment_plan_details": {{
            "monthly_amount": amount or null,
            "start_date": "YYYY-MM-DD" or null,
            "duration_months": number or null
        }}
    }},
    "customer_sentiment": {{
        "overall_sentiment": "positive/neutral/frustrated/angry/distressed/cooperative/confused",
        "sentiment_progression": "improved/stable/worsened",
        "key_emotions_detected": ["list emotions"],
        "rapport_level": "high/medium/low"
    }},
    "action_items": {{
        "immediate_actions": ["list actions to take"],
        "follow_up_date": "YYYY-MM-DD" or null,
        "follow_up_type": "call/email/sms/letter",
        "notes_for_next_contact": "important notes for next agent"
    }},
    "compliance_flags": {{
        "legal_representation_mentioned": true/false,
        "dispute_requested": true/false,
        "cease_contact_requested": true/false,
        "mental_health_concerns": true/false,
        "recording_consent_given": true/false
    }},
    "key_quotes": [
        {{
            "speaker": "customer/agent",
            "quote": "exact quote from transcript",
            "significance": "why this matters"
        }}
    ],
    "conversation_summary": "2-3 sentence summary of the call",
    "recommendations": {{
        "profile_type_update": 1-5 or null,
        "risk_level_update": "low/moderate/high/severe",
        "strategy_adjustment": "recommended approach for next contact"
    }}
}}

## GUIDELINES
- Be precise with dates, amounts, and commitments
- Flag any compliance concerns immediately
- Capture exact quotes for important statements
- Note any changes in customer situation from previous records
- Identify actionable next steps
- Score success based on: payment obtained (1.0), payment promised (0.7), plan agreed (0.6), callback scheduled (0.4), no commitment (0.2), refusal (0.1)

Return ONLY the JSON object, no additional text."""

    return prompt


def parse_transcript_file(file_path: str) -> str:
    """
    Read and parse a transcript file.

    Supports: .txt, .json, .md formats

    Args:
        file_path: Path to the transcript file

    Returns:
        Transcript text as string
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")

    content = path.read_text(encoding='utf-8')

    # If JSON, extract transcript field
    if path.suffix == '.json':
        try:
            data = json.loads(content)
            # Try common transcript field names
            for key in ['transcript', 'text', 'conversation', 'content', 'messages']:
                if key in data:
                    if isinstance(data[key], list):
                        # Handle list of messages
                        return '\n'.join([
                            f"{msg.get('speaker', 'Unknown')}: {msg.get('text', msg.get('content', ''))}"
                            for msg in data[key]
                        ])
                    return data[key]
            # If no known key, return full JSON as string
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return content

    return content


def validate_analysis_result(result: Dict) -> List[str]:
    """
    Validate the analysis result against the expected schema.

    Args:
        result: The analysis result dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required_fields = [
        'call_outcome',
        'customer_info_extracted',
        'payment_info',
        'customer_sentiment',
        'action_items',
        'compliance_flags',
        'conversation_summary'
    ]

    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")

    # Validate call_outcome
    if 'call_outcome' in result:
        valid_outcomes = [e.value for e in CallOutcome]
        if result['call_outcome'].get('primary_outcome') not in valid_outcomes:
            errors.append(f"Invalid primary_outcome. Must be one of: {valid_outcomes}")

    # Validate sentiment
    if 'customer_sentiment' in result:
        valid_sentiments = [e.value for e in CustomerSentiment]
        if result['customer_sentiment'].get('overall_sentiment') not in valid_sentiments:
            errors.append(f"Invalid sentiment. Must be one of: {valid_sentiments}")

    # Validate payment date format if present
    if 'payment_info' in result:
        payment_date = result['payment_info'].get('payment_date')
        if payment_date:
            try:
                datetime.strptime(payment_date, '%Y-%m-%d')
            except ValueError:
                errors.append(f"Invalid payment_date format: {payment_date}. Use YYYY-MM-DD")

    return errors


def create_analysis_result_template() -> Dict[str, Any]:
    """
    Create an empty analysis result template.

    Returns:
        Dictionary with all required fields initialized
    """
    return {
        "call_metadata": {
            "call_id": None,
            "customer_id": None,
            "customer_name": None,
            "call_timestamp": datetime.utcnow().isoformat(),
            "call_duration_seconds": None,
            "agent_name": None
        },
        "call_outcome": {
            "primary_outcome": None,
            "secondary_outcomes": [],
            "success_score": 0.0,
            "follow_up_required": True
        },
        "customer_info_extracted": {
            "current_situation": None,
            "employment_status_update": None,
            "financial_hardship_indicators": [],
            "reason_for_non_payment": None,
            "life_events_mentioned": []
        },
        "payment_info": {
            "payment_promised": False,
            "payment_amount": None,
            "payment_date": None,
            "payment_method": None,
            "payment_plan_details": {
                "monthly_amount": None,
                "start_date": None,
                "duration_months": None
            }
        },
        "customer_sentiment": {
            "overall_sentiment": "neutral",
            "sentiment_progression": "stable",
            "key_emotions_detected": [],
            "rapport_level": "medium"
        },
        "action_items": {
            "immediate_actions": [],
            "follow_up_date": None,
            "follow_up_type": "call",
            "notes_for_next_contact": None
        },
        "compliance_flags": {
            "legal_representation_mentioned": False,
            "dispute_requested": False,
            "cease_contact_requested": False,
            "mental_health_concerns": False,
            "recording_consent_given": False
        },
        "key_quotes": [],
        "conversation_summary": None,
        "recommendations": {
            "profile_type_update": None,
            "risk_level_update": None,
            "strategy_adjustment": None
        }
    }


def save_analysis_result(result: Dict, output_path: str) -> None:
    """
    Save analysis result to a JSON file.

    Args:
        result: The analysis result dictionary
        output_path: Path to save the JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)


# Export schema for documentation
def get_output_schema() -> Dict:
    """
    Get the JSON output schema for documentation.

    Returns:
        Dictionary describing the output schema
    """
    return TRANSCRIPT_ANALYSIS_SCHEMA


class TranscriptAnalyzer:
    """
    Main class for analyzing call transcripts using AI (Gemini via OpenRouter).
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-2.5-pro", db_manager=None):
        """
        Initialize the transcript analyzer.
        
        Args:
            api_key: OpenRouter API key (if None, reads from OPENROUTERS_API_KEY env var)
            model: Model to use (default: google/gemini-2.5-pro)
            db_manager: Optional DatabaseManager instance for customer context
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is not installed. Install with: uv add requests")
        
        self.api_key = api_key or os.getenv('OPENROUTERS_API_KEY')
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.db_manager = db_manager
        
        if not self.api_key:
            raise ValueError("OPENROUTERS_API_KEY not found. Set it in .env file or pass as parameter.")
    
    def analyze_transcript(
        self,
        transcript: str,
        customer_id: Optional[int] = None,
        call_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a transcript and extract key information.
        
        Args:
            transcript: The call transcript text
            customer_id: Optional customer ID to fetch context from database
            call_id: Optional call ID for tracking
            output_path: Optional path to save the analysis result JSON
        
        Returns:
            Analysis result dictionary
        """
        # Get customer context if customer_id provided and db_manager available
        customer_context = None
        if customer_id and self.db_manager:
            customer_context = self._get_customer_context(customer_id)
        
        # Generate analysis prompt
        prompt = get_analysis_prompt(transcript, customer_context)
        
        # Call AI API
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/dklpp/cxc_hackathon",
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent extraction
                "max_tokens": 3000
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_response = response.json()
                    if 'error' in error_response:
                        error_detail = error_response['error'].get('message', str(error_response['error']))
                    else:
                        error_detail = str(error_response)
                except:
                    error_detail = response.text[:500]
                raise Exception(f"OpenRouter API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response format: {result}")
            
            analysis_text = result['choices'][0]['message']['content']
            
            # Parse JSON from response
            analysis_result = self._parse_ai_response(analysis_text, customer_id, call_id)
            
            # Validate result
            validation_errors = validate_analysis_result(analysis_result)
            if validation_errors:
                print(f"Warning: Validation errors found: {validation_errors}")
            
            # Save to file if output_path provided
            if output_path:
                save_analysis_result(analysis_result, output_path)
            
            return analysis_result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error analyzing transcript: {str(e)}")
    
    def analyze_transcript_file(
        self,
        transcript_path: str,
        customer_id: Optional[int] = None,
        call_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a transcript file.
        
        Args:
            transcript_path: Path to the transcript file
            customer_id: Optional customer ID to fetch context from database
            call_id: Optional call ID for tracking
            output_path: Optional path to save the analysis result JSON
        
        Returns:
            Analysis result dictionary
        """
        # Parse transcript file
        transcript = parse_transcript_file(transcript_path)
        
        # Analyze
        return self.analyze_transcript(transcript, customer_id, call_id, output_path)
    
    def _get_customer_context(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer context from database for analysis.
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Dictionary with customer context information
        """
        if not self.db_manager:
            return None
        
        try:
            summary = self.db_manager.get_customer_summary(customer_id)
            if not summary:
                return None
            
            customer = summary['customer']
            debts = summary['debts']
            active_debts = [d for d in debts if d.status.value == 'active']
            total_debt = sum(d.current_balance for d in active_debts)
            max_days_past_due = max([d.days_past_due for d in active_debts], default=0)
            
            # Get last communication outcome
            communications = summary.get('recent_communications', [])
            last_outcome = None
            if communications:
                last_outcome = communications[0].outcome
            
            # Determine profile type (simplified)
            credit_score = customer.credit_score or 650
            if credit_score >= 700 and max_days_past_due <= 30:
                profile_type = 1
            elif credit_score >= 650 and max_days_past_due <= 60:
                profile_type = 2
            elif max_days_past_due >= 120 or credit_score < 580:
                profile_type = 4
            else:
                profile_type = 3
            
            return {
                'customer_id': str(customer_id),
                'name': f"{customer.first_name} {customer.last_name}",
                'total_debt': f"${total_debt:,.2f}",
                'days_past_due': max_days_past_due,
                'profile_type': profile_type,
                'last_contact_outcome': last_outcome
            }
        except Exception as e:
            print(f"Warning: Could not fetch customer context: {e}")
            return None
    
    def _parse_ai_response(self, response_text: str, customer_id: Optional[int], call_id: Optional[str]) -> Dict[str, Any]:
        """
        Parse AI response and extract JSON.
        
        Args:
            response_text: Raw response from AI
            customer_id: Optional customer ID
            call_id: Optional call ID
        
        Returns:
            Parsed analysis result dictionary
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                
                # Ensure customer_id and call_id are set if provided
                if customer_id and 'call_metadata' in result:
                    result['call_metadata']['customer_id'] = str(customer_id)
                if call_id and 'call_metadata' in result:
                    result['call_metadata']['call_id'] = call_id
                
                # Ensure timestamp is set
                if 'call_metadata' in result and not result['call_metadata'].get('call_timestamp'):
                    result['call_metadata']['call_timestamp'] = datetime.utcnow().isoformat()
                
                return result
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse JSON from AI response: {e}")
                print(f"Response preview: {response_text[:500]}")
                # Return template with error note
                result = create_analysis_result_template()
                result['conversation_summary'] = f"Error parsing AI response: {str(e)}"
                result['call_metadata']['call_id'] = call_id or "unknown"
                if customer_id:
                    result['call_metadata']['customer_id'] = str(customer_id)
                return result
        
        # Fallback: return template
        print("Warning: No JSON found in AI response, returning template")
        result = create_analysis_result_template()
        result['conversation_summary'] = "AI response could not be parsed. Raw response: " + response_text[:500]
        result['call_metadata']['call_id'] = call_id or "unknown"
        if customer_id:
            result['call_metadata']['customer_id'] = str(customer_id)
        return result
    
    def update_database(self, analysis_result: Dict[str, Any]) -> None:
        """
        Update database with analysis results.
        
        This creates/updates:
        - CommunicationLog entry
        - Customer notes if significant changes
        - Payment records if payment was made
        
        Args:
            analysis_result: The analysis result dictionary
        """
        if not self.db_manager:
            print("Warning: No database manager provided, skipping database update")
            return
        
        try:
            customer_id = analysis_result.get('call_metadata', {}).get('customer_id')
            if not customer_id:
                print("Warning: No customer_id in analysis result, skipping database update")
                return
            
            customer_id = int(customer_id)
            
            # Get call outcome
            call_outcome = analysis_result.get('call_outcome', {})
            primary_outcome = call_outcome.get('primary_outcome', 'no_commitment')
            
            # Log communication
            from DB.db_manager import CommunicationType
            comm_log = self.db_manager.log_communication(
                customer_id=customer_id,
                communication_type=CommunicationType.CALL,
                direction='outbound',
                outcome=primary_outcome,
                duration_seconds=analysis_result.get('call_metadata', {}).get('call_duration_seconds'),
                notes=analysis_result.get('conversation_summary')
            )
            
            # Update customer notes if significant information extracted
            customer_info = analysis_result.get('customer_info_extracted', {})
            if customer_info.get('employment_status_update') or customer_info.get('current_situation'):
                notes = []
                if customer_info.get('employment_status_update'):
                    notes.append(f"Employment status update: {customer_info['employment_status_update']}")
                if customer_info.get('current_situation'):
                    notes.append(f"Situation: {customer_info['current_situation']}")
                
                customer = self.db_manager.get_customer(customer_id)
                if customer:
                    existing_notes = customer.notes or ""
                    new_notes = "\n".join(notes)
                    updated_notes = f"{existing_notes}\n[{datetime.utcnow().strftime('%Y-%m-%d')}] {new_notes}".strip()
                    self.db_manager.update_customer(customer_id, notes=updated_notes)
            
            # Create payment record if payment was made
            payment_info = analysis_result.get('payment_info', {})
            if payment_info.get('payment_promised') and payment_info.get('payment_amount'):
                # Get customer's active debts
                debts = self.db_manager.get_customer_debts(customer_id)
                active_debts = [d for d in debts if d.status.value == 'active']
                
                if active_debts:
                    # Use first active debt (or could be smarter about which debt)
                    debt = active_debts[0]
                    payment_date = payment_info.get('payment_date')
                    if payment_date:
                        try:
                            payment_dt = datetime.strptime(payment_date, '%Y-%m-%d')
                        except:
                            payment_dt = datetime.utcnow()
                    else:
                        payment_dt = datetime.utcnow()
                    
                    from DB.db_manager import PaymentStatus
                    self.db_manager.create_payment(
                        customer_id=customer_id,
                        debt_id=debt.id,
                        amount=float(payment_info['payment_amount']),
                        payment_date=payment_dt,
                        payment_method=payment_info.get('payment_method'),
                        status=PaymentStatus.PENDING  # Will be updated when payment clears
                    )
            
            print(f"✓ Database updated for customer {customer_id}")
            
        except Exception as e:
            print(f"Warning: Error updating database: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze call transcripts using AI")
    parser.add_argument("transcript_file", help="Path to transcript file (.txt, .json, .md)")
    parser.add_argument("--customer-id", type=int, help="Customer ID for database context")
    parser.add_argument("--call-id", type=str, help="Call ID for tracking")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument("--model", type=str, default="google/gemini-2.5-pro", help="AI model to use")
    parser.add_argument("--update-db", action="store_true", help="Update database with results")
    
    args = parser.parse_args()
    
    if not REQUESTS_AVAILABLE:
        print("Error: requests not installed. Install with: uv add requests")
        exit(1)
    
    # Initialize database manager if customer_id provided or update-db requested
    db_manager = None
    if args.customer_id or args.update_db:
        try:
            from DB.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
    
    try:
        # Initialize analyzer
        analyzer = TranscriptAnalyzer(model=args.model, db_manager=db_manager)
        
        # Analyze transcript
        print(f"Analyzing transcript: {args.transcript_file}")
        if args.customer_id:
            print(f"Customer ID: {args.customer_id}")
        print("This may take a few seconds...\n")
        
        result = analyzer.analyze_transcript_file(
            transcript_path=args.transcript_file,
            customer_id=args.customer_id,
            call_id=args.call_id,
            output_path=args.output
        )
        
        # Print results
        print("=" * 80)
        print("TRANSCRIPT ANALYSIS RESULTS")
        print("=" * 80)
        print(json.dumps(result, indent=2, default=str))
        
        # Update database if requested
        if args.update_db:
            print("\n" + "=" * 80)
            print("UPDATING DATABASE")
            print("=" * 80)
            analyzer.update_database(result)
        
        if args.output:
            print(f"\n✓ Results saved to: {args.output}")
        
    except Exception as e:
        print(f"Error analyzing transcript: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
