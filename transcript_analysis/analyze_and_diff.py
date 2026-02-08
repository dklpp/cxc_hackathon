"""
Transcript Analysis and Customer Diff Pipeline

This script:
1. Reads a transcript from JSON file
2. Sends it to Gemini (via OpenRouter) for analysis
3. Compares the analysis with existing customer data
4. Shows the differences (what needs to be updated)
"""

import json
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: uv add requests")
    sys.exit(1)

from transcript_analysis.customer_diff import (
    compare_customer_data,
    print_diff_report,
    save_diff_report,
    load_customer_json
)


# Gemini API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.0-flash-001"


def get_analysis_prompt(transcript_text: str, customer_name: str = None) -> str:
    """Build the prompt for Gemini to analyze the transcript"""

    context = ""
    if customer_name:
        context = f"\nCustomer Name: {customer_name}\n"

    return f"""You are an expert call transcript analyzer for a financial services customer engagement platform.

Analyze the following call transcript and extract all relevant information.
{context}
## TRANSCRIPT
```
{transcript_text}
```

## ANALYSIS TASK

Extract and return a JSON object with this EXACT structure:

{{
    "call_metadata": {{
        "call_id": "extract or generate",
        "customer_id": "extract if mentioned or null",
        "customer_name": "extract from transcript",
        "call_duration_seconds": "estimate from length",
        "agent_name": "extract from transcript"
    }},
    "call_outcome": {{
        "primary_outcome": "one of: payment_promised, payment_made, payment_plan_agreed, hardship_reported, dispute_filed, callback_requested, no_commitment, refused_to_pay, wrong_number, voicemail, no_answer, escalation_needed, legal_mention",
        "secondary_outcomes": [],
        "success_score": 0.0,
        "follow_up_required": true
    }},
    "customer_info_extracted": {{
        "current_situation": "summarize customer's situation from call",
        "employment_status_update": "employed/unemployed/new_job or null",
        "financial_hardship_indicators": ["list any hardship signs"],
        "reason_for_non_payment": "why they can't pay or null",
        "life_events_mentioned": ["job_loss", "medical", "travel", "stress", etc.]
    }},
    "payment_info": {{
        "payment_promised": true/false,
        "payment_amount": null,
        "payment_date": null,
        "payment_method": null,
        "payment_plan_details": {{
            "monthly_amount": null,
            "start_date": null,
            "duration_months": null
        }}
    }},
    "customer_sentiment": {{
        "overall_sentiment": "positive/neutral/frustrated/angry/distressed/cooperative/confused",
        "sentiment_progression": "improved/stable/worsened",
        "key_emotions_detected": ["list emotions"],
        "rapport_level": "high/medium/low"
    }},
    "action_items": {{
        "immediate_actions": ["list next steps"],
        "follow_up_date": null,
        "follow_up_type": "call/email/sms",
        "notes_for_next_contact": "important notes"
    }},
    "compliance_flags": {{
        "legal_representation_mentioned": false,
        "dispute_requested": false,
        "cease_contact_requested": false,
        "mental_health_concerns": true/false,
        "recording_consent_given": false
    }},
    "key_quotes": [
        {{
            "speaker": "customer/agent",
            "quote": "exact important quote",
            "significance": "why it matters"
        }}
    ],
    "conversation_summary": "2-3 sentence summary",
    "recommendations": {{
        "profile_type_update": 1-5 or null,
        "risk_level_update": "low/moderate/high/severe",
        "strategy_adjustment": "recommendation for next contact"
    }}
}}

## IMPORTANT GUIDELINES
- Identify emotional distress and mental health concerns
- Note any signs of financial hardship
- Capture the customer's sentiment changes through the call
- Be accurate about what was actually committed to
- Success score: payment made (1.0), promised (0.7), plan agreed (0.6), callback (0.4), no commitment (0.2), refusal (0.1)

Return ONLY valid JSON, no additional text."""


def format_transcript(transcript_data: dict) -> str:
    """Convert transcript JSON to readable text format"""
    messages = transcript_data.get("transcript", [])
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        message = msg.get("message", "")
        lines.append(f"{role}: {message}")
    return "\n".join(lines)


