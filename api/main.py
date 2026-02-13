"""
FastAPI Backend for Customer Debt Management System
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import json
from pathlib import Path
import asyncio
import logging
import time
import requests

# Configure logger for call pipeline
logger = logging.getLogger("call_pipeline")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(_handler)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, Customer, Debt, CommunicationLog, ScheduledCall, CallPlanningScript, PlannedEmail,
    DebtStatus, PaymentStatus, CommunicationType
)
from transcript_analysis.transcript_analyzer import TranscriptAnalyzer
from strategy_planning.strategy_pipeline import GeminiStrategyGenerator
from strategy_planning.prompt_template import classify_profile_type
import re

# Import outbound call manager
try:
    from custom_voice_pipeline.outbound_call import OutboundCallManager
    OUTBOUND_CALL_AVAILABLE = True
except ImportError:
    OUTBOUND_CALL_AVAILABLE = False
    print("Warning: OutboundCallManager not available. AI call functionality will be disabled.")

app = FastAPI(title="Customer Debt Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
db_manager = DatabaseManager()
db_manager.create_tables()
# Run migration for scheduled_calls table if needed
db_manager._migrate_scheduled_calls_if_needed()
# Run migration for customer contact preferences if needed
db_manager._migrate_customer_contact_preferences_if_needed()

# Create directories for storing files
FILES_DIR = Path(__file__).parent.parent / "call_files"
FILES_DIR.mkdir(exist_ok=True, parents=True)
PLANNING_DIR = FILES_DIR / "planning"
TRANSCRIPT_DIR = FILES_DIR / "transcripts"
PLANNING_DIR.mkdir(exist_ok=True, parents=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True, parents=True)

# OpenRouter / Gemini helper for generating call notes
OPENROUTERS_API_KEY = os.getenv("OPENROUTERS_API_KEY")

def generate_notes_from_transcript(transcript_text: str, customer_id: int = None) -> str:
    """Use Gemini via OpenRouter to generate concise call notes from a transcript."""
    ctx = f"customer_id={customer_id}" if customer_id else "unknown_customer"
    transcript_len = len(transcript_text)

    if not OPENROUTERS_API_KEY:
        logger.warning("[gemini-notes] %s — Skipped: OPENROUTERS_API_KEY not configured", ctx)
        return "AI call notes unavailable (no API key configured)."

    logger.info("[gemini-notes] %s — Sending transcript (%d chars) to Gemini for note generation", ctx, transcript_len)
    start = time.time()
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTERS_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-pro",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Analyze the following call transcript and produce a concise summary "
                            "(3-5 sentences). Include: call outcome, customer sentiment, any promises "
                            "or commitments made, and recommended next steps. Be factual and brief.\n\n"
                            f"TRANSCRIPT:\n{transcript_text}"
                        ),
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            },
            timeout=30,
        )
        elapsed = time.time() - start

        if resp.status_code == 200:
            notes = resp.json()["choices"][0]["message"]["content"]
            logger.info("[gemini-notes] %s — Success (%.2fs). Generated %d-char notes", ctx, elapsed, len(notes))
            return notes
        else:
            logger.error("[gemini-notes] %s — OpenRouter returned HTTP %d (%.2fs): %s", ctx, resp.status_code, elapsed, resp.text[:300])
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        logger.error("[gemini-notes] %s — Request timed out after %.2fs", ctx, elapsed)
    except Exception as e:
        elapsed = time.time() - start
        logger.error("[gemini-notes] %s — Exception after %.2fs: %s", ctx, elapsed, e)

    return "AI call notes generation failed."


# Pydantic models for request/response
class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone_primary: str
    phone_secondary: Optional[str]
    city: Optional[str]
    state: Optional[str]
    credit_score: Optional[int]
    account_status: Optional[str]
    preferred_communication_method: Optional[str]
    preferred_contact_time: Optional[str] = None
    preferred_contact_days: Optional[str] = None
    total_debt: Optional[float] = None

class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    debt_type: str
    original_amount: float
    current_balance: float
    interest_rate: Optional[float]
    minimum_payment: Optional[float]
    due_date: Optional[datetime]
    status: str
    days_past_due: int

class CommunicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    communication_type: str
    direction: str
    timestamp: datetime
    outcome: Optional[str]
    notes: Optional[str]
    duration_seconds: Optional[int]

class ScheduledCallRequest(BaseModel):
    customer_id: int
    scheduled_time: Optional[datetime] = None  # Optional - can be auto-selected
    notes: Optional[str] = None
    agent_id: Optional[str] = None
    use_auto_time: bool = False  # If True, use time from strategy
    planning_script_id: Optional[int] = None  # If scheduling a planned call

class PrepareEmailRequest(BaseModel):
    communication_type: str  # "email" or "sms"

class ScheduledCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    scheduled_time: datetime
    status: str
    notes: Optional[str]
    agent_id: Optional[str]
    created_at: datetime
    script_id: Optional[int] = None
    suggested_time: Optional[str] = None
    suggested_day: Optional[str] = None

class TranscriptAnalysisResponse(BaseModel):
    call_metadata: dict
    call_outcome: dict
    customer_info_extracted: dict
    payment_info: dict
    customer_sentiment: dict
    action_items: dict
    compliance_flags: dict
    key_quotes: List[dict]
    conversation_summary: str
    recommendations: dict

# API Routes
@app.get("/")
async def root():
    return {"message": "Customer Debt Management API", "version": "1.0.0"}

@app.get("/api/customers", response_model=List[CustomerResponse])
async def list_customers(search: Optional[str] = None, limit: int = 100, offset: int = 0):
    """List or search customers"""
    try:
        if search:
            customers = db_manager.search_customers(search)
        else:
            customers = db_manager.list_customers(limit=limit, offset=offset)
        
        # Add total_debt to each customer
        result = []
        for customer in customers:
            customer_dict = {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone_primary": customer.phone_primary,
                "phone_secondary": customer.phone_secondary,
                "city": customer.city,
                "state": customer.state,
                "credit_score": customer.credit_score,
                "account_status": customer.account_status,
                "preferred_communication_method": customer.preferred_communication_method.value if customer.preferred_communication_method else None,
                "preferred_contact_time": customer.preferred_contact_time,
                "preferred_contact_days": customer.preferred_contact_days,
                "total_debt": db_manager.get_total_debt(customer.id)
            }
            result.append(customer_dict)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}", response_model=dict)
async def get_customer_detail(customer_id: int):
    """Get detailed customer information with debts and communications"""
    try:
        summary = db_manager.get_customer_summary(customer_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer = summary['customer']
        debts = summary['debts']
        communications = summary['recent_communications']
        scheduled_calls = db_manager.get_scheduled_calls(customer_id=customer_id)
        planned_emails = db_manager.get_planned_emails(customer_id=customer_id)
        
        # Calculate max days past due
        active_debts = [d for d in debts if d.status.value == 'active']
        max_days_past_due = max((d.days_past_due for d in active_debts), default=0)
        
        return {
            "customer": {
                "id": customer.id,
                "first_name": customer.first_name,
                "middle_name": customer.middle_name,
                "last_name": customer.last_name,
                "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                "ssn": f"***-**-{customer.ssn[-4:]}" if customer.ssn else None,  # Masked SSN
                "email": customer.email,
                "phone_primary": customer.phone_primary,
                "phone_secondary": customer.phone_secondary,
                "address_line1": customer.address_line1,
                "address_line2": customer.address_line2,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "country": customer.country,
                "employer_name": customer.employer_name,
                "employment_status": customer.employment_status,
                "annual_income": customer.annual_income,
                "credit_score": customer.credit_score,
                "account_status": customer.account_status,
                "preferred_communication_method": customer.preferred_communication_method.value if customer.preferred_communication_method else None,
                "preferred_contact_time": customer.preferred_contact_time,
                "preferred_contact_days": customer.preferred_contact_days,
                "notes": customer.notes,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
                "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
                "max_days_past_due": max_days_past_due,
            },
            "debts": [
                {
                    "id": d.id,
                    "debt_type": d.debt_type,
                    "original_amount": d.original_amount,
                    "current_balance": d.current_balance,
                    "interest_rate": d.interest_rate,
                    "minimum_payment": d.minimum_payment,
                    "due_date": d.due_date.isoformat() if d.due_date else None,
                    "status": d.status.value,
                    "days_past_due": d.days_past_due,
                    "account_number": d.account_number,
                }
                for d in debts
            ],
            "total_debt": summary['total_debt'],
            "communications": [
                {
                    "id": c.id,
                    "communication_type": c.communication_type.value,
                    "direction": c.direction,
                    "timestamp": c.timestamp.isoformat(),
                    "outcome": c.outcome,
                    "notes": c.notes,
                    "duration_seconds": c.duration_seconds,
                }
                for c in communications
            ],
            "scheduled_calls": [
                {
                    "id": sc.id,
                    "scheduled_time": sc.scheduled_time.isoformat() if sc.scheduled_time else None,
                    "status": sc.status,
                    "notes": sc.notes,
                    "agent_id": sc.agent_id,
                    "created_at": sc.created_at.isoformat(),
                    "planning_file_path": f"call_files/planning/call_{sc.id}_planning.md" if db_manager.get_call_planning_scripts(customer_id, sc.id) else None,
                    "planning_script": next(iter([
                        {
                            "id": s.id,
                            "strategy_content": s.strategy_content,
                            "suggested_time": s.suggested_time,
                            "suggested_day": s.suggested_day,
                            "communication_channel": s.communication_channel,
                            "created_at": s.created_at.isoformat(),
                        }
                        for s in db_manager.get_call_planning_scripts(customer_id, sc.id)
                    ]), None),
                }
                for sc in scheduled_calls
            ],
            "planned_emails": [
                {
                    "id": pe.id,
                    "communication_type": pe.communication_type.value,
                    "subject": pe.subject,
                    "content": pe.content,
                    "status": pe.status,
                    "scheduled_send_time": pe.scheduled_send_time.isoformat() if pe.scheduled_send_time else None,
                    "sent_at": pe.sent_at.isoformat() if pe.sent_at else None,
                    "created_at": pe.created_at.isoformat(),
                    "planning_script_id": pe.planning_script_id,
                }
                for pe in planned_emails
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/debts", response_model=List[DebtResponse])
async def get_customer_debts(customer_id: int):
    """Get all debts for a customer"""
    try:
        debts = db_manager.get_customer_debts(customer_id)
        return [
            {
                "id": d.id,
                "customer_id": d.customer_id,
                "debt_type": d.debt_type,
                "original_amount": d.original_amount,
                "current_balance": d.current_balance,
                "interest_rate": d.interest_rate,
                "minimum_payment": d.minimum_payment,
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "status": d.status.value,
                "days_past_due": d.days_past_due,
            }
            for d in debts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_suggested_time_from_strategy(strategy_text: str) -> tuple:
    """Extract suggested time and day from strategy text"""
    suggested_time = None
    suggested_day = None
    
    # Try to extract time suggestions from the text
    time_patterns = [
        r'best[_\s]contact[_\s]time["\']?\s*[:=]\s*["\']?([^"\']+)',
        r'suggested[_\s]time["\']?\s*[:=]\s*["\']?([^"\']+)',
        r'contact[_\s]time["\']?\s*[:=]\s*["\']?([^"\']+)',
    ]
    
    day_patterns = [
        r'best[_\s]contact[_\s]day["\']?\s*[:=]\s*["\']?([^"\']+)',
        r'suggested[_\s]day["\']?\s*[:=]\s*["\']?([^"\']+)',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, strategy_text, re.IGNORECASE)
        if match:
            suggested_time = match.group(1).strip().strip('"\'')
            break
    
    for pattern in day_patterns:
        match = re.search(pattern, strategy_text, re.IGNORECASE)
        if match:
            suggested_day = match.group(1).strip().strip('"\'')
            break
    
    return suggested_time, suggested_day

def parse_time_from_strategy(suggested_time: str, suggested_day: str) -> Optional[datetime]:
    """Parse suggested time and day into a datetime object"""
    if not suggested_time:
        return None
    
    # Simple parsing - in production, use more robust date parsing
    # For now, default to tomorrow at a reasonable time based on suggested_time
    now = datetime.utcnow()
    
    # Map time strings to hours
    time_mapping = {
        'morning': 9,
        'afternoon': 14,
        'evening': 17,
        'night': 20,
    }
    
    hour = time_mapping.get(suggested_time.lower(), 14)  # Default to 2 PM
    
    # If day is specified, try to find next occurrence
    # For simplicity, use tomorrow
    scheduled = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    return scheduled

def generate_time_slots(customer: Customer, num_slots: int = 3) -> List[dict]:
    """Generate best time slots for contacting a customer based on their explicit preferences in the database"""
    now = datetime.utcnow()
    slots = []
    
    # Get preferred contact time and days from database (handle AttributeError if columns don't exist)
    try:
        preferred_time = customer.preferred_contact_time or ""
    except AttributeError:
        preferred_time = ""
    
    try:
        preferred_days = customer.preferred_contact_days or ""
    except AttributeError:
        preferred_days = ""
    
    # Default to business hours (9 AM - 5 PM) and weekdays if no preferences are set
    default_start_hour = 9
    default_end_hour = 17
    use_weekdays_only = True
    
    # Parse preferred_contact_time from database - this is the primary source
    if preferred_time:
        preferred_time_lower = preferred_time.lower().strip()
        
        # Try to extract time range first (e.g., "9 AM - 5 PM", "10am-2pm", "9:00 AM - 5:00 PM")
        time_range_match = re.search(r'(\d{1,2})\s*(?:AM|PM|am|pm|:00)?\s*[-–]\s*(\d{1,2})\s*(?:AM|PM|am|pm|:00)?', preferred_time)
        if time_range_match:
            start_hour = int(time_range_match.group(1))
            end_hour = int(time_range_match.group(2))
            # Convert to 24-hour format if needed
            # Check if PM appears anywhere in the string
            has_pm = "pm" in preferred_time_lower or "PM" in preferred_time
            has_am = "am" in preferred_time_lower or "AM" in preferred_time
            
            # Determine if hours are AM or PM
            if has_pm and not has_am:
                # Both are PM
                if start_hour < 12:
                    start_hour += 12
                if end_hour < 12:
                    end_hour += 12
            elif has_am and not has_pm:
                # Both are AM
                if start_hour == 12:
                    start_hour = 0
                if end_hour == 12:
                    end_hour = 0
            elif has_pm and has_am:
                # Mixed - need to check which is which
                # Simple heuristic: if first number is <= 7, likely PM; if >= 8, likely AM
                if start_hour <= 7:
                    start_hour += 12
                if end_hour <= 7 and end_hour < start_hour:
                    end_hour += 12
            
            default_start_hour = max(8, min(start_hour, 20))  # Clamp between 8 AM and 8 PM
            default_end_hour = max(9, min(end_hour, 20))  # Clamp between 9 AM and 8 PM
            
            # Ensure start < end
            if default_start_hour >= default_end_hour:
                default_end_hour = min(default_start_hour + 4, 20)
        elif "morning" in preferred_time_lower:
            default_start_hour = 9
            default_end_hour = 12
        elif "afternoon" in preferred_time_lower:
            default_start_hour = 13
            default_end_hour = 17
        elif "evening" in preferred_time_lower:
            default_start_hour = 17
            default_end_hour = 20
        elif "night" in preferred_time_lower:
            default_start_hour = 18
            default_end_hour = 21
        else:
            # Try to find single hour mentioned
            hour_match = re.search(r'\b(\d{1,2})\s*(?:AM|PM|am|pm)\b', preferred_time)
            if hour_match:
                hour = int(hour_match.group(1))
                if "pm" in preferred_time_lower or "PM" in preferred_time:
                    if hour < 12:
                        hour += 12
                elif hour == 12:
                    hour = 12  # Noon
                default_start_hour = max(8, hour - 1)
                default_end_hour = min(20, hour + 1)
    
    # Parse preferred_contact_days from database - this is the primary source
    if preferred_days:
        preferred_days_lower = preferred_days.lower().strip()
        if "weekend" in preferred_days_lower or "saturday" in preferred_days_lower or "sunday" in preferred_days_lower:
            use_weekdays_only = False
        elif "any" in preferred_days_lower or "all" in preferred_days_lower or "every" in preferred_days_lower:
            use_weekdays_only = False
        elif "weekday" in preferred_days_lower or "monday" in preferred_days_lower or "tuesday" in preferred_days_lower or "wednesday" in preferred_days_lower or "thursday" in preferred_days_lower or "friday" in preferred_days_lower:
            use_weekdays_only = True
    
    # Generate slots starting from tomorrow based on customer's preferences
    days_ahead = 1
    slots_generated = 0
    
    # Generate time slots within the customer's preferred time range
    while slots_generated < num_slots and days_ahead <= 14:  # Look up to 2 weeks ahead
        candidate_date = now + timedelta(days=days_ahead)
        weekday = candidate_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Skip if weekdays only and it's a weekend (based on customer preference)
        if use_weekdays_only and weekday >= 5:
            days_ahead += 1
            continue
        
        # Generate varied hours within the customer's preferred time range
        hours_to_try = []
        hour_range = default_end_hour - default_start_hour
        
        if hour_range > 0:
            # Distribute slots across the preferred range
            if slots_generated < num_slots:
                hours_to_try.append(default_start_hour)
            if slots_generated + 1 < num_slots:
                # Add middle hour
                mid_hour = default_start_hour + (hour_range // 2)
                hours_to_try.append(mid_hour)
            if slots_generated + 2 < num_slots:
                # Add end hour (but not too late)
                end_hour = min(default_end_hour - 1, 20)  # Don't go past 8 PM
                if end_hour > default_start_hour:
                    hours_to_try.append(end_hour)
        else:
            # If range is small, use the start hour and add small variations
            hours_to_try.append(default_start_hour)
            if slots_generated + 1 < num_slots and default_start_hour < 20:
                hours_to_try.append(default_start_hour + 1)
            if slots_generated + 2 < num_slots and default_start_hour < 19:
                hours_to_try.append(default_start_hour + 2)
        
        # Remove duplicates and sort
        hours_to_try = sorted(list(set(hours_to_try)))
        
        for hour in hours_to_try[:num_slots - slots_generated]:
            # Ensure hour is valid (between 8 AM and 8 PM)
            if hour < 8 or hour > 20:
                continue
                
            # Create time slot (10-minute window)
            slot_start = candidate_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(minutes=10)
            
            # Format day name
            day_name = candidate_date.strftime("%A")
            
            slots.append({
                "start_time": slot_start.isoformat(),
                "end_time": slot_end.isoformat(),
                "display": slot_start.strftime("%A, %B %d at %I:%M %p"),
                "day_name": day_name,
            })
            slots_generated += 1
            
            if slots_generated >= num_slots:
                break
        
        days_ahead += 1
    
    # If we didn't generate enough slots, fill with defaults based on preferences
    while len(slots) < num_slots:
        fallback_date = now + timedelta(days=len(slots) + 1)
        if use_weekdays_only and fallback_date.weekday() >= 5:
            fallback_date += timedelta(days=1)
        
        slot_start = fallback_date.replace(hour=default_start_hour, minute=0, second=0, microsecond=0)
        slot_end = slot_start + timedelta(minutes=10)
        
        slots.append({
            "start_time": slot_start.isoformat(),
            "end_time": slot_end.isoformat(),
            "display": slot_start.strftime("%A, %B %d at %I:%M %p"),
            "day_name": slot_start.strftime("%A"),
        })
    
    return slots[:num_slots]  # Ensure we return exactly num_slots

def save_planning_file(call_id: int, content: str) -> str:
    """Save planning script as MD file"""
    file_path = PLANNING_DIR / f"call_{call_id}_planning.md"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path.relative_to(FILES_DIR.parent))

def save_transcript_file(call_id: int, content: str) -> str:
    """Save transcript as MD file"""
    file_path = TRANSCRIPT_DIR / f"call_{call_id}_transcript.md"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path.relative_to(FILES_DIR.parent))

def get_file_content(relative_path: str) -> Optional[str]:
    """Get file content by relative path"""
    file_path = FILES_DIR.parent / relative_path
    if file_path.exists():
        return file_path.read_text(encoding='utf-8')
    return None

def generate_planning_script_background(customer_id: int, planned_call_id: int):
    """Background task to generate planning script"""
    try:
        # Generate strategy
        generator = GeminiStrategyGenerator(db=db_manager)
        strategy = generator.generate_strategy(customer_id)
        
        # Save planning script linked to planned call
        script = db_manager.create_call_planning_script(
            customer_id=customer_id,
            scheduled_call_id=planned_call_id,
            strategy_content=strategy.message_content or "",
            communication_channel=strategy.communication_channel or None,
            profile_type=strategy.profile_type,
            suggested_time=strategy.best_contact_time,
            suggested_day=strategy.best_contact_day,
            created_by="current_user"
        )
        
        # Save planning file
        try:
            file_path = save_planning_file(planned_call_id, strategy.message_content or "")
        except Exception as e:
            print(f"Warning: Failed to save planning file: {e}")
        
        # Update scheduled call status to indicate planning is complete
        db_manager.update_scheduled_call(
            planned_call_id,
            notes="Planned call - planning script generated"
        )
        
        print(f"✓ Planning script generated for call {planned_call_id}")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating planning script in background: {error_details}")
        # Update call with error status
        try:
            db_manager.update_scheduled_call(
                planned_call_id,
                notes=f"Error generating planning script: {str(e)}"
            )
        except:
            pass

@app.post("/api/customers/{customer_id}/prepare-call")
async def prepare_call(customer_id: int, background_tasks: BackgroundTasks):
    """Generate call preparation script and create planned call entry (async)"""
    try:
        # Create planned call immediately (no scheduled_time)
        try:
            planned_call = db_manager.create_scheduled_call(
                customer_id=customer_id,
                scheduled_time=None,  # No time set yet
                notes="Planned call - generating planning script...",
                agent_id="current_user",
                status="planned"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create planned call: {str(e)}"
            )
        
        # Add background task to generate strategy
        background_tasks.add_task(
            generate_planning_script_background,
            customer_id,
            planned_call.id
        )
        
        # Return immediately with call ID
        return {
            "success": True,
            "call_id": planned_call.id,
            "status": "processing",
            "message": "Planning script generation started. It will be available shortly.",
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Unexpected error in prepare_call: {error_details}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def generate_scheduling_strategy_background(customer_id: int, scheduled_call_id: int, use_auto_time: bool):
    """Background task to generate strategy for scheduled call"""
    try:
        # Generate strategy
        generator = GeminiStrategyGenerator(db=db_manager)
        strategy = generator.generate_strategy(customer_id)
        
        # Extract suggested time from strategy
        suggested_time, suggested_day = extract_suggested_time_from_strategy(
            strategy.message_content or ""
        )
        
        # If use_auto_time, update scheduled time
        if use_auto_time:
            parsed_time = parse_time_from_strategy(suggested_time or "", suggested_day or "")
            if parsed_time:
                db_manager.update_scheduled_call(
                    scheduled_call_id,
                    scheduled_time=parsed_time
                )
        
        # Save planning script linked to scheduled call
        script = db_manager.create_call_planning_script(
            customer_id=customer_id,
            scheduled_call_id=scheduled_call_id,
            strategy_content=strategy.message_content or "",
            communication_channel=strategy.communication_channel,
            profile_type=strategy.profile_type,
            suggested_time=suggested_time or strategy.best_contact_time,
            suggested_day=suggested_day or strategy.best_contact_day,
            created_by="current_user"
        )
        
        # Save planning file as MD
        try:
            file_path = save_planning_file(scheduled_call_id, strategy.message_content or "")
        except Exception as e:
            print(f"Warning: Failed to save planning file: {e}")
        
        print(f"✓ Strategy generated for scheduled call {scheduled_call_id}")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating strategy in background: {error_details}")
        try:
            db_manager.update_scheduled_call(
                scheduled_call_id,
                notes=f"Error generating strategy: {str(e)}"
            )
        except:
            pass

@app.get("/api/customers/{customer_id}/suggested-time-slots")
async def get_suggested_time_slots(customer_id: int):
    """Get 3 best time slots for scheduling a call with this customer"""
    try:
        summary = db_manager.get_customer_summary(customer_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer = summary['customer']
        
        # Ensure migration has run - try to access the new fields
        try:
            # Access the fields to trigger any AttributeError if columns don't exist
            _ = customer.preferred_contact_time
            _ = customer.preferred_contact_days
        except AttributeError:
            # Columns don't exist yet, run migration
            db_manager._migrate_customer_contact_preferences_if_needed()
            # Refresh the customer object
            session = db_manager.get_session()
            try:
                session.refresh(customer)
            finally:
                session.close()
        
        slots = generate_time_slots(customer, num_slots=3)
        
        return {
            "slots": slots,
            "customer_preferences": {
                "preferred_contact_time": getattr(customer, 'preferred_contact_time', None),
                "preferred_contact_days": getattr(customer, 'preferred_contact_days', None),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_suggested_time_slots: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating time slots: {str(e)}")

@app.post("/api/scheduled-calls", response_model=ScheduledCallResponse)
async def create_scheduled_call(call: ScheduledCallRequest, background_tasks: BackgroundTasks):
    """Schedule a call for a customer, then run strategy planning (async)"""
    try:
        scheduled_time = call.scheduled_time
        
        # If scheduling a planned call, get planning script first
        planning_script = None
        if call.planning_script_id:
            planning_script = db_manager.get_call_planning_script(call.planning_script_id)
            if not planning_script:
                raise HTTPException(status_code=404, detail="Planning script not found")
            
            # If no time provided and use_auto_time, parse from planning script
            if not scheduled_time and call.use_auto_time:
                scheduled_time = parse_time_from_strategy(
                    planning_script.suggested_time or "",
                    planning_script.suggested_day or ""
                )
                if not scheduled_time:
                    scheduled_time = datetime.utcnow() + timedelta(days=1, hours=14)  # Default to tomorrow 2 PM
        
        # If use_auto_time but no planning script, we'll generate strategy in background
        if not scheduled_time and call.use_auto_time and not call.planning_script_id:
            # Will be set after strategy generation
            scheduled_time = datetime.utcnow() + timedelta(days=1, hours=14)  # Temporary default
        elif not scheduled_time:
            raise HTTPException(status_code=400, detail="scheduled_time is required unless use_auto_time is True")
        
        # Create scheduled call first
        scheduled_call = db_manager.create_scheduled_call(
            customer_id=call.customer_id,
            scheduled_time=scheduled_time,
            notes=call.notes or "Generating strategy...",
            agent_id=call.agent_id,
            status="pending"
        )
        
        # Always generate strategy asynchronously after scheduling
        background_tasks.add_task(
            generate_scheduling_strategy_background,
            call.customer_id,
            scheduled_call.id,
            call.use_auto_time
        )
        
        return {
            "id": scheduled_call.id,
            "customer_id": scheduled_call.customer_id,
            "scheduled_time": scheduled_call.scheduled_time.isoformat() if scheduled_call.scheduled_time else None,
            "status": scheduled_call.status,
            "notes": scheduled_call.notes,
            "agent_id": scheduled_call.agent_id,
            "created_at": scheduled_call.created_at.isoformat(),
            "script_id": planning_script.id if planning_script else None,
            "suggested_time": planning_script.suggested_time if planning_script else None,
            "suggested_day": planning_script.suggested_day if planning_script else None,
            "planning_file_path": f"call_files/planning/call_{scheduled_call.id}_planning.md" if planning_script else None,
            "status_message": "Call scheduled. Strategy generation started. Planning file will be available shortly.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scheduled-calls/{call_id}")
async def cancel_scheduled_call(call_id: int):
    """Cancel a scheduled call"""
    try:
        scheduled_call = db_manager.update_scheduled_call(call_id, status="cancelled")
        if not scheduled_call:
            raise HTTPException(status_code=404, detail="Scheduled call not found")
        return {
            "success": True,
            "message": "Call cancelled successfully",
            "call": {
                "id": scheduled_call.id,
                "status": scheduled_call.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/call-planning-scripts")
async def get_call_planning_scripts(customer_id: int, scheduled_call_id: Optional[int] = None):
    """Get call planning scripts for a customer"""
    try:
        scripts = db_manager.get_call_planning_scripts(customer_id, scheduled_call_id)
        return [
            {
                "id": s.id,
                "customer_id": s.customer_id,
                "scheduled_call_id": s.scheduled_call_id,
                "strategy_content": s.strategy_content,
                "suggested_time": s.suggested_time,
                "suggested_day": s.suggested_day,
                "communication_channel": s.communication_channel,
                "profile_type": s.profile_type,
                "created_at": s.created_at.isoformat(),
                "created_by": s.created_by,
            }
            for s in scripts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/call-planning-scripts/{script_id}")
async def get_call_planning_script(script_id: int):
    """Get a specific call planning script"""
    try:
        script = db_manager.get_call_planning_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Call planning script not found")
        return {
            "id": script.id,
            "customer_id": script.customer_id,
            "scheduled_call_id": script.scheduled_call_id,
            "strategy_content": script.strategy_content,
            "suggested_time": script.suggested_time,
            "suggested_day": script.suggested_day,
            "communication_channel": script.communication_channel,
            "profile_type": script.profile_type,
            "created_at": script.created_at.isoformat(),
            "created_by": script.created_by,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/call-history")
async def get_call_history(customer_id: int):
    """Get interaction history for a customer (includes calls, emails, SMS)"""
    session = db_manager.get_session()
    try:
        # Get communication logs (all types)
        communications = db_manager.get_communication_logs(customer_id, limit=100)
        calls = [c for c in communications if c.communication_type == CommunicationType.CALL]
        emails_sms = [c for c in communications if c.communication_type in [CommunicationType.EMAIL, CommunicationType.SMS]]
        
        # Get scheduled calls (including planned)
        scheduled_calls = db_manager.get_scheduled_calls(customer_id=customer_id)
        
        # Get planned emails
        planned_emails = db_manager.get_planned_emails(customer_id=customer_id)
        
        # Separate calls into planned, scheduled (automatic), and completed
        planned_calls = []
        automatic_calls = []
        completed_calls = []
        
        # Separate emails into planned and sent
        planned_emails_list = []
        sent_emails_list = []
        
        # Process scheduled calls
        for sc in scheduled_calls:
            # Get planning script if exists
            scripts = db_manager.get_call_planning_scripts(customer_id, sc.id)
            planning_file_path = None
            planning_script = None
            if scripts:
                planning_file_path = f"call_files/planning/call_{sc.id}_planning.md"
                planning_script = {
                    "id": scripts[0].id,
                    "strategy_content": scripts[0].strategy_content,
                    "suggested_time": scripts[0].suggested_time,
                    "suggested_day": scripts[0].suggested_day,
                    "communication_channel": scripts[0].communication_channel,
                    "created_at": scripts[0].created_at.isoformat(),
                }
            
            call_data = {
                "id": f"scheduled_{sc.id}",
                "type": "scheduled",
                "customer_id": sc.customer_id,
                "communication_type": "call",
                "direction": "outbound",
                "timestamp": sc.scheduled_time.isoformat() if sc.scheduled_time else sc.created_at.isoformat(),
                "scheduled_time": sc.scheduled_time.isoformat() if sc.scheduled_time else None,
                "status": sc.status,
                "outcome": None,
                "notes": sc.notes,
                "duration_seconds": None,
                "planning_file_path": planning_file_path,
                "planning_script": planning_script,
                "scheduled_call_id": sc.id,
                "transcript_file_path": None,
            }
            
            if sc.status == "planned":
                planned_calls.append(call_data)
            elif sc.status == "pending":
                automatic_calls.append(call_data)
            elif sc.status == "completed":
                # For completed scheduled calls, check if transcript exists in DB
                if sc.communication_log_id:
                    # Get communication log to check for transcript
                    comm_log = db_manager.get_session().query(CommunicationLog).filter(
                        CommunicationLog.id == sc.communication_log_id
                    ).first()
                    if comm_log and comm_log.transcript:
                        call_data["has_transcript"] = True
                    else:
                        call_data["has_transcript"] = False
                    db_manager.get_session().close()
                else:
                    call_data["has_transcript"] = False
                # For completed scheduled calls, include transcript file path if communication log exists
                if sc.communication_log_id:
                    call_data["transcript_file_path"] = f"call_files/transcripts/call_{sc.communication_log_id}_transcript.md"
                completed_calls.append(call_data)
        
        # Track which communication logs are already represented by scheduled calls
        communication_logs_represented = set()
        for sc in scheduled_calls:
            if sc.communication_log_id:
                communication_logs_represented.add(sc.communication_log_id)
        
        # Add actual communication logs (completed calls) that aren't already represented
        for c in calls:
            # Skip if this communication log is already represented by a scheduled call
            if c.id in communication_logs_represented:
                continue
            
            # Check if transcript exists in database
            has_transcript = bool(c.transcript)
            transcript_file_path = f"call_files/transcripts/call_{c.id}_transcript.md"
            
            completed_calls.append({
                "id": c.id,
                "type": "completed",
                "customer_id": c.customer_id,
                "communication_type": c.communication_type.value,
                "direction": c.direction,
                "timestamp": c.timestamp.isoformat(),
                "scheduled_time": None,
                "status": "completed",
                "outcome": c.outcome,
                "notes": c.notes,
                "duration_seconds": c.duration_seconds,
                "planning_file_path": None,
                "planning_script": None,
                "has_transcript": has_transcript,
                "transcript_file_path": transcript_file_path,
                "scheduled_call_id": None,
            })
        
        # Process planned emails
        for pe in planned_emails:
            # Get planning script if exists
            planning_script = None
            planning_file_path = None
            if pe.planning_script_id:
                script = db_manager.get_call_planning_script(pe.planning_script_id)
                if script:
                    planning_file_path = f"call_files/planning/email_{pe.id}_planning.md"
                    planning_script = {
                        "id": script.id,
                        "strategy_content": script.strategy_content,
                        "suggested_time": script.suggested_time,
                        "suggested_day": script.suggested_day,
                        "communication_channel": script.communication_channel,
                        "created_at": script.created_at.isoformat(),
                    }
            
            email_data = {
                "id": f"email_{pe.id}",
                "type": "email",
                "customer_id": pe.customer_id,
                "communication_type": pe.communication_type.value,
                "direction": "outbound",
                "timestamp": (pe.scheduled_send_time.isoformat() if pe.scheduled_send_time 
                            else (pe.created_at.isoformat() if pe.created_at else datetime.utcnow().isoformat())),
                "scheduled_time": pe.scheduled_send_time.isoformat() if pe.scheduled_send_time else None,
                "status": pe.status,
                "subject": pe.subject,
                "content": pe.content or "",
                "notes": pe.notes,
                "planning_file_path": planning_file_path,
                "planning_script": planning_script,
                "sent_at": pe.sent_at.isoformat() if pe.sent_at else None,
            }
            
            if pe.status == "planned":
                planned_emails_list.append(email_data)
            elif pe.status == "sent":
                sent_emails_list.append(email_data)
        
        # Add sent emails from communication logs that aren't already represented
        email_logs_represented = set()
        for pe in planned_emails:
            if pe.communication_log_id:
                email_logs_represented.add(pe.communication_log_id)
        
        for comm in emails_sms:
            if comm.id in email_logs_represented:
                continue
            
            sent_emails_list.append({
                "id": comm.id,
                "type": "completed",
                "customer_id": comm.customer_id,
                "communication_type": comm.communication_type.value,
                "direction": comm.direction,
                "timestamp": comm.timestamp.isoformat(),
                "scheduled_time": None,
                "status": "completed",
                "subject": None,
                "content": comm.notes,  # Use notes as content for sent emails
                "outcome": comm.outcome,
                "notes": comm.notes,
                "planning_file_path": None,
                "planning_script": None,
                "sent_at": comm.timestamp.isoformat(),
            })
        
        # Sort each list by timestamp (most recent first)
        planned_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        automatic_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        completed_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        planned_emails_list.sort(key=lambda x: x['timestamp'], reverse=True)
        sent_emails_list.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "planned": planned_calls + planned_emails_list,
            "automatic": automatic_calls,
            "completed": completed_calls + sent_emails_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_call_history: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error fetching call history: {str(e)}")
    finally:
        session.close()

@app.get("/api/call-history/{call_id}/planning-file")
async def get_planning_file(call_id: str):
    """Get planning file content for a call"""
    try:
        # Extract scheduled call ID from format "scheduled_{id}" or just use as-is
        if call_id.startswith("scheduled_"):
            scheduled_call_id = int(call_id.replace("scheduled_", ""))
        else:
            scheduled_call_id = int(call_id)
        
        file_path = f"call_files/planning/call_{scheduled_call_id}_planning.md"
        content = get_file_content(file_path)
        
        if not content:
            raise HTTPException(status_code=404, detail="Planning file not found")
        
        return {
            "content": content,
            "file_path": file_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/call-history/{call_id}/transcript-file")
async def get_transcript_file(call_id: str):
    """Get transcript content for a call from database"""
    try:
        session = db_manager.get_session()
        
        # Handle both numeric IDs and "scheduled_{id}" format
        if call_id.startswith("scheduled_"):
            scheduled_call_id = int(call_id.replace("scheduled_", ""))
            # Get the scheduled call to find its communication_log_id
            scheduled_call = session.query(ScheduledCall).filter(
                ScheduledCall.id == scheduled_call_id
            ).first()
            
            if not scheduled_call or not scheduled_call.communication_log_id:
                session.close()
                raise HTTPException(status_code=404, detail="Scheduled call or communication log not found")
            
            comm_id = scheduled_call.communication_log_id
        else:
            comm_id = int(call_id)
        
        # Get communication log with transcript
        comm_log = session.query(CommunicationLog).filter(
            CommunicationLog.id == comm_id
        ).first()
        
        session.close()
        
        if not comm_log:
            raise HTTPException(status_code=404, detail="Communication log not found")
        
        if not comm_log.transcript:
            raise HTTPException(status_code=404, detail="Transcript not found in database")
        
        return {
            "content": comm_log.transcript,
            "communication_id": comm_log.id,
        }
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid call ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_email_content_background(customer_id: int, planned_email_id: int, communication_type: str):
    """Background task to generate email/SMS content using email master prompt"""
    try:
        # Generate strategy with forced email channel to use email master prompt
        generator = GeminiStrategyGenerator(db=db_manager)
        
        # Get customer summary
        summary = generator.db.get_customer_summary(customer_id)
        if not summary:
            raise ValueError(f"Customer {customer_id} not found")
        
        customer = summary['customer']
        debts = summary['debts']
        payments = summary['payments']
        communications = summary['recent_communications']
        
        # Force email channel for email generation
        active_debts = [d for d in debts if d.status == DebtStatus.ACTIVE]
        total_debt = sum(d.current_balance for d in active_debts)
        max_days_past_due = max((d.days_past_due for d in active_debts), default=0)
        primary_debt = active_debts[0] if active_debts else None
        
        completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        total_paid = sum(p.amount for p in completed_payments)
        
        # Calculate profile type for the prompt template
        customer_tenure_years = (
            int((datetime.now() - customer.created_at).days / 365.25)
            if customer.created_at else 0
        )
        # Import classify_profile_type directly to ensure it's available
        from strategy_planning.prompt_template import classify_profile_type
        profile_type = classify_profile_type(
            credit_score=customer.credit_score,
            days_past_due=max_days_past_due,
            employment_status=customer.employment_status,
            customer_tenure_years=customer_tenure_years
        )
        
        debt_details = []
        for debt in active_debts:
            interest_rate_str = f"{debt.interest_rate}%" if debt.interest_rate else "N/A"
            debt_details.append(
                f"- {debt.debt_type}: ${debt.current_balance:,.2f} "
                f"(Original: ${debt.original_amount:,.2f}, "
                f"Days Past Due: {debt.days_past_due}, "
                f"Interest Rate: {interest_rate_str})"
            )
        
        recent_payments = [
            f'${p.amount:.2f} on {p.payment_date.strftime("%Y-%m-%d")}' 
            for p in completed_payments[-3:]
        ]
        
        comm_history = [
            f"- {comm.communication_type.value} ({comm.direction}) on {comm.timestamp.strftime('%Y-%m-%d')}: "
            f"{comm.outcome or 'no outcome recorded'}"
            for comm in communications[:5]
        ]
        
        age = generator._calculate_age(customer.date_of_birth) if customer.date_of_birth else None
        address_parts = [p for p in [customer.address_line1, customer.address_line2] if p]
        address = ", ".join(address_parts) if address_parts else None
        
        last_payment_date_str = None
        if completed_payments:
            last_payment = max(completed_payments, key=lambda p: p.payment_date)
            last_payment_date_str = last_payment.payment_date.strftime("%Y-%m-%d")
        
        due_date_str = None
        if primary_debt and primary_debt.due_date:
            due_date_str = primary_debt.due_date.strftime("%Y-%m-%d")
        
        customer_data = generator._prepare_customer_data_dict(
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
        
        # Add profile type and risk level to customer data for the template
        customer_data["PROFILE_TYPE"] = str(profile_type)
        # Determine risk level based on profile type
        if profile_type in [1, 2]:
            risk_level = "low"
        elif profile_type == 3:
            risk_level = "moderate"
        elif profile_type == 4:
            risk_level = "high"
        else:
            risk_level = "vip"
        customer_data["RISK_LEVEL"] = risk_level
        
        # Force use of email prompt regardless of customer preference
        from strategy_planning.prompt_template import build_email_prompt
        prompt = build_email_prompt(customer_data)
        
        headers = {
            "Authorization": f"Bearer {generator.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/dklpp/cxc_hackathon",
        }
        
        payload = {
            "model": generator.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        response = requests.post(generator.api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        if 'choices' not in result or not result['choices']:
            raise ValueError(f"Unexpected API response format: {result}")
        
        strategy_text = result['choices'][0]['message']['content']
        
        # Extract email/SMS content from strategy
        if communication_type == "email":
            # Try to parse as JSON first
            subject = "Payment Reminder"  # Default subject
            content = strategy_text  # Default to full text
            
            try:
                # Try to parse JSON from the response
                # Look for JSON code blocks or raw JSON
                json_text = strategy_text.strip()
                
                # Remove markdown code blocks if present
                # Handle ```json (triple backticks) first
                if '```json' in json_text.lower():
                    start_idx = json_text.lower().find('```json')
                    if start_idx != -1:
                        end_idx = json_text.find('```', start_idx + 7)
                        if end_idx != -1:
                            json_text = json_text[start_idx + 7:end_idx].strip()
                # Handle ``json (double backticks) - check this BEFORE generic ```
                elif '``json' in json_text.lower() and not json_text.lower().startswith('```json'):
                    start_idx = json_text.lower().find('``json')
                    if start_idx != -1:
                        # Look for closing backticks - could be `` or ``` or `
                        end_idx = json_text.find('```', start_idx + 6)
                        if end_idx == -1:
                            end_idx = json_text.find('``', start_idx + 6)
                        if end_idx == -1:
                            end_idx = json_text.find('`', start_idx + 6)
                        if end_idx != -1:
                            json_text = json_text[start_idx + 6:end_idx].strip()
                # Handle generic ``` code blocks
                elif '```' in json_text:
                    start_idx = json_text.find('```')
                    if start_idx != -1:
                        end_idx = json_text.find('```', start_idx + 3)
                        if end_idx != -1:
                            json_text = json_text[start_idx + 3:end_idx].strip()
                # Handle single backticks wrapping the entire text
                elif json_text.startswith('`') and json_text.endswith('`'):
                    json_text = json_text.strip('`').strip()
                
                # Try to find JSON object boundaries if not already clean
                if '{' in json_text and '}' in json_text:
                    start_brace = json_text.find('{')
                    end_brace = json_text.rfind('}')
                    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                        json_text = json_text[start_brace:end_brace + 1]
                        print(f"Extracted JSON object boundaries")
                
                print(f"Attempting to parse JSON (length: {len(json_text)}, first 200 chars: {json_text[:200]}...)")
                
                # Try to parse as JSON
                parsed_json = json.loads(json_text)
                
                # Extract email_body and email_subject from parsed JSON
                if 'email_body' in parsed_json:
                    content = str(parsed_json['email_body']).strip()
                    print(f"Found email_body in JSON")
                elif 'body' in parsed_json:
                    content = str(parsed_json['body']).strip()
                    print(f"Found body in JSON")
                elif 'message' in parsed_json:
                    content = str(parsed_json['message']).strip()
                    print(f"Found message in JSON")
                else:
                    raise KeyError(f"No email_body, body, or message field found in JSON. Available keys: {list(parsed_json.keys())}")
                
                if 'email_subject' in parsed_json:
                    subject = str(parsed_json['email_subject']).strip()
                elif 'subject' in parsed_json:
                    subject = str(parsed_json['subject']).strip()
                
                print(f"✓ Successfully parsed JSON - extracted email_body (length: {len(content)}) and subject: {subject}")
                print(f"  Content preview (first 100 chars): {content[:100]}...")
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # If JSON parsing fails, fall back to text extraction
                print(f"Could not parse JSON, falling back to text extraction: {e}")
                print(f"Response text (first 500 chars): {strategy_text[:500]}")
                if 'json_text' in locals():
                    print(f"Attempted to parse JSON text (first 500 chars): {json_text[:500]}")
                
                # Extract subject and body from text
                subject_found = False
                lines = strategy_text.split('\n')
                
                # Look for subject line patterns
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    # Check for subject patterns
                    if ('subject:' in line_lower or 'email_subject:' in line_lower) and ':' in line:
                        subject = line.split(':', 1)[1].strip().strip('"').strip("'")
                        subject_found = True
                        # Remove subject line from content
                        lines.pop(i)
                        break
                
                # Extract email body - remove subject line and any metadata
                # Look for common email body markers
                body_start_markers = [
                    'dear', 'hi', 'hello', 'greetings',
                    'email body:', 'body:', 'message:', 'content:'
                ]
                
                body_start_idx = 0
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    # Skip empty lines and subject-related lines
                    if not line.strip() or 'subject' in line_lower:
                        continue
                    # Check if this looks like the start of the email body
                    if any(line_lower.startswith(marker) for marker in body_start_markers):
                        body_start_idx = i
                        # Remove the marker line if it exists
                        if ':' in line:
                            body_start_idx = i + 1
                        break
                
                # Extract just the body content
                if body_start_idx > 0 or subject_found:
                    content = '\n'.join(lines[body_start_idx:]).strip()
                else:
                    # If no clear markers, use the full text but try to remove subject if found
                    content = strategy_text
                    if subject_found:
                        # Remove subject line from content
                        content = '\n'.join([l for l in lines if 'subject' not in l.lower()]).strip()
                
                # Clean up content - remove any remaining metadata markers
                content = re.sub(r'^(subject|email_subject|email body|body|message|content):\s*', '', content, flags=re.IGNORECASE | re.MULTILINE)
                content = content.strip()
            
        else:  # SMS
            # For SMS, try to parse JSON first
            try:
                json_text = strategy_text.strip()
                # Remove markdown code blocks if present
                if '```json' in json_text.lower():
                    start_idx = json_text.lower().find('```json')
                    if start_idx != -1:
                        end_idx = json_text.find('```', start_idx + 7)
                        if end_idx != -1:
                            json_text = json_text[start_idx + 7:end_idx].strip()
                elif '```' in json_text:
                    start_idx = json_text.find('```')
                    if start_idx != -1:
                        end_idx = json_text.find('```', start_idx + 3)
                        if end_idx != -1:
                            json_text = json_text[start_idx + 3:end_idx].strip()
                
                parsed_json = json.loads(json_text)
                
                if 'sms_message' in parsed_json:
                    content = str(parsed_json['sms_message']).strip()
                elif 'message' in parsed_json:
                    content = str(parsed_json['message']).strip()
                else:
                    content = strategy_text
            except (json.JSONDecodeError, KeyError, ValueError):
                # If JSON parsing fails, use the full text
                content = strategy_text
            subject = None
        
        # Update planned email with generated content
        db_manager.update_planned_email(
            planned_email_id,
            content=content,
            subject=subject,
            status="planned"
        )
        
        print(f"✓ Email content generated for planned email {planned_email_id}")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating email content in background: {error_details}")
        try:
            # Update email with error message so frontend can detect it
            error_message = f"Error generating content: {str(e)}"
            db_manager.update_planned_email(
                planned_email_id,
                content=f"Error: {error_message}. Please try again.",
                notes=error_message,
                status="planned"
            )
        except Exception as update_err:
            print(f"Failed to update email with error: {update_err}")

@app.post("/api/customers/{customer_id}/prepare-email")
async def prepare_email(
    customer_id: int,
    request: PrepareEmailRequest,
    background_tasks: BackgroundTasks
):
    """Generate email/SMS content and create planned email entry (async)"""
    try:
        # Validate communication type
        if request.communication_type not in ["email", "sms"]:
            raise HTTPException(status_code=400, detail="communication_type must be 'email' or 'sms'")
        
        # Create planned email immediately
        comm_type = CommunicationType.EMAIL if request.communication_type == "email" else CommunicationType.SMS
        planned_email = db_manager.create_planned_email(
            customer_id=customer_id,
            communication_type=comm_type,
            content="Generating email content...",
            status="planned",
            agent_id="current_user",
            notes="Planned email - generating content..."
        )
        
        # Add background task to generate content
        background_tasks.add_task(
            generate_email_content_background,
            customer_id,
            planned_email.id,
            request.communication_type
        )
        
        return {
            "success": True,
            "email_id": planned_email.id,
            "status": "processing",
            "message": "Email content generation started. It will be available shortly.",
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Unexpected error in prepare_email: {error_details}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/customers/{customer_id}/planned-email/{email_id}")
async def get_planned_email(customer_id: int, email_id: int):
    """Get a planned email for preview"""
    try:
        planned_email = db_manager.get_session().query(PlannedEmail).filter(
            PlannedEmail.id == email_id,
            PlannedEmail.customer_id == customer_id
        ).first()
        
        if not planned_email:
            raise HTTPException(status_code=404, detail="Planned email not found")
        
        return {
            "id": planned_email.id,
            "customer_id": planned_email.customer_id,
            "communication_type": planned_email.communication_type.value,
            "subject": planned_email.subject,
            "content": planned_email.content,
            "status": planned_email.status,
            "created_at": planned_email.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UpdateEmailRequest(BaseModel):
    subject: Optional[str] = None
    content: Optional[str] = None

@app.put("/api/customers/{customer_id}/planned-email/{email_id}")
async def update_planned_email_content(
    customer_id: int,
    email_id: int,
    request: UpdateEmailRequest
):
    """Update planned email content (for editing)"""
    try:
        planned_email = db_manager.get_session().query(PlannedEmail).filter(
            PlannedEmail.id == email_id,
            PlannedEmail.customer_id == customer_id
        ).first()
        
        if not planned_email:
            raise HTTPException(status_code=404, detail="Planned email not found")
        
        if planned_email.status != "planned":
            raise HTTPException(status_code=400, detail=f"Email status is {planned_email.status}, cannot edit")
        
        update_data = {}
        if request.content is not None:
            update_data["content"] = request.content
        if request.subject is not None:
            update_data["subject"] = request.subject
        
        updated_email = db_manager.update_planned_email(email_id, **update_data)
        
        return {
            "success": True,
            "email": {
                "id": updated_email.id,
                "subject": updated_email.subject,
                "content": updated_email.content,
                "status": updated_email.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/customers/{customer_id}/planned-email/{email_id}")
async def delete_planned_email(customer_id: int, email_id: int):
    """Delete a planned email"""
    try:
        planned_email = db_manager.get_session().query(PlannedEmail).filter(
            PlannedEmail.id == email_id,
            PlannedEmail.customer_id == customer_id
        ).first()
        
        if not planned_email:
            raise HTTPException(status_code=404, detail="Planned email not found")
        
        db_manager.delete_planned_email(email_id)
        
        return {
            "success": True,
            "message": "Planned email deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/customers/{customer_id}/communication-log/{log_id}")
async def delete_communication_log(customer_id: int, log_id: int):
    """Delete a communication log"""
    session = db_manager.get_session()
    try:
        comm_log = session.query(CommunicationLog).filter(
            CommunicationLog.id == log_id,
            CommunicationLog.customer_id == customer_id
        ).first()
        
        if not comm_log:
            raise HTTPException(status_code=404, detail="Communication log not found")
        
        session.delete(comm_log)
        session.commit()
        
        return {
            "success": True,
            "message": "Communication log deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.post("/api/customers/{customer_id}/cleanup-interactions")
async def cleanup_maria_interactions(customer_id: int):
    """Clean up specific problematic interactions for Maria Elena Santos"""
    try:
        customer = db_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify it's Maria Elena Santos
        if customer.first_name != "Maria" or customer.last_name != "Santos" or customer.middle_name != "Elena":
            raise HTTPException(status_code=400, detail="This endpoint is only for Maria Elena Santos")
        
        session = db_manager.get_session()
        deleted_count = 0
        
        try:
            # Get all planned emails
            planned_emails = session.query(PlannedEmail).filter(
                PlannedEmail.customer_id == customer_id
            ).all()
            
            # Delete planned emails matching the problematic patterns
            for email in planned_emails:
                should_delete = False
                
                # Check for JSON email
                if email.content and ("```json" in email.content or '"profile_type"' in email.content):
                    should_delete = True
                
                # Check for error email
                elif email.content and "Error generating content" in email.content:
                    should_delete = True
                
                # Check for payment reminder with traveling note
                elif email.notes and "payment reminder" in email.notes.lower() and "traveling" in email.notes.lower():
                    should_delete = True
                
                if should_delete:
                    session.delete(email)
                    deleted_count += 1
            
            # Get all communication logs
            comm_logs = session.query(CommunicationLog).filter(
                CommunicationLog.customer_id == customer_id,
                CommunicationLog.communication_type.in_([CommunicationType.EMAIL, CommunicationType.SMS])
            ).all()
            
            # Delete communication logs matching the problematic patterns
            for comm in comm_logs:
                should_delete = False
                
                # Check for JSON email in notes
                if comm.notes and ("```json" in comm.notes or '"profile_type"' in comm.notes):
                    should_delete = True
                
                # Check for error message
                elif comm.notes and "Error generating content" in comm.notes:
                    should_delete = True
                
                # Check for payment reminder
                elif comm.notes and "payment reminder" in comm.notes.lower() and "traveling" in comm.notes.lower():
                    should_delete = True
                
                if should_delete:
                    session.delete(comm)
                    deleted_count += 1
            
            session.commit()
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} problematic interactions",
                "deleted_count": deleted_count
            }
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers/{customer_id}/send-email/{email_id}")
async def send_email(customer_id: int, email_id: int):
    """Send a planned email/SMS"""
    try:
        planned_email = db_manager.get_session().query(PlannedEmail).filter(
            PlannedEmail.id == email_id,
            PlannedEmail.customer_id == customer_id
        ).first()
        
        if not planned_email:
            raise HTTPException(status_code=404, detail="Planned email not found")
        
        if planned_email.status != "planned":
            raise HTTPException(status_code=400, detail=f"Email status is {planned_email.status}, cannot send")
        
        # Get customer
        customer = db_manager.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Create communication log
        contact_email = customer.email if planned_email.communication_type == CommunicationType.EMAIL else None
        contact_phone = customer.phone_primary if planned_email.communication_type == CommunicationType.SMS else None
        
        # Store full email content in notes for visibility in completed interactions
        email_notes = ""
        if planned_email.subject:
            email_notes += f"Subject: {planned_email.subject}\n\n"
        if planned_email.content:
            email_notes += planned_email.content
        
        comm_log = db_manager.log_communication(
            customer_id=customer_id,
            communication_type=planned_email.communication_type,
            direction="outbound",
            contact_email=contact_email,
            contact_phone=contact_phone,
            outcome="sent",
            notes=email_notes or None,
            agent_id="current_user"
        )
        
        # Update planned email
        db_manager.update_planned_email(
            email_id,
            status="sent",
            sent_at=datetime.utcnow(),
            communication_log_id=comm_log.id
        )
        
        return {
            "success": True,
            "message": f"{planned_email.communication_type.value.capitalize()} sent successfully",
            "communication_log_id": comm_log.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/call-history/{call_id}/file")
async def delete_call_file(
    call_id: str,
    file_type: str  # "planning" or "transcript"
):
    """Delete a file associated with a call"""
    try:
        # Handle both numeric IDs and "scheduled_{id}" format
        if call_id.startswith("scheduled_"):
            call_id_int = int(call_id.replace("scheduled_", ""))
        else:
            call_id_int = int(call_id)
        
        if file_type == "transcript":
            # For transcripts, delete from database instead of file
            session = db_manager.get_session()
            try:
                # Check if this is a scheduled call with a communication_log_id
                scheduled_call = session.query(ScheduledCall).filter(
                    ScheduledCall.id == call_id_int
                ).first()
                
                if scheduled_call and scheduled_call.communication_log_id:
                    # Use communication_log_id for the transcript
                    transcript_id = scheduled_call.communication_log_id
                else:
                    # Use call_id directly (it's a communication_log_id)
                    transcript_id = call_id_int
                
                # Get communication log and clear transcript
                comm_log = session.query(CommunicationLog).filter(
                    CommunicationLog.id == transcript_id
                ).first()
                
                if not comm_log:
                    session.close()
                    raise HTTPException(status_code=404, detail="Communication log not found")
                
                if not comm_log.transcript:
                    session.close()
                    raise HTTPException(status_code=404, detail="Transcript not found in database")
                
                # Clear transcript from database
                comm_log.transcript = None
                session.commit()
                session.close()
                
                return {
                    "success": True,
                    "message": "Transcript deleted successfully from database"
                }
            except HTTPException:
                raise
            except Exception as e:
                session.rollback()
                session.close()
                raise HTTPException(status_code=500, detail=str(e))
        elif file_type == "planning":
            # For planning files, delete from filesystem
            file_path = FILES_DIR.parent / f"call_files/planning/call_{call_id_int}_planning.md"
            
            # Check if file exists
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"{file_type.capitalize()} file not found")
            
            # Delete the file
            file_path.unlink()
            
            # Also clear the database reference
            session = db_manager.get_session()
            try:
                # Get the scheduled call to find associated planning scripts
                scheduled_call = session.query(ScheduledCall).filter(
                    ScheduledCall.id == call_id_int
                ).first()
                
                if scheduled_call:
                    # Delete planning script records from database
                    planning_scripts = session.query(CallPlanningScript).filter(
                        CallPlanningScript.scheduled_call_id == call_id_int
                    ).all()
                    
                    for script in planning_scripts:
                        session.delete(script)
                    session.commit()
                session.close()
            except Exception as e:
                session.rollback()
                session.close()
                print(f"Warning: Could not delete planning scripts from DB: {e}")
        else:
            raise HTTPException(status_code=400, detail="Invalid file_type. Must be 'planning' or 'transcript'")
        
        return {
            "success": True,
            "message": f"{file_type.capitalize()} file deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SchedulePlannedCallRequest(BaseModel):
    scheduled_time: Optional[datetime] = None
    use_auto_time: bool = False

@app.post("/api/scheduled-calls/{call_id}/schedule")
async def schedule_planned_call(call_id: int, request: SchedulePlannedCallRequest):
    """Schedule a planned call"""
    try:
        scheduled_call = db_manager.get_session().query(ScheduledCall).filter(
            ScheduledCall.id == call_id,
            ScheduledCall.status == "planned"
        ).first()
        
        if not scheduled_call:
            raise HTTPException(status_code=404, detail="Planned call not found")
        
        # Get planning script
        scripts = db_manager.get_call_planning_scripts(scheduled_call.customer_id, call_id)
        if not scripts:
            raise HTTPException(status_code=404, detail="Planning script not found")
        
        planning_script = scripts[0]
        
        # Determine scheduled time
        final_time = request.scheduled_time
        if not final_time and request.use_auto_time:
            final_time = parse_time_from_strategy(
                planning_script.suggested_time or "",
                planning_script.suggested_day or ""
            )
            if not final_time:
                final_time = datetime.utcnow() + timedelta(days=1, hours=14)
        
        if not final_time:
            raise HTTPException(status_code=400, detail="scheduled_time is required or use_auto_time must be True")
        
        # Update scheduled call
        scheduled_call = db_manager.update_scheduled_call(
            call_id,
            scheduled_time=final_time,
            status="pending"
        )
        
        return {
            "success": True,
            "call": {
                "id": scheduled_call.id,
                "scheduled_time": scheduled_call.scheduled_time.isoformat(),
                "status": scheduled_call.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers/{customer_id}/upload-transcript")
async def upload_transcript(
    customer_id: int, 
    file: UploadFile = File(...), 
    scheduled_call_id: Optional[int] = Form(None),
    file_type: Optional[str] = Form("transcript")  # transcript, planning_notes, other
):
    """Upload and analyze a call transcript or other file"""
    try:
        # Read file content
        content = await file.read()
        file_text = content.decode('utf-8')
        
        if file_type == "transcript":
            # Initialize transcript analyzer
            analyzer = TranscriptAnalyzer(db_manager=db_manager)
            
            # Analyze transcript
            analysis_result = analyzer.analyze_transcript(
                transcript=file_text,
                customer_id=customer_id,
                call_id=f"upload_{datetime.utcnow().isoformat()}"
            )
            
            # Update database with results
            comm_log = analyzer.update_database(analysis_result)
            
            # Save transcript to database instead of file
            if comm_log:
                # Update the communication log with the transcript content
                session = db_manager.get_session()
                try:
                    comm_log.transcript = file_text
                    session.commit()
                    session.refresh(comm_log)
                except Exception as e:
                    session.rollback()
                    print(f"Error saving transcript to DB: {e}")
                finally:
                    session.close()
                
                # If linked to scheduled call, update it
                if scheduled_call_id:
                    db_manager.update_scheduled_call(
                        scheduled_call_id,
                        communication_log_id=comm_log.id,
                        status="completed"
                    )
            
            return {
                "success": True,
                "analysis": analysis_result,
                "message": "Transcript analyzed and database updated",
                "communication_id": comm_log.id if comm_log else None,
            }
        else:
            # For planning notes or other files, save as files (not transcripts)
            if scheduled_call_id:
                # Save as additional file for the call
                file_path = save_transcript_file(scheduled_call_id, file_text)
            else:
                # Save as general file
                file_path = save_transcript_file(f"general_{datetime.utcnow().timestamp()}", file_text)
            
            return {
                "success": True,
                "message": f"{file_type} file uploaded successfully",
                "file_path": file_path,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/transcript/{communication_id}")
async def get_transcript_analysis(customer_id: int, communication_id: int):
    """Get transcript analysis for a specific communication"""
    try:
        # This would require storing transcript analysis results
        # For now, return a placeholder
        comm = db_manager.get_session().query(CommunicationLog).filter(
            CommunicationLog.id == communication_id,
            CommunicationLog.customer_id == customer_id
        ).first()
        
        if not comm:
            raise HTTPException(status_code=404, detail="Communication not found")
        
        return {
            "communication_id": comm.id,
            "timestamp": comm.timestamp.isoformat(),
            "outcome": comm.outcome,
            "notes": comm.notes,
            "message": "Transcript analysis storage not yet implemented"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers/{customer_id}/make-ai-call")
async def make_ai_call(customer_id: int):
    """Initiate an AI-powered call to the customer"""
    logger.info("[make-ai-call] customer_id=%d — Request received", customer_id)
    try:
        if not OUTBOUND_CALL_AVAILABLE:
            logger.error("[make-ai-call] customer_id=%d — OutboundCallManager not available", customer_id)
            raise HTTPException(status_code=503, detail="AI call functionality is not available. OutboundCallManager not found.")

        # Get customer
        customer = db_manager.get_customer(customer_id)
        if not customer:
            logger.warning("[make-ai-call] customer_id=%d — Customer not found in DB", customer_id)
            raise HTTPException(status_code=404, detail="Customer not found")

        if not customer.phone_primary:
            logger.warning("[make-ai-call] customer_id=%d — No phone number on file", customer_id)
            raise HTTPException(status_code=400, detail="Customer phone number is required")

        # Get webhook URL from environment or use default
        webhook_url = os.getenv('TWILIO_WEBHOOK_URL', 'http://localhost:5000/voice')

        # Initialize outbound call manager
        call_manager = OutboundCallManager()

        # Make the call
        logger.info("[make-ai-call] customer_id=%d — Initiating Twilio call to %s", customer_id, customer.phone_primary)
        call_start = time.time()
        call_sid = call_manager.make_call(
            to_number=customer.phone_primary,
            webhook_url=webhook_url
        )
        logger.info("[make-ai-call] customer_id=%d — Twilio call initiated (%.2fs). call_sid=%s", customer_id, time.time() - call_start, call_sid)

        # Create a communication log entry for the call
        comm_log = db_manager.create_communication_log(
            customer_id=customer_id,
            communication_type=CommunicationType.CALL,
            direction="outbound",
            contact_phone=customer.phone_primary,
            outcome="initiated",
            notes=f"AI call initiated via Twilio. Call SID: {call_sid}",
            agent_id="ai_system"
        )
        logger.info("[make-ai-call] customer_id=%d — Communication log created: id=%d", customer_id, comm_log.id)

        return {
            "success": True,
            "message": "AI call initiated successfully",
            "call_sid": call_sid,
            "communication_log_id": comm_log.id,
            "phone_number": customer.phone_primary
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error("[make-ai-call] customer_id=%d — Unhandled exception: %s", customer_id, error_details)
        raise HTTPException(status_code=500, detail=f"Failed to initiate AI call: {str(e)}")

CALL_SERVICE_URL = os.getenv("CALL_SERVICE_URL", "https://cxc-call-service.onrender.com")

@app.post("/api/customers/{customer_id}/make-call")
async def proxy_make_call(customer_id: int, background_tasks: BackgroundTasks):
    """Proxy call to external call service, wait for response, save transcript."""
    logger.info("[make-call] customer_id=%d — Request received", customer_id)
    customer = db_manager.get_customer(customer_id)
    if not customer:
        logger.warning("[make-call] customer_id=%d — Customer not found in DB", customer_id)
        raise HTTPException(status_code=404, detail="Customer not found")

    debts = db_manager.get_customer_debts(customer_id)
    scheduled_calls = db_manager.get_scheduled_calls(customer_id)
    logger.debug("[make-call] customer_id=%d — Loaded %d debts, %d scheduled calls", customer_id, len(debts), len(scheduled_calls))

    payload = {
        "customer": {col.name: getattr(customer, col.name) for col in customer.__table__.columns},
        "debts": [{col.name: getattr(d, col.name) for col in d.__table__.columns} for d in debts],
        "scheduled_calls": [{col.name: getattr(c, col.name) for col in c.__table__.columns} for c in scheduled_calls],
    }

    # Serialize non-JSON types to strings
    import json as _json
    from datetime import date as _date
    from enum import Enum as _Enum
    def _default(o):
        if isinstance(o, (datetime, _date)):
            return o.isoformat()
        if isinstance(o, _Enum):
            return o.value
        return str(o)
    serialized = _json.loads(_json.dumps(payload, default=_default))

    def forward_call_and_save_transcript():
        call_start = time.time()
        try:
            logger.info("[make-call] customer_id=%d — Sending request to call service at %s", customer_id, CALL_SERVICE_URL)
            resp = requests.post(f"{CALL_SERVICE_URL}/make_call", json=serialized, timeout=600)
            call_elapsed = time.time() - call_start

            if resp.status_code != 200:
                logger.error("[make-call] customer_id=%d — Call service returned HTTP %d (%.2fs): %s", customer_id, resp.status_code, call_elapsed, resp.text[:300])
                return

            call_result = resp.json()
            conversation_id = call_result.get("conversation_id", "unknown")
            call_status = call_result.get("status", "unknown")
            logger.info("[make-call] customer_id=%d — Call completed (%.2fs). conversation_id=%s, status=%s", customer_id, call_elapsed, conversation_id, call_status)

            transcript = call_result.get("transcript", [])
            if transcript:
                logger.info("[make-call] customer_id=%d — Transcript received: %d messages", customer_id, len(transcript))
                transcript_text = "\n".join(
                    f"{'Agent' if t.get('role') == 'agent' else 'Customer'}: {t.get('message', '')}"
                    for t in transcript
                )
                logger.info("[make-call] customer_id=%d — Formatted transcript: %d chars. Generating AI notes...", customer_id, len(transcript_text))
                notes = generate_notes_from_transcript(transcript_text, customer_id=customer_id)
                logger.info("[make-call] customer_id=%d — Saving communication log to DB", customer_id)
                db_manager.log_communication(
                    customer_id=customer_id,
                    communication_type=CommunicationType.CALL,
                    direction="outbound",
                    contact_phone=customer.phone_primary or "",
                    outcome="completed" if call_status == "done" else call_status,
                    notes=notes,
                    transcript=transcript_text,
                    agent_id="ai_voice_agent",
                )
                total_elapsed = time.time() - call_start
                logger.info("[make-call] customer_id=%d — Pipeline complete (%.2fs total). Transcript + notes saved", customer_id, total_elapsed)
            else:
                logger.warning("[make-call] customer_id=%d — No transcript returned from call service", customer_id)
        except Exception as e:
            elapsed = time.time() - call_start
            logger.error("[make-call] customer_id=%d — Error after %.2fs: %s", customer_id, elapsed, e, exc_info=True)

    background_tasks.add_task(forward_call_and_save_transcript)
    logger.info("[make-call] customer_id=%d — Background task queued. Returning to client", customer_id)
    return {"success": True, "message": "Call is being initiated"}


class SaveTranscriptRequest(BaseModel):
    conversation_id: str
    status: str
    transcript: list
    customer_id: int

@app.post("/api/customers/{customer_id}/save-transcript")
async def save_transcript(customer_id: int, req: SaveTranscriptRequest):
    """Save call transcript from call service to the database."""
    pipeline_start = time.time()
    logger.info("[save-transcript] customer_id=%d — Request received. conversation_id=%s, status=%s, transcript_messages=%d",
                customer_id, req.conversation_id, req.status, len(req.transcript))

    customer = db_manager.get_customer(customer_id)
    if not customer:
        logger.warning("[save-transcript] customer_id=%d — Customer not found in DB", customer_id)
        raise HTTPException(status_code=404, detail="Customer not found")

    # Format transcript as readable text
    transcript_text = "\n".join(
        f"{'Agent' if t.get('role') == 'agent' else 'Customer'}: {t.get('message', '')}"
        for t in req.transcript
    )
    logger.info("[save-transcript] customer_id=%d — Formatted transcript: %d chars", customer_id, len(transcript_text))

    # Generate AI notes from transcript using Gemini
    logger.info("[save-transcript] customer_id=%d — Generating AI notes via Gemini...", customer_id)
    notes = generate_notes_from_transcript(transcript_text, customer_id=customer_id)

    # Save as a communication log
    logger.info("[save-transcript] customer_id=%d — Saving communication log to DB (outcome=%s)", customer_id, req.status)
    comm_log = db_manager.log_communication(
        customer_id=customer_id,
        communication_type=CommunicationType.CALL,
        direction="outbound",
        contact_phone=customer.phone_primary or "",
        outcome="completed" if req.status == "done" else req.status,
        notes=notes,
        transcript=transcript_text,
        agent_id="ai_voice_agent",
    )

    total_elapsed = time.time() - pipeline_start
    logger.info("[save-transcript] customer_id=%d — Pipeline complete (%.2fs). comm_log_id=%d", customer_id, total_elapsed, comm_log.id)
    return {"success": True, "communication_log_id": comm_log.id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
