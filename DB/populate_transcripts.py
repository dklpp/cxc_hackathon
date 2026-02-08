#!/usr/bin/env python3
"""
Script to populate simulated call transcripts for all completed calls.
This creates realistic call transcripts based on customer data and call outcomes.
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
    CommunicationLog, ScheduledCall
)
from pathlib import Path


def generate_simulated_transcript(customer, debts, call_log, scheduled_call=None) -> str:
    """Generate a simulated call transcript based on customer data and call outcome"""
    
    customer_name = f"{customer.first_name} {customer.last_name}"
    active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
    total_debt = sum(d.current_balance for d in active_debts)
    
    # Determine call outcome and tone
    outcome = call_log.outcome or "payment_discussed"
    
    # Generate different transcript styles based on outcome
    if "payment" in outcome.lower() or "promised" in outcome.lower():
        transcript_type = "successful"
    elif "refused" in outcome.lower() or "declined" in outcome.lower():
        transcript_type = "refused"
    elif "no_answer" in outcome.lower() or "voicemail" in outcome.lower():
        transcript_type = "no_answer"
    else:
        transcript_type = "neutral"
    
    # Get call duration
    duration = call_log.duration_seconds or random.randint(120, 600)  # 2-10 minutes
    
    # Format timestamp
    call_time = call_log.timestamp.strftime("%B %d, %Y at %I:%M %p")
    
    # Generate transcript based on type
    if transcript_type == "no_answer":
        transcript = f"""# Call Transcript - {customer_name}
**Date**: {call_time}
**Duration**: {duration} seconds
**Outcome**: {outcome}

## Call Summary

**Agent**: Hello, this is [Agent Name] calling from Tangerine Bank regarding your account. Is {customer_name} available?

[No answer - call went to voicemail]

**Voicemail Left**: 
"Hi {customer.first_name}, this is [Agent Name] from Tangerine Bank. I'm calling to discuss your account with us. Please call us back at 1-800-555-0123 at your earliest convenience. Thank you."

---
*End of call*
"""
    
    elif transcript_type == "refused":
        transcript = f"""# Call Transcript - {customer_name}
**Date**: {call_time}
**Duration**: {duration} seconds
**Outcome**: {outcome}

## Call Summary

**Agent**: Hello, this is [Agent Name] calling from Tangerine Bank. May I speak with {customer_name}?

**Customer**: This is {customer.first_name}.

**Agent**: Thank you for taking my call. I'm calling regarding your account with us. I see you have a balance of ${total_debt:,.2f} across {len(active_debts)} account(s). I'd like to discuss payment options with you today.

**Customer**: I'm not really in a position to make a payment right now. Things have been difficult.

**Agent**: I understand, and I want to help. We have several options available, including payment plans and hardship programs that might work for your situation.

**Customer**: I appreciate that, but I really can't commit to anything right now. Can we talk about this another time?

**Agent**: Of course. I understand this is a difficult situation. Would it be helpful if I sent you some information about our payment assistance programs? You can review them when you're ready.

**Customer**: Sure, you can send that.

**Agent**: I'll have that sent to your email on file. Is there a better time to reach you, or would you prefer to call us when you're ready to discuss options?

**Customer**: I'll call when I'm ready. Thanks.

**Agent**: Thank you for your time, {customer.first_name}. Have a good day.

---
*End of call*
"""
    
    elif transcript_type == "successful":
        # Determine payment amount discussed
        if total_debt < 1000:
            payment_amount = total_debt
        else:
            payment_amount = min(total_debt * 0.3, 500)  # 30% or $500, whichever is less
        
        transcript = f"""# Call Transcript - {customer_name}
**Date**: {call_time}
**Duration**: {duration} seconds
**Outcome**: {outcome}

## Call Summary

**Agent**: Hello, this is [Agent Name] calling from Tangerine Bank. May I speak with {customer_name}?

**Customer**: Yes, this is {customer.first_name}.

**Agent**: Thank you for taking my call. I'm calling regarding your account with us. I see you have a balance of ${total_debt:,.2f} across {len(active_debts)} account(s). I'd like to discuss payment options with you today.

**Customer**: Yes, I've been meaning to call about this. I want to get this resolved.

**Agent**: I'm glad to hear that. We have several options available. Would you be able to make a payment today, or would you prefer to set up a payment plan?

**Customer**: I think I can make a payment today. How much are we looking at?

**Agent**: Your total balance is ${total_debt:,.2f}. We can accept any amount you're comfortable with, or we can set up a structured payment plan if that works better for you.

**Customer**: I think I can do ${payment_amount:,.2f} today. Would that help?

**Agent**: Absolutely, that would be a great start. That would bring your balance down to ${total_debt - payment_amount:,.2f}. Would you like to make that payment now, or would you prefer to set up a payment plan for the remaining balance?

