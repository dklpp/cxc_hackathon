"""
Prompt Template for Transcript Analysis

This module contains prompt templates for analyzing call transcripts
and extracting key information for customer tracking and database updates.
"""

from typing import Dict, Optional


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
