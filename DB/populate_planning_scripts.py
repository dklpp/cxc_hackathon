#!/usr/bin/env python3
"""
Script to populate simulated planning scripts for all completed calls.
This creates planning scripts for completed calls that don't already have one.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, CommunicationType, DebtStatus,
    CommunicationLog, ScheduledCall, CallPlanningScript
)
from strategy_planning.prompt_template import classify_profile_type


def generate_simulated_planning_script(customer, debts, scheduled_call) -> str:
    """Generate a simulated planning script based on customer data"""
    
    # Get customer info
    customer_name = f"{customer.first_name} {customer.last_name}"
    active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
    total_debt = sum(d.current_balance for d in active_debts)
    max_days_past_due = max((d.days_past_due for d in active_debts), default=0)
    
    # Determine profile type
    customer_tenure_years = int((datetime.now() - customer.created_at).days / 365.25) if customer.created_at else 0
    profile_type = classify_profile_type(
        credit_score=customer.credit_score,
        days_past_due=max_days_past_due,
        employment_status=customer.employment_status,
        customer_tenure_years=customer_tenure_years
    )
    
    # Determine communication channel
    preferred_channel = customer.preferred_communication_method.value if customer.preferred_communication_method else "call"
    
    # Generate suggested time based on call timestamp
    if scheduled_call and scheduled_call.scheduled_time:
        call_time = scheduled_call.scheduled_time
        hour = call_time.hour
        if hour < 12:
            suggested_time = "morning"
        elif hour < 17:
            suggested_time = "afternoon"
        else:
            suggested_time = "evening"
        suggested_day = call_time.strftime("%A")
    else:
        suggested_time = random.choice(["morning", "afternoon", "evening"])
        suggested_day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    
    # Generate script content based on profile type
    if profile_type == 1:
        tone = "professional and supportive"
        approach = "emphasize their good standing and offer flexible payment options"
    elif profile_type == 2:
        tone = "understanding and collaborative"
        approach = "acknowledge their situation and work together on a payment plan"
    elif profile_type == 3:
        tone = "firm but respectful"
        approach = "clearly communicate the urgency while offering assistance programs"
    else:  # profile_type == 4
        tone = "professional and direct"
        approach = "clearly outline consequences while still offering last-chance solutions"
    
    # Build the planning script
    script = f"""# Call Planning Script for {customer_name}

## Customer Profile
- **Name**: {customer_name}
- **Profile Type**: {profile_type}
- **Total Debt**: ${total_debt:,.2f}
- **Days Past Due**: {max_days_past_due} days
- **Credit Score**: {customer.credit_score or 'N/A'}
- **Employment Status**: {customer.employment_status or 'Unknown'}

## Recommended Approach
**Tone**: {tone}
**Strategy**: {approach}

## Best Contact Time
- **Suggested Time**: {suggested_time}
- **Suggested Day**: {suggested_day}
- **Communication Channel**: {preferred_channel}

## Key Talking Points

1. **Opening**
   - Greet the customer warmly and confirm their identity
   - Acknowledge their account status and express willingness to help
   - Set a collaborative tone for the conversation

2. **Main Discussion**
   - Review their current debt situation: ${total_debt:,.2f} across {len(active_debts)} account(s)
   - Discuss payment options:
     * Full payment if possible
     * Payment plan options
     * Hardship programs if eligible
   - Address any concerns or questions they may have

3. **Debt Details**
"""
    
    for debt in active_debts[:3]:  # Show up to 3 debts
        script += f"""
   - **{debt.debt_type}**: ${debt.current_balance:,.2f}
     * Days past due: {debt.days_past_due}
     * Minimum payment: ${debt.minimum_payment:,.2f} if applicable
"""
    
    script += f"""
4. **Closing**
   - Summarize agreed-upon next steps
   - Confirm payment arrangements or follow-up schedule
   - Provide contact information for questions
   - Thank them for their time and cooperation

## Payment Options to Discuss
- **Immediate Payment**: Full balance or partial payment
- **Payment Plan**: Structured monthly payments
- **Hardship Program**: If customer qualifies based on financial situation
- **Settlement**: If appropriate for the account status

## Notes
- Customer's preferred communication method: {preferred_channel}
- Previous interactions may inform approach
- Be prepared to discuss financial assistance programs if needed

