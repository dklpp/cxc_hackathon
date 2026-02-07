"""
Strategy Pipeline for Debt Collection using Gemini AI

This module generates personalized debt collection strategies using Gemini AI
via OpenRouter, including communication channel, timing, tone, and messaging.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import json
import re
import requests
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (DatabaseManager, DebtStatus, PaymentStatus, CommunicationType)
from prompt_template import build_strategy_prompt

@dataclass
class GeminiStrategy:
    """AI-generated strategy from Gemini"""
    customer_id: int
    customer_name: str
    communication_channel: str
    call_script: Optional[str] = None
    message_content: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    sms_message: Optional[str] = None
    key_talking_points: List[str] = None
    suggested_payment_amount: Optional[float] = None
    payment_plan_suggestion: Optional[str] = None
    best_contact_time: Optional[str] = None
    tone_recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    
    def __post_init__(self):
        if self.key_talking_points is None:
            self.key_talking_points = []


class GeminiStrategyGenerator:
    """Uses OpenRouter (Gemini) API to generate personalized debt collection strategies"""
    def __init__(self, db: DatabaseManager, api_key: Optional[str] = None, model: str = "google/gemini-2.5-pro"):
        self.db = db
        self.api_key = api_key or os.getenv('OPENROUTERS_API_KEY')
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("OPENROUTERS_API_KEY not found. Set it in .env file or pass as parameter.")
    
    def generate_strategy(self, customer_id: int) -> GeminiStrategy:
        summary = self.db.get_customer_summary(customer_id)
        if not summary:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer = summary['customer']
        debts = summary['debts']
        payments = summary['payments']
        communications = summary['recent_communications']
        
        # Get preferred communication method
        preferred_method = customer.preferred_communication_method
        if preferred_method:
            preferred_channel = preferred_method.value
        else:
            preferred_channel = "call"  # Default
        
        # Build customer context
        active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
        total_debt = sum(d.current_balance for d in active_debts)
        max_days_past_due = max([d.days_past_due for d in active_debts], default=0)
        
        # Payment history
        completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        total_paid = sum(p.amount for p in completed_payments)
        
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
        comm_history = []
        for comm in communications[:5]:
            comm_history.append(
                f"- {comm.communication_type.value} ({comm.direction}) on {comm.timestamp.strftime('%Y-%m-%d')}: "
                f"{comm.outcome or 'no outcome recorded'}"
            )
        
        # Calculate age
        age = self._calculate_age(customer.date_of_birth) if customer.date_of_birth else None
        
        # Build prompt using template
        prompt = build_strategy_prompt(
            customer_first_name=customer.first_name,
            customer_last_name=customer.last_name,
            age=age,
            employment_status=customer.employment_status,
            annual_income=customer.annual_income,
            credit_score=customer.credit_score,
            preferred_channel=preferred_channel,
            email=customer.email,
            phone=customer.phone_primary,
            total_debt=total_debt,
            days_past_due=max_days_past_due,
            debt_details=debt_details,
            payment_history_count=len(completed_payments),
            total_paid=total_paid,
            recent_payments=recent_payments,
            communication_history=comm_history,
            customer_notes=customer.notes
        )
        
        # Generate strategy using OpenRouter (Gemini)
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/dklpp/cxc_hackathon",  # Optional: for OpenRouter analytics
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
                "max_tokens": 2000
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            # Better error handling - show actual error from API
            if response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_response = response.json()
                    if 'error' in error_response:
                        error_detail = error_response['error'].get('message', str(error_response['error']))
                    else:
                        error_detail = str(error_response)
                except:
                    error_detail = response.text[:500]  # Limit error text length
                raise Exception(f"OpenRouter API error ({response.status_code}): {error_detail}")
            
            result = response.json()
            
            # Check if response has expected structure
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response format: {result}")
            
            strategy_text = result['choices'][0]['message']['content']
            
            # Parse Gemini response
            strategy = self._parse_gemini_response(
                customer_id=customer_id,
                customer_name=f"{customer.first_name} {customer.last_name}",
                preferred_channel=preferred_channel,
                response_text=strategy_text
            )
            
            return strategy
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating strategy: {str(e)}")
    
    def _calculate_age(self, date_of_birth: Optional[datetime]) -> Optional[int]:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return None
        today = datetime.now()
        return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    
    def _parse_gemini_response(self, customer_id: int, customer_name: str,
                              preferred_channel: str, response_text: str) -> GeminiStrategy:

        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except json.JSONDecodeError:
                return self._create_fallback_strategy(customer_id, customer_name, preferred_channel, response_text)
        else:
            return self._create_fallback_strategy(customer_id, customer_name, preferred_channel, response_text)
        
        # Create GeminiStrategy from parsed data
        strategy = GeminiStrategy(
            customer_id=customer_id,
            customer_name=customer_name,
            communication_channel=data.get('communication_channel', preferred_channel),
            call_script=data.get('call_script'),
            message_content=data.get('message_content'),
            email_subject=data.get('email_subject'),
            email_body=data.get('email_body'),
            sms_message=data.get('sms_message'),
            key_talking_points=data.get('key_talking_points', []),
            suggested_payment_amount=data.get('suggested_payment_amount'),
            payment_plan_suggestion=data.get('payment_plan_suggestion'),
            best_contact_time=data.get('best_contact_time'),
            tone_recommendation=data.get('tone_recommendation'),
            reasoning=data.get('reasoning')
        )
        
        return strategy
    
    def _create_fallback_strategy(self, customer_id: int, customer_name: str,
                                 preferred_channel: str, response_text: str) -> GeminiStrategy:
        """Create fallback strategy if JSON parsing fails"""
        return GeminiStrategy(
            customer_id=customer_id,
            customer_name=customer_name,
            communication_channel=preferred_channel,
            message_content=response_text[:500],  # Use first 500 chars
            reasoning="Generated by Gemini AI (parsed from text response)"
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate debt collection strategies using Gemini AI")
    parser.add_argument("--customer-id", type=int, required=True, help="Customer ID to generate strategy for")
    parser.add_argument("--model", type=str, default="google/gemini-2.5-pro", help="Gemini model to use")
    
    args = parser.parse_args()
    db = DatabaseManager()
    
    generator = GeminiStrategyGenerator(db, model=args.model)
    strategy = generator.generate_strategy(args.customer_id)
    print(strategy)
