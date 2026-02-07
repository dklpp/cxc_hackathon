"""
FastAPI Backend for Customer Debt Management System
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DB.db_manager import (
    DatabaseManager, Customer, Debt, CommunicationLog, ScheduledCall,
    DebtStatus, PaymentStatus, CommunicationType
)
from transcript_analysis.transcript_analyzer import TranscriptAnalyzer

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
    scheduled_time: datetime
    notes: Optional[str] = None
    agent_id: Optional[str] = None

class ScheduledCallResponse(BaseModel):
    id: int
    customer_id: int
    scheduled_time: datetime
    status: str
    notes: Optional[str]
    agent_id: Optional[str]
    created_at: datetime
    
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
        
        return {
            "customer": {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone_primary": customer.phone_primary,
                "phone_secondary": customer.phone_secondary,
                "address_line1": customer.address_line1,
                "address_line2": customer.address_line2,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "employer_name": customer.employer_name,
                "employment_status": customer.employment_status,
                "annual_income": customer.annual_income,
                "credit_score": customer.credit_score,
                "account_status": customer.account_status,
                "preferred_communication_method": customer.preferred_communication_method.value if customer.preferred_communication_method else None,
                "notes": customer.notes,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
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
                    "scheduled_time": sc.scheduled_time.isoformat(),
                    "status": sc.status,
                    "notes": sc.notes,
                    "agent_id": sc.agent_id,
                    "created_at": sc.created_at.isoformat(),
                }
                for sc in scheduled_calls
            ]
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

@app.post("/api/scheduled-calls", response_model=ScheduledCallResponse)
async def create_scheduled_call(call: ScheduledCallRequest):
    """Schedule a call for a customer"""
    try:
        scheduled_call = db_manager.create_scheduled_call(
            customer_id=call.customer_id,
            scheduled_time=call.scheduled_time,
            notes=call.notes,
            agent_id=call.agent_id,
            status="pending"
        )
        return {
            "id": scheduled_call.id,
            "customer_id": scheduled_call.customer_id,
            "scheduled_time": scheduled_call.scheduled_time.isoformat(),
            "status": scheduled_call.status,
            "notes": scheduled_call.notes,
            "agent_id": scheduled_call.agent_id,
            "created_at": scheduled_call.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/call-history", response_model=List[CommunicationResponse])
async def get_call_history(customer_id: int):
    """Get call history for a customer"""
    try:
        communications = db_manager.get_communication_logs(customer_id, limit=100)
        # Filter for calls only
        calls = [c for c in communications if c.communication_type == CommunicationType.CALL]
        return [
            {
                "id": c.id,
                "customer_id": c.customer_id,
                "communication_type": c.communication_type.value,
                "direction": c.direction,
                "timestamp": c.timestamp.isoformat(),
                "outcome": c.outcome,
                "notes": c.notes,
                "duration_seconds": c.duration_seconds,
            }
            for c in calls
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers/{customer_id}/upload-transcript")
async def upload_transcript(customer_id: int, file: UploadFile = File(...)):
    """Upload and analyze a call transcript"""
    try:
        # Read transcript content
        content = await file.read()
        transcript_text = content.decode('utf-8')
        
        # Initialize transcript analyzer
        analyzer = TranscriptAnalyzer(db_manager=db_manager)
        
        # Analyze transcript
        analysis_result = analyzer.analyze_transcript(
            transcript=transcript_text,
            customer_id=customer_id,
            call_id=f"upload_{datetime.utcnow().isoformat()}"
        )
        
        # Update database with results
        analyzer.update_database(analysis_result)
        
        return {
            "success": True,
            "analysis": analysis_result,
            "message": "Transcript analyzed and database updated"
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