## Follow-up Actions
1. Document the call outcome
2. Schedule follow-up if payment plan is established
3. Update account status based on customer response
4. Send confirmation email/letter if payment is arranged

---
*Generated planning script for completed call*
"""
    
    return script


def populate_planning_scripts():
    """Populate planning scripts for all completed calls"""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        # Get all call communication logs
        call_logs = session.query(CommunicationLog).filter(
            CommunicationLog.communication_type == CommunicationType.CALL
        ).all()
        
        print(f"Found {len(call_logs)} completed calls")
        
        scripts_created = 0
        scripts_skipped = 0
        scheduled_calls_created = 0
        
        for call_log in call_logs:
            try:
                # Find linked scheduled call
                scheduled_call = session.query(ScheduledCall).filter(
                    ScheduledCall.communication_log_id == call_log.id
                ).first()
                
                # If no scheduled call linked, create one retroactively
                if not scheduled_call:
                    # Create a scheduled call entry for this completed call
                    scheduled_call = db_manager.create_scheduled_call(
                        customer_id=call_log.customer_id,
                        scheduled_time=call_log.timestamp,
                        status="completed",
                        communication_log_id=call_log.id,
                        agent_id=call_log.agent_id or "system",
                        notes=f"Retroactively created for completed call on {call_log.timestamp.strftime('%Y-%m-%d')}"
                    )
                    scheduled_calls_created += 1
                    print(f"  Created scheduled call entry {scheduled_call.id} for call log {call_log.id}")
                
                # Check if planning script already exists
                existing_script = session.query(CallPlanningScript).filter(
                    CallPlanningScript.scheduled_call_id == scheduled_call.id
                ).first()
                
                if existing_script:
                    print(f"  Skipping call {call_log.id} - planning script already exists (script ID: {existing_script.id})")
                    scripts_skipped += 1
                    continue
                
                # Get customer and debts
                customer = db_manager.get_customer(call_log.customer_id)
                if not customer:
                    print(f"  Warning: Customer {call_log.customer_id} not found for call {call_log.id}")
                    continue
                
                debts = db_manager.get_customer_debts(call_log.customer_id)
                
                # Generate planning script
                script_content = generate_simulated_planning_script(customer, debts, scheduled_call)
                
                # Determine suggested time and day
                if scheduled_call.scheduled_time:
                    call_time = scheduled_call.scheduled_time
                    hour = call_time.hour
                    if hour < 12:
                        suggested_time = "morning"
                    elif hour < 17:
                        suggested_time = "afternoon"
                    else:
                        suggested_time = "evening"
                    suggested_day = call_time.strftime("%A")
                else:
                    suggested_time = "afternoon"
                    suggested_day = "Tuesday"
                
                # Calculate profile type
                active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
                max_days_past_due = max((d.days_past_due for d in active_debts), default=0)
                customer_tenure_years = int((datetime.now() - customer.created_at).days / 365.25) if customer.created_at else 0
                profile_type = classify_profile_type(
                    credit_score=customer.credit_score,
                    days_past_due=max_days_past_due,
                    employment_status=customer.employment_status,
                    customer_tenure_years=customer_tenure_years
                )
                
                # Create planning script
                planning_script = db_manager.create_call_planning_script(
                    customer_id=customer.id,
                    scheduled_call_id=scheduled_call.id,
                    strategy_content=script_content,
                    communication_channel=customer.preferred_communication_method.value if customer.preferred_communication_method else "call",
                    profile_type=profile_type,
                    suggested_time=suggested_time,
                    suggested_day=suggested_day,
                    created_by="system_retroactive"
                )
                
                scripts_created += 1
                print(f"  ✓ Created planning script {planning_script.id} for call {call_log.id} (customer {customer.id}, {customer.first_name} {customer.last_name})")
                
            except Exception as e:
                print(f"  Error processing call {call_log.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n✓ Completed!")
        print(f"  - Scripts created: {scripts_created}")
        print(f"  - Scripts skipped (already exist): {scripts_skipped}")
        print(f"  - Scheduled calls created: {scheduled_calls_created}")
        print(f"  - Total calls processed: {len(call_logs)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("Populating planning scripts for completed calls...")
    print("=" * 60)
    populate_planning_scripts()
