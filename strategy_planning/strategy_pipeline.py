"""
Strategy Pipeline for Debt Collection

This module analyzes customer data and generates optimal contact strategies
for debt collection, including communication channel, timing, tone, and messaging.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, DebtStatus, PaymentStatus, CommunicationType
)


class UrgencyLevel(Enum):
    """Urgency level for debt collection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationChannel(Enum):
    """Recommended communication channels"""
    CALL = "call"
    EMAIL = "email"
    SMS = "sms"
    MULTI_CHANNEL = "multi_channel"  # Use multiple channels


class Tone(Enum):
    """Message tone/approach"""
    FRIENDLY_REMINDER = "friendly_reminder"
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    FINAL_NOTICE = "final_notice"


@dataclass
class ContactStrategy:
    """Contact strategy for a customer"""
    customer_id: int
    customer_name: str
    
    # Strategy recommendations
    recommended_channel: CommunicationChannel
    urgency_level: UrgencyLevel
    tone: Tone
    
    # Timing
    recommended_contact_time: str  # e.g., "morning", "afternoon", "evening", "asap"
    days_since_last_contact: Optional[int]
    
    # Messaging
    suggested_message: str
    suggested_payment_amount: Optional[float]
    payment_plan_suggestion: Optional[str]
    
    # Analysis
    risk_score: float  # 0-100, higher = more risk
    payment_probability: float  # 0-100, estimated likelihood of payment
    reasoning: List[str]  # List of reasons for this strategy
    
    # Customer context
    total_debt: float
    days_past_due: int
    payment_history_score: float  # 0-100
    communication_responsiveness: float  # 0-100


