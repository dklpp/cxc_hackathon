"""
Prompt Template for AI Strategy Generation

This module contains prompt templates for generating personalized
debt collection strategies. Supports both voice (ElevenLabs) and
email/text communication channels.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


# Customer data placeholder fields
CUSTOMER_DATA_FIELDS = {
    # Personal Information
    "CUSTOMER_FIRST_NAME": "",
    "CUSTOMER_LAST_NAME": "",
    "CUSTOMER_AGE": "",
    "CUSTOMER_DOB": "",
    "CUSTOMER_EMAIL": "",
    "CUSTOMER_PHONE_PRIMARY": "",
    "CUSTOMER_PHONE_SECONDARY": "",
    "CUSTOMER_ADDRESS": "",
    "CUSTOMER_CITY": "",
    "CUSTOMER_STATE": "",
    "CUSTOMER_ZIP": "",

    # Employment & Financial
    "EMPLOYER_NAME": "",
    "EMPLOYMENT_STATUS": "",
    "ANNUAL_INCOME": "",
    "CREDIT_SCORE": "",
    "ACCOUNT_STATUS": "",
    "CUSTOMER_NOTES": "",

    # Debt Information
    "TOTAL_DEBT": "",
    "DAYS_PAST_DUE": "",
    "DEBT_TYPE": "",
    "ORIGINAL_AMOUNT": "",
    "CURRENT_BALANCE": "",
    "MINIMUM_PAYMENT": "",
    "DUE_DATE": "",
    "LAST_PAYMENT_DATE": "",
    "DEBT_STATUS": "",
    "DEBT_NOTES": "",
    "DEBT_DETAILS_LIST": "",

    # Payment History
    "PAYMENT_HISTORY_COUNT": "",
    "TOTAL_PAID": "",
    "RECENT_PAYMENTS_LIST": "",

    # Communication
    "COMMUNICATION_HISTORY_LIST": "",
    "LAST_CONTACT_DATE": "",
    "LAST_CONTACT_OUTCOME": "",
    "PREFERRED_CONTACT_TIME": "",

    # Strategy & Classification
    "PROFILE_TYPE": "",
    "RISK_LEVEL": "",
    "RECOMMENDED_STRATEGY": "",

    # System
    "CURRENT_DATE": "",
    "CURRENT_TIME": "",
    "AGENT_NAME": "",
    "INSTITUTION_NAME": "",
    "SUPPORT_PHONE": "",
    "SUPPORT_EMAIL": "",
    "PAYMENT_PORTAL_URL": "",
}


def get_prompts_dir() -> Path:
    """Get the path to the prompts directory."""
    return Path(__file__).parent.parent / "prompts"


def load_master_prompt(channel: str = "voice") -> str:
    """
    Load the master prompt template for the specified channel.

    Args:
        channel: Either "voice" for ElevenLabs or "email" for text communication

    Returns:
        The master prompt template as a string
    """
    prompts_dir = get_prompts_dir()

    if channel == "voice":
        prompt_file = prompts_dir / "master_prompt_voice.md"
    elif channel == "email":
        prompt_file = prompts_dir / "master_prompt_email.md"
    else:
        raise ValueError(f"Unknown channel: {channel}. Use 'voice' or 'email'.")

    if not prompt_file.exists():
        raise FileNotFoundError(f"Master prompt not found: {prompt_file}")

    return prompt_file.read_text()


def fill_customer_data(template: str, customer_data: Dict[str, Any]) -> str:
    """
    Fill in customer data placeholders in the template.

    Args:
        template: The prompt template with {{PLACEHOLDER}} fields
        customer_data: Dictionary of customer data to fill in

    Returns:
        Template with placeholders replaced with actual data
    """
    filled = template

    for key, value in customer_data.items():
        placeholder = "{{" + key + "}}"
        if value is not None:
            filled = filled.replace(placeholder, str(value))
        else:
            filled = filled.replace(placeholder, "Not available")

    return filled


def classify_profile_type(
    credit_score: Optional[int],
    days_past_due: int,
    employment_status: Optional[str],
    customer_tenure_years: int = 0
) -> int:
    """
    Classify customer into profile type (1-5) based on their data.

    Returns:
        Profile type number (1-5)
    """
    # Profile Type 5: High-Value Relationship Priority
    if customer_tenure_years >= 5:
        return 5

    # Profile Type 1: Low-Risk Service Recovery
    if credit_score and credit_score >= 700 and days_past_due <= 30:
        return 1

    # Profile Type 2: Early Financial Stress
    if credit_score and credit_score >= 650 and days_past_due <= 60:
        return 2

    # Profile Type 4: Severe Financial Crisis
    if days_past_due >= 120 or (credit_score and credit_score < 580):
        return 4

    # Profile Type 3: Moderate Financial Hardship (default for middle cases)
    return 3


def build_strategy_prompt(
    customer_first_name: str,
    customer_last_name: str,
    age: Optional[int],
    employment_status: Optional[str],
    annual_income: Optional[float],
    credit_score: Optional[int],
    preferred_channel: str,
    email: Optional[str],
    phone: str,
    total_debt: float,
    days_past_due: int,
    debt_details: List[str],
    payment_history_count: int,
    total_paid: float,
    recent_payments: List[str],
    communication_history: List[str],
    customer_notes: Optional[str],
    # Additional fields for enhanced prompts
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    employer_name: Optional[str] = None,
    debt_type: Optional[str] = None,
    current_balance: Optional[float] = None,
    minimum_payment: Optional[float] = None,
    due_date: Optional[str] = None,
    last_payment_date: Optional[str] = None,
    institution_name: str = "First National Bank",
    agent_name: str = "Alex",
    support_phone: str = "1-800-555-0123",
    support_email: str = "support@bank.com",
    payment_portal_url: str = "https://pay.bank.com"
) -> str:
    """
    Build the prompt for AI to generate a debt collection strategy.

    This function creates a comprehensive prompt by:
    1. Classifying the customer profile type
    2. Preparing all customer data fields
    3. Building a structured prompt for the AI

    Args:
        customer_first_name: Customer's first name
        customer_last_name: Customer's last name
        age: Customer's age (if available)
        employment_status: Employment status
        annual_income: Annual income
        credit_score: Credit score
        preferred_channel: Preferred communication channel (call, email, sms)
        email: Customer email
        phone: Customer phone number
        total_debt: Total outstanding debt
        days_past_due: Maximum days past due
        debt_details: List of debt detail strings
        payment_history_count: Number of payments made
        total_paid: Total amount paid
        recent_payments: List of recent payment strings
        communication_history: List of communication history strings
        customer_notes: Additional customer notes

    Returns:
        Formatted prompt string
    """

    # Classify profile type
    profile_type = classify_profile_type(
        credit_score=credit_score,
        days_past_due=days_past_due,
        employment_status=employment_status
    )

    # Determine risk level
    if profile_type in [1, 2]:
        risk_level = "low"
    elif profile_type == 3:
        risk_level = "moderate"
    elif profile_type == 4:
        risk_level = "high"
    else:
        risk_level = "vip"

    # Prepare customer data dictionary
    customer_data = {
        "CUSTOMER_FIRST_NAME": customer_first_name,
        "CUSTOMER_LAST_NAME": customer_last_name,
        "CUSTOMER_AGE": age if age else "Unknown",
        "CUSTOMER_EMAIL": email if email else "Not provided",
        "CUSTOMER_PHONE_PRIMARY": phone,
        "CUSTOMER_ADDRESS": address if address else "Not provided",
        "CUSTOMER_CITY": city if city else "",
        "CUSTOMER_STATE": state if state else "",
        "CUSTOMER_ZIP": zip_code if zip_code else "",
        "EMPLOYER_NAME": employer_name if employer_name else "Not provided",
        "EMPLOYMENT_STATUS": employment_status if employment_status else "Unknown",
        "ANNUAL_INCOME": f"${annual_income:,.2f}" if annual_income else "Unknown",
        "CREDIT_SCORE": credit_score if credit_score else "Unknown",
        "CUSTOMER_NOTES": customer_notes if customer_notes else "No additional notes",
        "TOTAL_DEBT": f"${total_debt:,.2f}",
        "DAYS_PAST_DUE": days_past_due,
        "DEBT_TYPE": debt_type if debt_type else "Various",
        "CURRENT_BALANCE": f"${current_balance:,.2f}" if current_balance else f"${total_debt:,.2f}",
        "MINIMUM_PAYMENT": f"${minimum_payment:,.2f}" if minimum_payment else "Contact for details",
        "DUE_DATE": due_date if due_date else "See statement",
        "LAST_PAYMENT_DATE": last_payment_date if last_payment_date else "No recent payment",
        "DEBT_DETAILS_LIST": "\n".join(debt_details) if debt_details else "No active debts",
        "PAYMENT_HISTORY_COUNT": payment_history_count,
        "TOTAL_PAID": f"${total_paid:,.2f}",
        "RECENT_PAYMENTS_LIST": "\n".join(recent_payments) if recent_payments else "None",
        "COMMUNICATION_HISTORY_LIST": "\n".join(communication_history) if communication_history else "No recent communications",
        "PROFILE_TYPE": profile_type,
        "RISK_LEVEL": risk_level,
        "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
        "CURRENT_TIME": datetime.now().strftime("%H:%M"),
        "AGENT_NAME": agent_name,
        "INSTITUTION_NAME": institution_name,
        "SUPPORT_PHONE": support_phone,
        "SUPPORT_EMAIL": support_email,
        "PAYMENT_PORTAL_URL": payment_portal_url,
    }

    # Build the prompt
    prompt = f"""You are an expert debt collection strategist. Analyze the customer data and generate a personalized contact strategy.

