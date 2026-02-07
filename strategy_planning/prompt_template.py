"""
Prompt Template for Gemini Strategy Generation

This module contains the prompt template used to generate personalized
debt collection strategies using Gemini AI.
"""

from datetime import datetime
from typing import List, Optional


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
    customer_notes: Optional[str]
) -> str:
    """
    Build the prompt for Gemini API to generate a debt collection strategy.
    
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
    
    age_str = str(age) if age else 'Unknown'
    income_str = f"${annual_income:,.2f}" if annual_income else 'Unknown'
    credit_str = str(credit_score) if credit_score else 'Unknown'
    email_str = email or 'Not provided'
    notes_str = customer_notes or 'No additional notes'
    
    prompt = f"""You are an expert debt collection strategist. Generate a personalized contact strategy for a customer.

CUSTOMER PROFILE:
- Name: {customer_first_name} {customer_last_name}
- Age: {age_str}
- Employment Status: {employment_status or 'Unknown'}
- Annual Income: {income_str}
- Credit Score: {credit_str}
- Preferred Communication Method: {preferred_channel.upper()}
- Email: {email_str}
- Phone: {phone}

DEBT INFORMATION:
- Total Outstanding Debt: ${total_debt:,.2f}
- Days Past Due: {days_past_due}
- Number of Active Debts: {len(debt_details)}

DEBT DETAILS:
{chr(10).join(debt_details) if debt_details else 'No active debts'}

PAYMENT HISTORY:
- Total Payments Made: {payment_history_count}
- Total Amount Paid: ${total_paid:,.2f}
- Recent Payments: {', '.join(recent_payments) if recent_payments else 'None'}

COMMUNICATION HISTORY:
{chr(10).join(communication_history) if communication_history else 'No recent communications'}

CUSTOMER NOTES:
{notes_str}

TASK:
Generate a comprehensive contact strategy for this customer. The customer prefers {preferred_channel.upper()} communication.

Please provide your response in the following JSON format:
{{
    "communication_channel": "{preferred_channel}",
    "tone_recommendation": "friendly_reminder|professional|urgent|final_notice",
    "best_contact_time": "morning|afternoon|evening|asap",
    "key_talking_points": ["point1", "point2", "point3"],
    "suggested_payment_amount": 0.0,
    "payment_plan_suggestion": "suggestion text or null",
    "reasoning": "brief explanation of strategy",
"""
    
    if preferred_channel == "call":
        prompt += """    "call_script": "Full conversation script with greeting, main points, and closing"
"""
    elif preferred_channel == "email":
        prompt += """    "email_subject": "Subject line",
    "email_body": "Full email content"
"""
    elif preferred_channel == "sms":
        prompt += """    "sms_message": "Full SMS text message (under 160 characters)"
"""
    else:
        prompt += """    "message_content": "General message content"
"""
    
    prompt += """}

Guidelines:
- Be empathetic and professional
- Focus on solutions, not threats
- Consider the customer's payment history and communication preferences
- Suggest realistic payment amounts based on their income and debt
- Use appropriate tone based on days past due and payment history
- For calls: Include natural conversation flow with empathy
- For emails: Professional but warm tone, clear call-to-action
- For SMS: Concise, friendly, action-oriented

Generate the strategy now:"""
    
    return prompt
