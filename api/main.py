"""
FastAPI Backend for Customer Debt Management System
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import json
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, Customer, Debt, CommunicationLog, ScheduledCall, CallPlanningScript,
    DebtStatus, PaymentStatus, CommunicationType
)
from transcript_analysis.transcript_analyzer import TranscriptAnalyzer
from strategy_planning.strategy_pipeline import GeminiStrategyGenerator
import re

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

# Create directories for storing files
FILES_DIR = Path(__file__).parent.parent / "call_files"
FILES_DIR.mkdir(exist_ok=True, parents=True)
PLANNING_DIR = FILES_DIR / "planning"
TRANSCRIPT_DIR = FILES_DIR / "transcripts"
PLANNING_DIR.mkdir(exist_ok=True, parents=True)
TRANSCRIPT_DIR.mkdir(exist_ok=True, parents=True)

# Pydantic models for request/response
class CustomerResponse(BaseModel):
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
    total_debt: Optional[float] = None
    
    class Config:
        from_attributes = True

class DebtResponse(BaseModel):
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
    
    class Config:
        from_attributes = True

class CommunicationResponse(BaseModel):
    id: int
    customer_id: int
    communication_type: str
    direction: str
    timestamp: datetime
    outcome: Optional[str]
    notes: Optional[str]
    duration_seconds: Optional[int]
    
    class Config:
        from_attributes = True

class ScheduledCallRequest(BaseModel):
    customer_id: int
    scheduled_time: Optional[datetime] = None  # Optional - can be auto-selected
    notes: Optional[str] = None
    agent_id: Optional[str] = None
    use_auto_time: bool = False  # If True, use time from strategy
    planning_script_id: Optional[int] = None  # If scheduling a planned call

class ScheduledCallResponse(BaseModel):
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
    
    class Config:
        from_attributes = True

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
            notes=call.notes or ("Generating strategy..." if call.use_auto_time else None),
            agent_id=call.agent_id,
            status="pending"
        )
        
        # If we need to generate strategy (use_auto_time without existing script), do it in background
        if call.use_auto_time and not call.planning_script_id:
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
                "script_id": None,
                "suggested_time": None,
                "suggested_day": None,
                "planning_file_path": None,
                "status_message": "Strategy generation started. Planning file will be available shortly.",
            }
        
        # If we have a planning script, we're done
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
    """Get call history for a customer (includes scheduled calls and communication logs)"""
    try:
        # Get communication logs (actual calls)
        communications = db_manager.get_communication_logs(customer_id, limit=100)
        calls = [c for c in communications if c.communication_type == CommunicationType.CALL]
        
        # Get scheduled calls (including planned)
        scheduled_calls = db_manager.get_scheduled_calls(customer_id=customer_id)
        
        # Separate into planned, scheduled (automatic), and completed
        planned_calls = []
        automatic_calls = []
        completed_calls = []
        
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
                "transcript_file_path": transcript_file_path,
                "scheduled_call_id": None,
            })
        
        # Sort each list by timestamp (most recent first)
        planned_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        automatic_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        completed_calls.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "planned": planned_calls,
            "automatic": automatic_calls,
            "completed": completed_calls,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """Get transcript file content for a call"""
    try:
        # Handle both numeric IDs and "scheduled_{id}" format
        if call_id.startswith("scheduled_"):
            comm_id = int(call_id.replace("scheduled_", ""))
        else:
            comm_id = int(call_id)
        
        file_path = f"call_files/transcripts/call_{comm_id}_transcript.md"
        content = get_file_content(file_path)
        
        if not content:
            raise HTTPException(status_code=404, detail="Transcript file not found")
        
        return {
            "content": content,
            "file_path": file_path,
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
            
            # Save transcript file
            file_path = None
            if comm_log:
                file_path = save_transcript_file(comm_log.id, file_text)
                
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
                "file_path": file_path,
            }
        else:
            # For planning notes or other files, just save them
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