## CUSTOMER PROFILE (Type {profile_type} - {risk_level.upper()} RISK)

### Personal Information
- Name: {customer_first_name} {customer_last_name}
- Age: {customer_data['CUSTOMER_AGE']}
- Email: {customer_data['CUSTOMER_EMAIL']}
- Phone: {phone}
- Location: {city}, {state} {zip_code}

### Employment & Financial
- Employer: {customer_data['EMPLOYER_NAME']}
- Employment Status: {customer_data['EMPLOYMENT_STATUS']}
- Annual Income: {customer_data['ANNUAL_INCOME']}
- Credit Score: {customer_data['CREDIT_SCORE']}

### Debt Information
- Total Outstanding: {customer_data['TOTAL_DEBT']}
- Days Past Due: {days_past_due}
- Number of Active Debts: {len(debt_details)}

### Debt Details
{customer_data['DEBT_DETAILS_LIST']}

### Payment History
- Total Payments Made: {payment_history_count}
- Total Amount Paid: {customer_data['TOTAL_PAID']}
- Recent Payments:
{customer_data['RECENT_PAYMENTS_LIST']}

### Communication History
{customer_data['COMMUNICATION_HISTORY_LIST']}

### Customer Notes
{customer_data['CUSTOMER_NOTES']}

---

