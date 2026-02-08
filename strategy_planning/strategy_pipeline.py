import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import requests

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, DebtStatus, PaymentStatus, CommunicationType, Base
)
from strategy_planning.prompt_template import (
    build_voice_prompt,
    build_email_prompt,
    classify_profile_type,
    get_customer_data_template
)


@dataclass
class GeminiStrategy:
    """AI-generated strategy from Gemini"""
    customer_id: int
    customer_name: str
    communication_channel: str
    profile_type: Optional[int] = None
    risk_level: Optional[str] = None
    
    # Call-specific fields
    call_script: Optional[str] = None
    opening_script: Optional[str] = None
    main_talking_points_script: Optional[str] = None
    objection_responses: Optional[Dict[str, str]] = None
    closing_script: Optional[str] = None
    
    # Email-specific fields
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    follow_up_date: Optional[str] = None
    follow_up_action: Optional[str] = None
    
    # SMS-specific fields
    sms_message: Optional[str] = None
    follow_up_sms: Optional[str] = None
    
    # General fields
    message_content: Optional[str] = None
    key_talking_points: List[str] = None
    suggested_payment_amount: Optional[float] = None
    payment_plan_suggestion: Optional[str] = None
    best_contact_time: Optional[str] = None
    best_contact_day: Optional[str] = None
    tone_recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    
    # Enhanced fields from profile-based prompts
    hardship_program_eligible: Optional[bool] = None
    fee_waiver_recommended: Optional[bool] = None
    escalation_needed: Optional[bool] = None
    mental_health_flags: List[str] = None
    
    def __post_init__(self):
        if self.key_talking_points is None:
            self.key_talking_points = []
        if self.mental_health_flags is None:
            self.mental_health_flags = []
        if self.objection_responses is None:
            self.objection_responses = {}