def analyze_transcript_with_gemini(
    transcript_path: str,
    customer_name: str = None,
    api_key: str = None,
    model: str = DEFAULT_MODEL
) -> dict:
    """
    Send transcript to Gemini for analysis.

    Args:
        transcript_path: Path to transcript JSON file
        customer_name: Optional customer name for context
        api_key: OpenRouter API key (uses env var if not provided)
        model: Model to use

    Returns:
        Analysis result dictionary
    """
    api_key = api_key or os.getenv("OPENROUTERS_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTERS_API_KEY not found in environment")

    # Load transcript
    with open(transcript_path, 'r') as f:
        transcript_data = json.load(f)

    # Format transcript for analysis
    transcript_text = format_transcript(transcript_data)

    print(f"Analyzing transcript: {transcript_path}")
    print(f"Using model: {model}")
    print("-" * 50)

    # Build prompt
    prompt = get_analysis_prompt(transcript_text, customer_name)

    # Call Gemini via OpenRouter
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/dklpp/cxc_hackathon",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4000
    }

    print("Sending to Gemini API...")
    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        error_msg = response.text[:500]
        raise Exception(f"API error ({response.status_code}): {error_msg}")

    result = response.json()

    if 'choices' not in result or len(result['choices']) == 0:
        raise Exception(f"Unexpected API response: {result}")

    analysis_text = result['choices'][0]['message']['content']

    # Parse JSON from response
    json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
    if json_match:
        try:
            analysis = json.loads(json_match.group())
            print("Successfully parsed analysis from Gemini")
            return analysis
        except json.JSONDecodeError as e:
            print(f"Warning: JSON parse error: {e}")
            print(f"Raw response:\n{analysis_text[:1000]}")
            raise
    else:
        print(f"No JSON found in response:\n{analysis_text[:1000]}")
        raise Exception("Could not extract JSON from Gemini response")


def run_pipeline(
    transcript_path: str,
    customer_json_path: str,
    output_path: str = None,
    save_analysis: bool = True
):
    """
    Run the full pipeline:
    1. Analyze transcript with Gemini
    2. Compare with customer data
    3. Show/save diff report

    Args:
        transcript_path: Path to transcript JSON
        customer_json_path: Path to customer JSON
        output_path: Optional path to save diff report
        save_analysis: Whether to save the Gemini analysis
    """
    print("=" * 70)
    print("TRANSCRIPT ANALYSIS & DIFF PIPELINE")
    print("=" * 70)

    # Load customer data first to get name
    customer_data = load_customer_json(customer_json_path)
    customer = customer_data.get("customer", {})
    customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()

    print(f"Customer: {customer_name}")
    print(f"Transcript: {transcript_path}")
    print("=" * 70)

    # Step 1: Analyze transcript with Gemini
    print("\n[STEP 1] Analyzing transcript with Gemini...")
    analysis = analyze_transcript_with_gemini(
        transcript_path=transcript_path,
        customer_name=customer_name
    )

    # Optionally save the raw analysis
    if save_analysis:
        analysis_output = Path(transcript_path).stem + "_analysis.json"
        analysis_output_path = Path(transcript_path).parent / analysis_output
        with open(analysis_output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis saved to: {analysis_output_path}")

    # Step 2: Compare with customer data
    print("\n[STEP 2] Comparing with customer database...")
    transcript_id = Path(transcript_path).stem
    diff_report = compare_customer_data(
        transcript_analysis=analysis,
        customer_data=customer_data,
        transcript_id=transcript_id
    )

    # Step 3: Show diff report
    print("\n[STEP 3] Generating diff report...")
    print_diff_report(diff_report)

    # Optionally save diff report
    if output_path:
        save_diff_report(diff_report, output_path)

    return analysis, diff_report


# --- Main Entry Point ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze transcript and compare with customer data")
    parser.add_argument(
        "--transcript",
        default="DB/transcript_example.json",
        help="Path to transcript JSON file"
    )
    parser.add_argument(
        "--customer",
        default="DB/customers/01_maria_santos.json",
        help="Path to customer JSON file"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to save diff report JSON"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model to use"
    )

    args = parser.parse_args()

    # Run pipeline
    try:
        analysis, diff_report = run_pipeline(
            transcript_path=args.transcript,
            customer_json_path=args.customer,
            output_path=args.output
        )

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