**Customer**: Let me make the payment now, and then we can talk about the rest.

**Agent**: Perfect. I can process that payment for you right now. Do you have a credit card or bank account you'd like to use?

**Customer**: Yes, I have my credit card.

**Agent**: Great. [Payment processing details discussed]

**Agent**: Perfect, I've processed your payment of ${payment_amount:,.2f}. You should receive a confirmation email shortly. Now, regarding the remaining balance of ${total_debt - payment_amount:,.2f}, would you like to set up a payment plan?

**Customer**: Yes, that would be helpful. What would that look like?

**Agent**: We can set up monthly payments over the next 6-12 months, depending on what works for your budget. What amount would you be comfortable with each month?

**Customer**: I think I could do ${(total_debt - payment_amount) / 6:,.2f} per month.

**Agent**: That works perfectly. I'll set up a 6-month payment plan for ${(total_debt - payment_amount) / 6:,.2f} per month, starting next month. You'll receive a confirmation email with all the details.

**Customer**: Thank you so much for your help. I really appreciate it.

**Agent**: You're very welcome, {customer.first_name}. Is there anything else I can help you with today?

**Customer**: No, that's everything. Thanks again.

**Agent**: Thank you for your time. Have a wonderful day!

---
*End of call*
"""
    
    else:  # neutral
        transcript = f"""# Call Transcript - {customer_name}
**Date**: {call_time}
**Duration**: {duration} seconds
**Outcome**: {outcome}

## Call Summary

**Agent**: Hello, this is [Agent Name] calling from Tangerine Bank. May I speak with {customer_name}?

**Customer**: Yes, this is {customer.first_name}.

**Agent**: Thank you for taking my call. I'm calling regarding your account with us. I see you have a balance of ${total_debt:,.2f} across {len(active_debts)} account(s). I wanted to reach out to discuss your account status and see how we can help.

**Customer**: Okay, what do you need to know?

**Agent**: I'd like to understand your current situation better. Are you experiencing any financial difficulties that are preventing you from making payments?

**Customer**: Well, things have been tight lately. I'm working on it though.

**Agent**: I understand. We have several assistance programs available that might help. Would you be interested in learning more about payment plans or hardship programs?

**Customer**: Maybe. Can you send me some information?

**Agent**: Absolutely. I'll send you information about our payment assistance options to your email on file. You can review them and let us know what works best for your situation.

**Customer**: That would be helpful. Thank you.

**Agent**: You're welcome. Is there a good time to follow up with you, or would you prefer to call us when you're ready?

**Customer**: I'll call when I'm ready to discuss it further.

**Agent**: Perfect. Thank you for your time today, {customer.first_name}. Have a good day.

---
*End of call*
"""
    
    return transcript


def populate_transcripts():
    """Populate simulated transcripts for all completed calls"""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    # Create transcripts directory if it doesn't exist
    base_dir = Path(__file__).parent.parent
    transcripts_dir = base_dir / "call_files" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get all call communication logs
        call_logs = session.query(CommunicationLog).filter(
            CommunicationLog.communication_type == CommunicationType.CALL
        ).all()
        
        print(f"Found {len(call_logs)} completed calls")
        
        transcripts_created = 0
        transcripts_skipped = 0
        
        for call_log in call_logs:
            try:
                # Check if transcript file already exists
                transcript_file = transcripts_dir / f"call_{call_log.id}_transcript.md"
                if transcript_file.exists():
                    print(f"  Skipping call {call_log.id} - transcript already exists")
                    transcripts_skipped += 1
                    continue
                
                # Get customer and debts
                customer = db_manager.get_customer(call_log.customer_id)
                if not customer:
                    print(f"  Warning: Customer {call_log.customer_id} not found for call {call_log.id}")
                    continue
                
                debts = db_manager.get_customer_debts(call_log.customer_id)
                
                # Find linked scheduled call if exists
                scheduled_call = session.query(ScheduledCall).filter(
                    ScheduledCall.communication_log_id == call_log.id
                ).first()
                
                # Generate transcript
                transcript_content = generate_simulated_transcript(customer, debts, call_log, scheduled_call)
                
                # Save transcript file
                transcript_file.write_text(transcript_content, encoding='utf-8')
                
                transcripts_created += 1
                print(f"  ✓ Created transcript for call {call_log.id} (customer {customer.id}, {customer.first_name} {customer.last_name})")
                
            except Exception as e:
                print(f"  Error processing call {call_log.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n✓ Completed!")
        print(f"  - Transcripts created: {transcripts_created}")
        print(f"  - Transcripts skipped (already exist): {transcripts_skipped}")
        print(f"  - Total calls processed: {len(call_logs)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("Populating simulated call transcripts...")
    print("=" * 60)
    populate_transcripts()