## TASK

Generate a comprehensive contact strategy for this **Profile Type {profile_type}** customer.
Preferred communication channel: **{preferred_channel.upper()}**

Provide your response in the following JSON format:
{{
    "profile_type": {profile_type},
    "risk_level": "{risk_level}",
    "communication_channel": "{preferred_channel}",
    "tone_recommendation": "friendly_reminder|professional|empathetic|urgent|compassionate",
    "best_contact_time": "morning|afternoon|evening|weekend",
    "best_contact_day": "monday|tuesday|wednesday|thursday|friday|saturday",
    "key_talking_points": ["point1", "point2", "point3"],
    "suggested_payment_amount": 0.0,
    "payment_plan_suggestion": "suggestion text or null",
    "hardship_program_eligible": true|false,
    "fee_waiver_recommended": true|false,
    "escalation_needed": true|false,
    "mental_health_flags": [],
    "reasoning": "brief explanation of strategy",
"""

    # Add channel-specific output fields
    if preferred_channel == "call":
        prompt += """    "opening_script": "Natural greeting and opening",
    "main_talking_points_script": "Key conversation points",
    "objection_responses": {"objection1": "response1"},
"""
    elif preferred_channel == "email":
        prompt += """    "email_subject": "Subject line",
    "email_body": "Full email content with proper formatting",
    "follow_up_date": "YYYY-MM-DD",
    "follow_up_action": "Description of next step"
"""
    elif preferred_channel == "sms":
        prompt += """    "sms_message": "Full SMS text message (under 160 characters)",
    "follow_up_sms": "Follow-up message if no response"
"""
    else:
        prompt += """    "message_content": "General message content"
"""

    prompt += """}

## STRATEGY GUIDELINES BY PROFILE TYPE

**Profile Type 1 (Low-Risk Service Recovery):**
- Tone: Friendly, service-oriented, appreciative
- Approach: Quick resolution, fee waivers, restore autopay
- Success rate: 85-90%

**Profile Type 2 (Early Financial Stress):**
- Tone: Helpful, educational, non-judgmental
- Approach: Explain situation, set up systems, provide resources
- Success rate: 75-80%

**Profile Type 3 (Moderate Financial Hardship):**
- Tone: Empathetic, problem-solving, realistic
- Approach: Payment plans, hardship assessment, flexibility
- Success rate: 60-70%

**Profile Type 4 (Severe Financial Crisis):**
- Tone: Deeply compassionate, patient, no pressure
- Approach: Listen first, offer minimal options, provide resources
- Success rate: 35-45%
- IMPORTANT: Watch for mental health indicators, offer crisis resources if needed

**Profile Type 5 (High-Value Relationship):**
- Tone: Premium, personalized, accommodating
- Approach: VIP treatment, immediate fee waivers, relationship focus
- Success rate: 90-95%

## COMPLIANCE REMINDERS
- Never threaten or use abusive language
- Respect contact time restrictions (8 AM - 9 PM local)
- Include required disclosures for written communications
- If customer mentions legal representation, cease collection discussion

Generate the strategy now:"""

    return prompt


def build_voice_prompt(customer_data: Dict[str, Any]) -> str:
    """
    Build a prompt specifically for ElevenLabs voice agent.

    Args:
        customer_data: Dictionary containing all customer fields

    Returns:
        Formatted voice prompt with customer data filled in
    """
    try:
        master_prompt = load_master_prompt("voice")
        return fill_customer_data(master_prompt, customer_data)
    except FileNotFoundError:
        # Fallback to building inline if master prompt not found
        return build_strategy_prompt(
            customer_first_name=customer_data.get("CUSTOMER_FIRST_NAME", "Customer"),
            customer_last_name=customer_data.get("CUSTOMER_LAST_NAME", ""),
            age=customer_data.get("CUSTOMER_AGE"),
            employment_status=customer_data.get("EMPLOYMENT_STATUS"),
            annual_income=customer_data.get("ANNUAL_INCOME"),
            credit_score=customer_data.get("CREDIT_SCORE"),
            preferred_channel="call",
            email=customer_data.get("CUSTOMER_EMAIL"),
            phone=customer_data.get("CUSTOMER_PHONE_PRIMARY", ""),
            total_debt=float(customer_data.get("TOTAL_DEBT", 0)),
            days_past_due=int(customer_data.get("DAYS_PAST_DUE", 0)),
            debt_details=[],
            payment_history_count=int(customer_data.get("PAYMENT_HISTORY_COUNT", 0)),
            total_paid=float(customer_data.get("TOTAL_PAID", 0)),
            recent_payments=[],
            communication_history=[],
            customer_notes=customer_data.get("CUSTOMER_NOTES")
        )


def build_email_prompt(customer_data: Dict[str, Any]) -> str:
    """
    Build a prompt specifically for email/text communication.

    Args:
        customer_data: Dictionary containing all customer fields

    Returns:
        Formatted email prompt with customer data filled in
    """
    try:
        master_prompt = load_master_prompt("email")
        return fill_customer_data(master_prompt, customer_data)
    except FileNotFoundError:
        # Fallback to building inline if master prompt not found
        return build_strategy_prompt(
            customer_first_name=customer_data.get("CUSTOMER_FIRST_NAME", "Customer"),
            customer_last_name=customer_data.get("CUSTOMER_LAST_NAME", ""),
            age=customer_data.get("CUSTOMER_AGE"),
            employment_status=customer_data.get("EMPLOYMENT_STATUS"),
            annual_income=customer_data.get("ANNUAL_INCOME"),
            credit_score=customer_data.get("CREDIT_SCORE"),
            preferred_channel="email",
            email=customer_data.get("CUSTOMER_EMAIL"),
            phone=customer_data.get("CUSTOMER_PHONE_PRIMARY", ""),
            total_debt=float(customer_data.get("TOTAL_DEBT", 0)),
            days_past_due=int(customer_data.get("DAYS_PAST_DUE", 0)),
            debt_details=[],
            payment_history_count=int(customer_data.get("PAYMENT_HISTORY_COUNT", 0)),
            total_paid=float(customer_data.get("TOTAL_PAID", 0)),
            recent_payments=[],
            communication_history=[],
            customer_notes=customer_data.get("CUSTOMER_NOTES")
        )


# Export available placeholder fields for reference
def get_customer_data_template() -> Dict[str, str]:
    """
    Get a template dictionary with all available customer data fields.

    Returns:
        Dictionary with all placeholder field names and empty values
    """
    return CUSTOMER_DATA_FIELDS.copy()