class StrategyAnalyzer:
    """Analyzes customer data and generates contact strategies"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def analyze_customer(self, customer_id: int) -> ContactStrategy:
        """
        Analyze a customer and generate a contact strategy.
        
        Args:
            customer_id: ID of the customer to analyze
            
        Returns:
            ContactStrategy object with recommendations
        """
        summary = self.db.get_customer_summary(customer_id)
        if not summary:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer = summary['customer']
        debts = summary['debts']
        payments = summary['payments']
        communications = summary['recent_communications']
        
        # Calculate key metrics
        total_debt = summary['total_debt']
        active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
        
        # Get the most urgent debt
        max_days_past_due = max([d.days_past_due for d in active_debts], default=0)
        largest_debt = max(active_debts, key=lambda d: d.current_balance) if active_debts else None
        
        # Analyze payment history
        payment_history_score = self._calculate_payment_history_score(payments)
        
        # Analyze communication responsiveness
        communication_responsiveness = self._calculate_communication_responsiveness(communications)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            customer, total_debt, max_days_past_due, 
            payment_history_score, communication_responsiveness
        )
        
        # Determine urgency
        urgency_level = self._determine_urgency(total_debt, max_days_past_due, risk_score)
        
        # Determine communication channel
        recommended_channel = self._determine_channel(
            customer, communications, urgency_level, communication_responsiveness
        )
        
        # Determine tone
        tone = self._determine_tone(urgency_level, max_days_past_due, payment_history_score)
        
        # Determine timing
        recommended_contact_time = self._determine_timing(customer, communications, urgency_level)
        
        # Calculate days since last contact
        days_since_last_contact = self._days_since_last_contact(communications)
        
        # Generate message
        suggested_message = self._generate_message(
            customer, total_debt, largest_debt, tone, urgency_level
        )
        
        # Suggest payment amount
        suggested_payment_amount = self._suggest_payment_amount(
            total_debt, largest_debt, payment_history_score, customer
        )
        
        # Payment plan suggestion
        payment_plan_suggestion = self._suggest_payment_plan(
            total_debt, customer, payment_history_score
        )
        
        # Estimate payment probability
        payment_probability = self._estimate_payment_probability(
            payment_history_score, communication_responsiveness, 
            urgency_level, customer
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            customer, total_debt, max_days_past_due, payment_history_score,
            communication_responsiveness, urgency_level, recommended_channel
        )
        
        return ContactStrategy(
            customer_id=customer_id,
            customer_name=f"{customer.first_name} {customer.last_name}",
            recommended_channel=recommended_channel,
            urgency_level=urgency_level,
            tone=tone,
            recommended_contact_time=recommended_contact_time,
            days_since_last_contact=days_since_last_contact,
            suggested_message=suggested_message,
            suggested_payment_amount=suggested_payment_amount,
            payment_plan_suggestion=payment_plan_suggestion,
            risk_score=risk_score,
            payment_probability=payment_probability,
            reasoning=reasoning,
            total_debt=total_debt,
            days_past_due=max_days_past_due,
            payment_history_score=payment_history_score,
            communication_responsiveness=communication_responsiveness
        )
    
    def _calculate_payment_history_score(self, payments: List) -> float:
        """Calculate payment history score (0-100)"""
        if not payments:
            return 30.0  # No history = moderate risk
        
        completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        failed_payments = [p for p in payments if p.status == PaymentStatus.FAILED]
        
        total_payments = len(payments)
        if total_payments == 0:
            return 30.0
        
        # Base score from completion rate
        completion_rate = len(completed_payments) / total_payments
        base_score = completion_rate * 70  # Max 70 points for completion rate
        
        # Bonus for recent payments
        recent_payments = [p for p in completed_payments 
                          if (datetime.utcnow() - p.payment_date).days < 90]
        if recent_payments:
            base_score += 20
        
        # Penalty for failed payments
        if failed_payments:
            base_score -= len(failed_payments) * 5
        
        return max(0, min(100, base_score))
    
    def _calculate_communication_responsiveness(self, communications: List) -> float:
        """Calculate communication responsiveness score (0-100)"""
        if not communications:
            return 50.0  # Neutral if no history
        
        outbound = [c for c in communications if c.direction == "outbound"]
        inbound = [c for c in communications if c.direction == "inbound"]
        
        # Check for positive outcomes
        positive_outcomes = ["payment_promised", "payment_made", "agreed_to_pay", "payment_plan_setup"]
        positive_communications = [c for c in communications 
                                  if c.outcome and any(po in c.outcome.lower() for po in positive_outcomes)]
        
        # Responsiveness based on inbound/outbound ratio and positive outcomes
        if len(outbound) == 0:
            return 30.0
        
        response_rate = len(inbound) / len(outbound) if outbound else 0
        positive_rate = len(positive_communications) / len(outbound) if outbound else 0
        
        score = (response_rate * 40) + (positive_rate * 60)
        return max(0, min(100, score))
    
    def _calculate_risk_score(self, customer, total_debt: float, days_past_due: int,
                             payment_history_score: float, communication_responsiveness: float) -> float:
        """Calculate overall risk score (0-100, higher = more risk)"""
        risk = 0.0
        
        # Debt amount risk (normalized to 0-30)
        if total_debt > 50000:
            risk += 30
        elif total_debt > 20000:
            risk += 20
        elif total_debt > 10000:
            risk += 15
        elif total_debt > 5000:
            risk += 10
        else:
            risk += 5
        
        # Days past due risk (0-30)
        if days_past_due > 90:
            risk += 30
        elif days_past_due > 60:
            risk += 25
        elif days_past_due > 30:
            risk += 20
        elif days_past_due > 15:
            risk += 15
        elif days_past_due > 0:
            risk += 10
        
        # Payment history risk (inverse of score, 0-20)
        risk += (100 - payment_history_score) * 0.2
        
        # Communication risk (inverse of responsiveness, 0-20)
        risk += (100 - communication_responsiveness) * 0.2
        
        # Employment status risk
        if customer.employment_status and customer.employment_status.lower() in ["unemployed", "retired"]:
            risk += 10
        
        # Credit score risk
        if customer.credit_score:
            if customer.credit_score < 600:
                risk += 10
            elif customer.credit_score < 650:
                risk += 5
        
        return min(100, risk)
    
    def _determine_urgency(self, total_debt: float, days_past_due: int, risk_score: float) -> UrgencyLevel:
        """Determine urgency level"""
        if days_past_due > 90 or risk_score > 80 or total_debt > 50000:
            return UrgencyLevel.CRITICAL
        elif days_past_due > 60 or risk_score > 60 or total_debt > 20000:
            return UrgencyLevel.HIGH
        elif days_past_due > 30 or risk_score > 40 or total_debt > 10000:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    def _determine_channel(self, customer, communications: List, 
                          urgency_level: UrgencyLevel, responsiveness: float) -> CommunicationChannel:
        """Determine best communication channel"""
        # Check customer preferences from notes
        notes = customer.notes or ""
        if "email" in notes.lower() and "prefer" in notes.lower():
            return CommunicationChannel.EMAIL
        if "phone" in notes.lower() and "prefer" in notes.lower():
            return CommunicationChannel.CALL
        
        # Check recent communication success
        recent_comms = [c for c in communications if (datetime.utcnow() - c.timestamp).days < 30]
        if recent_comms:
            successful_types = {}
            for comm in recent_comms:
                if comm.outcome and "payment" in comm.outcome.lower():
                    comm_type = comm.communication_type.value
                    successful_types[comm_type] = successful_types.get(comm_type, 0) + 1
            
            if successful_types:
                best_type = max(successful_types.items(), key=lambda x: x[1])[0]
                if best_type == "call":
                    return CommunicationChannel.CALL
                elif best_type == "email":
                    return CommunicationChannel.EMAIL
                elif best_type == "sms":
                    return CommunicationChannel.SMS
        
        # Default based on urgency
        if urgency_level == UrgencyLevel.CRITICAL:
            return CommunicationChannel.MULTI_CHANNEL
        elif urgency_level == UrgencyLevel.HIGH:
            return CommunicationChannel.CALL
        elif responsiveness > 70:
            return CommunicationChannel.EMAIL
        else:
            return CommunicationChannel.CALL
    
    def _determine_tone(self, urgency_level: UrgencyLevel, days_past_due: int, 
                       payment_history_score: float) -> Tone:
        """Determine appropriate tone"""
        if urgency_level == UrgencyLevel.CRITICAL or days_past_due > 90:
            return Tone.FINAL_NOTICE
        elif urgency_level == UrgencyLevel.HIGH or days_past_due > 60:
            return Tone.URGENT
        elif payment_history_score > 70:
            return Tone.FRIENDLY_REMINDER
        else:
            return Tone.PROFESSIONAL
    
    def _determine_timing(self, customer, communications: List, urgency_level: UrgencyLevel) -> str:
        """Determine best time to contact"""
        if urgency_level == UrgencyLevel.CRITICAL:
            return "asap"
        
        # Check if there's a pattern in successful contact times
        successful_comms = [c for c in communications 
                          if c.outcome and "payment" in c.outcome.lower()]
        if successful_comms:
            # Analyze timestamps (simplified - would need timezone handling in production)
            return "morning"  # Default to morning
        
        # Default based on urgency
        if urgency_level == UrgencyLevel.HIGH:
            return "morning"
        else:
            return "afternoon"
    
    def _days_since_last_contact(self, communications: List) -> Optional[int]:
        """Calculate days since last outbound contact"""
        outbound = [c for c in communications if c.direction == "outbound"]
        if not outbound:
            return None
        
        most_recent = max(outbound, key=lambda c: c.timestamp)
        return (datetime.utcnow() - most_recent.timestamp).days
    
    def _generate_message(self, customer, total_debt: float, largest_debt, 
                         tone: Tone, urgency_level: UrgencyLevel) -> str:
        """Generate suggested message based on tone and urgency"""
        name = customer.first_name
        
        if tone == Tone.FRIENDLY_REMINDER:
            return (
                f"Hi {name}, this is a friendly reminder about your outstanding balance of "
                f"${total_debt:,.2f}. We're here to help you find a payment solution that works "
                f"for you. Please contact us at your earliest convenience."
            )
        elif tone == Tone.PROFESSIONAL:
            return (
                f"Dear {name}, we're reaching out regarding your account balance of "
                f"${total_debt:,.2f}. To avoid further action, please arrange payment or contact "
                f"us to discuss payment options."
            )
        elif tone == Tone.URGENT:
            return (
                f"{name}, your account has an outstanding balance of ${total_debt:,.2f} that "
                f"requires immediate attention. Please contact us today to resolve this matter "
                f"and avoid additional fees or collection actions."
            )
        else:  # FINAL_NOTICE
            return (
                f"FINAL NOTICE: {name}, your account balance of ${total_debt:,.2f} is seriously "
                f"past due. Immediate payment is required to prevent account closure and potential "
                f"legal action. Contact us immediately to resolve this matter."
            )
    
    def _suggest_payment_amount(self, total_debt: float, largest_debt, 
                               payment_history_score: float, customer) -> Optional[float]:
        """Suggest payment amount"""
        if not largest_debt:
            return None
        
        # Base suggestion on minimum payment or percentage of debt
        if largest_debt.minimum_payment:
            base_amount = largest_debt.minimum_payment
        else:
            base_amount = total_debt * 0.1  # 10% of total debt
        
        # Adjust based on payment history
        if payment_history_score > 70:
            # Good history - suggest higher amount
            suggested = base_amount * 1.5
        elif payment_history_score < 40:
            # Poor history - suggest minimum
            suggested = base_amount * 0.8
        else:
            suggested = base_amount
        
        # Consider income if available
        if customer.annual_income:
            monthly_income = customer.annual_income / 12
            # Don't suggest more than 20% of monthly income
            max_suggested = monthly_income * 0.2
            suggested = min(suggested, max_suggested)
        
        return round(suggested, 2)
    
    def _suggest_payment_plan(self, total_debt: float, customer, 
                              payment_history_score: float) -> Optional[str]:
        """Suggest payment plan"""
        if total_debt < 1000:
            return None
        
        if payment_history_score > 60:
            # Good history - suggest flexible plan
            months = max(3, min(12, int(total_debt / 500)))
            monthly_payment = total_debt / months
            return (
                f"Consider a {months}-month payment plan at ${monthly_payment:,.2f}/month. "
                f"Based on your payment history, you may qualify for reduced interest."
            )
        else:
            # Poor history - suggest structured plan
            months = max(6, min(24, int(total_debt / 300)))
            monthly_payment = total_debt / months
            return (
                f"Consider a structured {months}-month payment plan at ${monthly_payment:,.2f}/month. "
                f"This can help you manage payments more effectively."
            )
    
    def _estimate_payment_probability(self, payment_history_score: float,
                                      communication_responsiveness: float,
                                      urgency_level: UrgencyLevel, customer) -> float:
        """Estimate probability of payment (0-100)"""
        base_probability = (payment_history_score + communication_responsiveness) / 2
        
        # Adjust for urgency (higher urgency = slightly lower probability initially)
        if urgency_level == UrgencyLevel.CRITICAL:
            base_probability *= 0.85
        elif urgency_level == UrgencyLevel.HIGH:
            base_probability *= 0.90
        
        # Adjust for employment
        if customer.employment_status and customer.employment_status.lower() == "employed":
            base_probability *= 1.1
        
        return min(100, max(0, base_probability))
    
    def _generate_reasoning(self, customer, total_debt: float, days_past_due: int,
                            payment_history_score: float, communication_responsiveness: float,
                            urgency_level: UrgencyLevel, channel: CommunicationChannel) -> List[str]:
        """Generate reasoning for the strategy"""
        reasons = []
        
        reasons.append(f"Total debt: ${total_debt:,.2f}")
        reasons.append(f"Days past due: {days_past_due}")
        reasons.append(f"Payment history score: {payment_history_score:.1f}/100")
        reasons.append(f"Communication responsiveness: {communication_responsiveness:.1f}/100")
        
        if urgency_level == UrgencyLevel.CRITICAL:
            reasons.append("CRITICAL: Account requires immediate attention")
        elif urgency_level == UrgencyLevel.HIGH:
            reasons.append("HIGH priority: Account is significantly past due")
        
        if payment_history_score < 50:
            reasons.append("Low payment history score indicates higher risk")
        
        if communication_responsiveness < 40:
            reasons.append("Low communication responsiveness - may need multiple contact attempts")
        
        if customer.employment_status:
            reasons.append(f"Employment status: {customer.employment_status}")
        
        reasons.append(f"Recommended channel: {channel.value} (best for this customer profile)")
        
        return reasons
    
    def generate_strategies_for_all_customers(self, 
                                             min_debt: float = 0.0,
                                             status: Optional[DebtStatus] = None) -> List[ContactStrategy]:
        """Generate strategies for all customers with active debts"""
        session = self.db.get_session()
        try:
            from DB.db_manager import Customer, Debt
            
            query = session.query(Customer).join(Debt)
            if status:
                query = query.filter(Debt.status == status)
            else:
                query = query.filter(Debt.status != DebtStatus.PAID_OFF)
            
            customers = query.distinct().all()
            
            strategies = []
            for customer in customers:
                total_debt = self.db.get_total_debt(customer.id)
                if total_debt >= min_debt:
                    try:
                        strategy = self.analyze_customer(customer.id)
                        strategies.append(strategy)
                    except Exception as e:
                        print(f"Error analyzing customer {customer.id}: {e}")
                        continue
            
            return strategies
        finally:
            session.close()


def print_strategy(strategy: ContactStrategy):
    """Pretty print a contact strategy"""
    print("=" * 80)
    print(f"CONTACT STRATEGY: {strategy.customer_name} (ID: {strategy.customer_id})")
    print("=" * 80)
    
    print(f"\n📊 ANALYSIS:")
    print(f"  Total Debt: ${strategy.total_debt:,.2f}")
    print(f"  Days Past Due: {strategy.days_past_due}")
    print(f"  Risk Score: {strategy.risk_score:.1f}/100")
    print(f"  Payment Probability: {strategy.payment_probability:.1f}%")
    print(f"  Payment History Score: {strategy.payment_history_score:.1f}/100")
    print(f"  Communication Responsiveness: {strategy.communication_responsiveness:.1f}/100")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"  Urgency Level: {strategy.urgency_level.value.upper()}")
    print(f"  Channel: {strategy.recommended_channel.value.upper()}")
    print(f"  Tone: {strategy.tone.value.replace('_', ' ').title()}")
    print(f"  Best Time: {strategy.recommended_contact_time.upper()}")
    if strategy.days_since_last_contact is not None:
        print(f"  Days Since Last Contact: {strategy.days_since_last_contact}")
    
    if strategy.suggested_payment_amount:
        print(f"  Suggested Payment: ${strategy.suggested_payment_amount:,.2f}")
    
    if strategy.payment_plan_suggestion:
        print(f"\n💡 PAYMENT PLAN:")
        print(f"  {strategy.payment_plan_suggestion}")
    
    print(f"\n💬 SUGGESTED MESSAGE:")
    print(f"  {strategy.suggested_message}")
    
    print(f"\n📝 REASONING:")
    for reason in strategy.reasoning:
        print(f"  • {reason}")
    
    print()


if __name__ == "__main__":
    # Example usage
    db = DatabaseManager()
    analyzer = StrategyAnalyzer(db)
    
    # Analyze a specific customer
    # strategy = analyzer.analyze_customer(1)
    # print_strategy(strategy)
    
    # Or generate strategies for all customers with debts
    print("Generating strategies for all customers with active debts...\n")
    strategies = analyzer.generate_strategies_for_all_customers(min_debt=0.0)
    
    # Sort by urgency and risk
    strategies.sort(key=lambda s: (s.urgency_level.value, -s.risk_score), 
                   reverse=True)
    
    for strategy in strategies:
        print_strategy(strategy)