class GeminiStrategyGenerator:
    def __init__(self, db: DatabaseManager, api_key: Optional[str] = None, 
                 model: str = "google/gemini-2.5-pro",
                 institution_name: str = "Tangerine Bank",
                 agent_name: str = "John Doe",
                 support_phone: str = "1-800-555-0123",
                 support_email: str = "support@bank.com",
                 payment_portal_url: str = "https://pay.bank.com"):
        self.db = db
        self.api_key = api_key or os.getenv('OPENROUTERS_API_KEY')
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.institution_name = institution_name
        self.agent_name = agent_name
        self.support_phone = support_phone
        self.support_email = support_email
        self.payment_portal_url = payment_portal_url
        
        if not self.api_key:
            raise ValueError("OPENROUTERS_API_KEY not found. Set it in .env file or pass as parameter.")
    
    def generate_strategy(self, customer_id: int) -> GeminiStrategy:
        Base.metadata.create_all(bind=self.db.engine)
        summary = self.db.get_customer_summary(customer_id)
        if not summary:
            raise ValueError(
                f"Customer {customer_id} not found. "
                f"Please load customer data first using: uv run python DB/db_usage_example.py"
            )
        
        customer = summary['customer']
        debts = summary['debts']
        payments = summary['payments']
        communications = summary['recent_communications']
        
        # Get preferred communication method
        preferred_channel = (
            customer.preferred_communication_method.value 
            if customer.preferred_communication_method 
            else "call"
        )
        
        # Build customer context
        active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
        total_debt = sum(d.current_balance for d in active_debts)
        max_days_past_due = max((d.days_past_due for d in active_debts), default=0)
        
        # Get primary debt for additional details
        primary_debt = active_debts[0] if active_debts else None
        
        # Payment history
        completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        total_paid = sum(p.amount for p in completed_payments)
        
        # Classify profile type
        customer_tenure_years = (
            int((datetime.now() - customer.created_at).days / 365.25)
            if customer.created_at else 0
        )
        profile_type = classify_profile_type(
            credit_score=customer.credit_score,
            days_past_due=max_days_past_due,
            employment_status=customer.employment_status,
            customer_tenure_years=customer_tenure_years
        )
        
        # Prepare debt details
        debt_details = []
        for debt in active_debts:
            interest_rate_str = f"{debt.interest_rate}%" if debt.interest_rate else "N/A"
            debt_details.append(
                f"- {debt.debt_type}: ${debt.current_balance:,.2f} "
                f"(Original: ${debt.original_amount:,.2f}, "
                f"Days Past Due: {debt.days_past_due}, "
                f"Interest Rate: {interest_rate_str})"
            )
        
        # Prepare recent payments
        recent_payments = [
            f'${p.amount:.2f} on {p.payment_date.strftime("%Y-%m-%d")}' 
            for p in completed_payments[-3:]
        ]
        
        # Prepare communication history
        comm_history = [
            f"- {comm.communication_type.value} ({comm.direction}) on {comm.timestamp.strftime('%Y-%m-%d')}: "
            f"{comm.outcome or 'no outcome recorded'}"
            for comm in communications[:5]
        ]
        
        # Calculate age
        age = self._calculate_age(customer.date_of_birth) if customer.date_of_birth else None
        
        # Build address string
        address_parts = [p for p in [customer.address_line1, customer.address_line2] if p]
        address = ", ".join(address_parts) if address_parts else None
        
        # Prepare last payment date
        last_payment_date_str = None
        if completed_payments:
            last_payment = max(completed_payments, key=lambda p: p.payment_date)
            last_payment_date_str = last_payment.payment_date.strftime("%Y-%m-%d")
        
        # Prepare due date
        due_date_str = None
        if primary_debt and primary_debt.due_date:
            due_date_str = primary_debt.due_date.strftime("%Y-%m-%d")
        
        customer_data = self._prepare_customer_data_dict(
            customer=customer,
            age=age,
            total_debt=total_debt,
            days_past_due=max_days_past_due,
            debt_details=debt_details,
            payment_history_count=len(completed_payments),
            total_paid=total_paid,
            recent_payments=recent_payments,
            communication_history=comm_history,
            address=address,
            primary_debt=primary_debt,
            due_date_str=due_date_str,
            last_payment_date_str=last_payment_date_str
        )
        
        # Select prompt builder based on channel
        prompt = (
            build_email_prompt(customer_data) 
            if preferred_channel in ["email", "sms"] 
            else build_voice_prompt(customer_data)
        )
        
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
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # Raise exception for bad status codes
        
        result = response.json()
        if 'choices' not in result or not result['choices']:
            raise ValueError(f"Unexpected API response format: {result}")
        
        strategy_text = result['choices'][0]['message']['content']
        return GeminiStrategy(
            customer_id=customer_id,
            customer_name=f"{customer.first_name} {customer.last_name}",
            communication_channel=preferred_channel,
            profile_type=profile_type,
            message_content=strategy_text,
            reasoning="Raw response from Gemini AI"
        )
        
    
    def _prepare_customer_data_dict(self, customer, age, total_debt, days_past_due,
                                    debt_details, payment_history_count, total_paid,
                                    recent_payments, communication_history, address,
                                    primary_debt, due_date_str, last_payment_date_str) -> Dict[str, Any]:
        template = get_customer_data_template()
        
        template.update({
            "CUSTOMER_FIRST_NAME": customer.first_name,
            "CUSTOMER_LAST_NAME": customer.last_name,
            "CUSTOMER_AGE": str(age) if age else "Unknown",
            "CUSTOMER_DOB": customer.date_of_birth.strftime("%Y-%m-%d") if customer.date_of_birth else "",
            "CUSTOMER_EMAIL": customer.email or "",
            "CUSTOMER_PHONE_PRIMARY": customer.phone_primary,
            "CUSTOMER_PHONE_SECONDARY": customer.phone_secondary or "",
            "CUSTOMER_ADDRESS": address or "",
            "CUSTOMER_CITY": customer.city or "",
            "CUSTOMER_STATE": customer.state or "",
            "CUSTOMER_ZIP": customer.zip_code or "",
            "EMPLOYER_NAME": customer.employer_name or "",
            "EMPLOYMENT_STATUS": customer.employment_status or "",
            "ANNUAL_INCOME": f"${customer.annual_income:,.2f}" if customer.annual_income else "",
            "CREDIT_SCORE": str(customer.credit_score) if customer.credit_score else "",
            "ACCOUNT_STATUS": customer.account_status or "",
            "CUSTOMER_NOTES": customer.notes or "",
            "TOTAL_DEBT": f"${total_debt:,.2f}",
            "DAYS_PAST_DUE": str(days_past_due),
            "DEBT_TYPE": primary_debt.debt_type if primary_debt else "",
            "ORIGINAL_AMOUNT": f"${primary_debt.original_amount:,.2f}" if primary_debt else "",
            "CURRENT_BALANCE": f"${primary_debt.current_balance:,.2f}" if primary_debt else "",
            "MINIMUM_PAYMENT": f"${primary_debt.minimum_payment:,.2f}" if primary_debt and primary_debt.minimum_payment else "",
            "DUE_DATE": due_date_str or "",
            "LAST_PAYMENT_DATE": last_payment_date_str or "",
            "DEBT_STATUS": primary_debt.status.value if primary_debt else "",
            "DEBT_DETAILS_LIST": "\n".join(debt_details),
            "PAYMENT_HISTORY_COUNT": str(payment_history_count),
            "TOTAL_PAID": f"${total_paid:,.2f}",
            "RECENT_PAYMENTS_LIST": "\n".join(recent_payments),
            "COMMUNICATION_HISTORY_LIST": "\n".join(communication_history),
            "INSTITUTION_NAME": self.institution_name,
            "AGENT_NAME": self.agent_name,
            "SUPPORT_PHONE": self.support_phone,
            "SUPPORT_EMAIL": self.support_email,
            "PAYMENT_PORTAL_URL": self.payment_portal_url,
        })
        
        return template
    
    def _calculate_age(self, date_of_birth: Optional[datetime]) -> Optional[int]:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return None
        today = datetime.now()
        return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


def print_gemini_strategy(strategy: GeminiStrategy):
    """Print the raw Gemini response"""
    print("=" * 80)
    print(f"AI-GENERATED STRATEGY: {strategy.customer_name} (ID: {strategy.customer_id})")
    print(f"COMMUNICATION CHANNEL: {strategy.communication_channel.upper()}")
    if strategy.profile_type:
        print(f"PROFILE TYPE: {strategy.profile_type}")
    print("=" * 80)
    print()
    
    if strategy.message_content:
        print(strategy.message_content)
    else:
        print("No response content available.")
    
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate debt collection strategies using Gemini AI")
    parser.add_argument("--customer-id", type=int, required=True, help="Customer ID to generate strategy for")
    parser.add_argument("--model", type=str, default="google/gemini-2.5-pro", help="Gemini model to use")
    
    args = parser.parse_args()
    
    try:
        db = DatabaseManager()
        generator = GeminiStrategyGenerator(db, model=args.model)
        strategy = generator.generate_strategy(args.customer_id)
        print_gemini_strategy(strategy)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo initialize the database and load sample customers:")
        print("  uv run python DB/db_usage_example.py")
    except Exception as e:
        print(f"Error generating strategy: {e}")
        import traceback
        traceback.print_exc()
