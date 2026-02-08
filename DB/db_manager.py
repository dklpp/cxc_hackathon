"""
Database Manager for Banking System - Customer Data and Debt Tracking

This module provides database management functionality for tracking customer
profiles, debts, payments, and communication logs in an internal banking system.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
import enum

Base = declarative_base()


# Enums for status tracking
class DebtStatus(enum.Enum):
    """Status of a debt account"""
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    IN_COLLECTION = "in_collection"
    SETTLED = "settled"
    WRITTEN_OFF = "written_off"


class PaymentStatus(enum.Enum):
    """Status of a payment"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CommunicationType(enum.Enum):
    """Type of communication"""
    CALL = "call"
    EMAIL = "email"
    SMS = "sms"
    LETTER = "letter"
    IN_PERSON = "in_person"


# Database Models
class Customer(Base):
    """Customer personal profile table"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    ssn = Column(String(11), unique=True, nullable=True)  # Format: XXX-XX-XXXX
    
    # Contact Information
    email = Column(String(255), unique=True, nullable=True)
    phone_primary = Column(String(20), nullable=False)
    phone_secondary = Column(String(20), nullable=True)
    
    # Address Information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    country = Column(String(100), default='USA')
    
    # Employment Information
    employer_name = Column(String(255), nullable=True)
    employment_status = Column(String(50), nullable=True)  # employed, unemployed, retired, etc.
    annual_income = Column(Float, nullable=True)
    
    # Account Status
    account_status = Column(String(50), default='active')  # active, closed, frozen, etc.
    credit_score = Column(Integer, nullable=True)
    
    # Communication Preferences
    preferred_communication_method = Column(Enum(CommunicationType), nullable=True)  # Preferred way to contact customer
    preferred_contact_time = Column(String(100), nullable=True)  # Preferred time range (e.g., "9 AM - 5 PM", "Evenings only")
    preferred_contact_days = Column(String(100), nullable=True)  # Preferred days (e.g., "Weekdays", "Monday-Friday", "Any day")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    debts = relationship("Debt", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    communications = relationship("CommunicationLog", back_populates="customer", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    scheduled_calls = relationship("ScheduledCall", back_populates="customer", cascade="all, delete-orphan")
    call_planning_scripts = relationship("CallPlanningScript", back_populates="customer", cascade="all, delete-orphan")
    planned_emails = relationship("PlannedEmail", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.first_name} {self.last_name}', phone='{self.phone_primary}')>"


class Debt(Base):
    """Debt records table"""
    __tablename__ = 'debts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Debt Information
    debt_type = Column(String(100), nullable=False)  # credit_card, loan, mortgage, etc.
    original_amount = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=True)  # Annual percentage rate
    minimum_payment = Column(Float, nullable=True)
    
    # Dates
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(Enum(DebtStatus), default=DebtStatus.ACTIVE, nullable=False)
    days_past_due = Column(Integer, default=0)
    
    # Account Information
    account_number = Column(String(50), nullable=True)
    reference_number = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="debts")
    payments = relationship("Payment", back_populates="debt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Debt(id={self.id}, customer_id={self.customer_id}, balance=${self.current_balance:.2f}, status={self.status.value})>"


class Payment(Base):
    """Payment history table"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    debt_id = Column(Integer, ForeignKey('debts.id'), nullable=False)
    
    # Payment Information
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String(50), nullable=True)  # credit_card, bank_transfer, check, cash, etc.
    transaction_id = Column(String(100), unique=True, nullable=True)
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="payments")
    debt = relationship("Debt", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount=${self.amount:.2f}, date={self.payment_date}, status={self.status.value})>"


class CommunicationLog(Base):
    """Communication logs table for tracking all customer interactions"""
    __tablename__ = 'communication_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Communication Details
    communication_type = Column(Enum(CommunicationType), nullable=False)
    direction = Column(String(20), nullable=False)  # inbound, outbound
    duration_seconds = Column(Integer, nullable=True)  # For calls
    
    # Contact Information Used
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Outcome
    outcome = Column(String(100), nullable=True)  # payment_promised, no_answer, voicemail, etc.
    notes = Column(Text, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent_id = Column(String(100), nullable=True)  # ID of the agent/system that made the contact
    
    # Relationships
    customer = relationship("Customer", back_populates="communications")
    
    def __repr__(self):
        return f"<CommunicationLog(id={self.id}, type={self.communication_type.value}, customer_id={self.customer_id}, timestamp={self.timestamp})>"


class Account(Base):
    """Bank account information table"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Account Information
    account_type = Column(String(50), nullable=False)  # checking, savings, credit_card, etc.
    account_number = Column(String(50), unique=True, nullable=False)
    routing_number = Column(String(20), nullable=True)
    bank_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    
    def __repr__(self):
        return f"<Account(id={self.id}, type={self.account_type}, account_number={self.account_number[:4]}***, customer_id={self.customer_id})>"


class CallPlanningScript(Base):
    """Call planning scripts generated by strategy planning"""
    __tablename__ = 'call_planning_scripts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    scheduled_call_id = Column(Integer, ForeignKey('scheduled_calls.id'), nullable=True)  # Optional link to scheduled call
    
    # Strategy Content
    strategy_content = Column(Text, nullable=False)  # Full output from strategy planning
    suggested_time = Column(String(100), nullable=True)  # Suggested best contact time
    suggested_day = Column(String(100), nullable=True)  # Suggested best contact day
    communication_channel = Column(String(50), nullable=True)
    profile_type = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # Agent ID who generated it
    
    # Relationships
    customer = relationship("Customer", back_populates="call_planning_scripts")
    scheduled_call = relationship("ScheduledCall", back_populates="planning_script", foreign_keys=[scheduled_call_id])
    
    def __repr__(self):
        return f"<CallPlanningScript(id={self.id}, customer_id={self.customer_id}, created_at={self.created_at})>"


class ScheduledCall(Base):
    """Scheduled calls table for tracking planned customer calls"""
    __tablename__ = 'scheduled_calls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Scheduling Information
    scheduled_time = Column(DateTime, nullable=True)  # Nullable for planned calls
    status = Column(String(50), default='pending', nullable=False)  # pending, planned, completed, cancelled, missed
    
    # Call Details
    agent_id = Column(String(100), nullable=True)  # ID of the agent who scheduled it
    notes = Column(Text, nullable=True)  # Pre-call notes or reason for call
    
    # Result (linked to CommunicationLog after call)
    communication_log_id = Column(Integer, ForeignKey('communication_logs.id'), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="scheduled_calls")
    communication_log = relationship("CommunicationLog", foreign_keys=[communication_log_id])
    planning_script = relationship("CallPlanningScript", back_populates="scheduled_call", uselist=False)
    
    def __repr__(self):
        return f"<ScheduledCall(id={self.id}, customer_id={self.customer_id}, scheduled_time={self.scheduled_time}, status={self.status})>"


class PlannedEmail(Base):
    """Planned emails/SMS table for tracking email communications"""
    __tablename__ = 'planned_emails'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Email/SMS Information
    communication_type = Column(Enum(CommunicationType), nullable=False)  # EMAIL or SMS
    subject = Column(String(500), nullable=True)  # Subject line (for emails)
    content = Column(Text, nullable=False)  # Email/SMS content
    status = Column(String(50), default='planned', nullable=False)  # planned, sent, cancelled
    
    # Planning Script Reference
    planning_script_id = Column(Integer, ForeignKey('call_planning_scripts.id'), nullable=True)
    
    # Sending Information
    scheduled_send_time = Column(DateTime, nullable=True)  # When to send (optional)
    sent_at = Column(DateTime, nullable=True)  # When it was actually sent
    
    # Result (linked to CommunicationLog after sending)
    communication_log_id = Column(Integer, ForeignKey('communication_logs.id'), nullable=True)
    
    # Metadata
    agent_id = Column(String(100), nullable=True)  # ID of the agent who created it
    notes = Column(Text, nullable=True)  # Notes about the email
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="planned_emails")
    planning_script = relationship("CallPlanningScript", foreign_keys=[planning_script_id])
    communication_log = relationship("CommunicationLog", foreign_keys=[communication_log_id])
    
    def __repr__(self):
        return f"<PlannedEmail(id={self.id}, customer_id={self.customer_id}, type={self.communication_type.value}, status={self.status})>"


class DatabaseManager:
    """Database manager class for handling all database operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            database_url: SQLAlchemy database URL. If None, defaults to SQLite in DB directory.
        """
        if database_url is None:
            # Default to SQLite database in the DB directory
            db_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(db_dir, 'banking_system.db')
            database_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        self._migrate_scheduled_calls_if_needed()
        self._migrate_customer_contact_preferences_if_needed()
        print("Database tables created successfully.")
    
    def _migrate_scheduled_calls_if_needed(self):
        """Migrate scheduled_calls table to allow NULL scheduled_time if needed"""
        try:
            import sqlite3
            from sqlalchemy import inspect
            
            # Only migrate if using SQLite
            if 'sqlite' in str(self.engine.url):
                inspector = inspect(self.engine)
                if 'scheduled_calls' in inspector.get_table_names():
                    # Check if scheduled_time is nullable
                    columns = inspector.get_columns('scheduled_calls')
                    scheduled_time_col = next((col for col in columns if col['name'] == 'scheduled_time'), None)
                    
                    if scheduled_time_col and not scheduled_time_col.get('nullable', False):
                        # Need to migrate
                        conn = self.engine.raw_connection()
                        cursor = conn.cursor()
                        
                        try:
                            # Create new table
                            cursor.execute("""
                                CREATE TABLE scheduled_calls_new (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    customer_id INTEGER NOT NULL,
                                    scheduled_time DATETIME,
                                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                                    agent_id VARCHAR(100),
                                    notes TEXT,
                                    communication_log_id INTEGER,
                                    created_at DATETIME,
                                    updated_at DATETIME,
                                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                                    FOREIGN KEY (communication_log_id) REFERENCES communication_logs(id)
                                )
                            """)
                            
                            # Copy data
                            cursor.execute("""
                                INSERT INTO scheduled_calls_new 
                                (id, customer_id, scheduled_time, status, agent_id, notes, 
                                 communication_log_id, created_at, updated_at)
                                SELECT 
                                    id, customer_id, scheduled_time, status, agent_id, notes,
                                    communication_log_id, created_at, updated_at
                                FROM scheduled_calls
                            """)
                            
                            # Drop old and rename
                            cursor.execute("DROP TABLE scheduled_calls")
                            cursor.execute("ALTER TABLE scheduled_calls_new RENAME TO scheduled_calls")
                            conn.commit()
                            print("✓ Migrated scheduled_calls table to allow NULL scheduled_time")
                        except Exception as e:
                            conn.rollback()
                            print(f"Warning: Migration failed (this is OK if table is already migrated): {e}")
                        finally:
                            conn.close()
        except Exception as e:
            # Don't fail if migration can't run
            print(f"Warning: Could not check/run migration: {e}")
    
    def _migrate_customer_contact_preferences_if_needed(self):
        """Migrate customers table to add preferred_contact_time and preferred_contact_days if needed"""
        try:
            import sqlite3
            from sqlalchemy import inspect
            
            # Only migrate if using SQLite
            if 'sqlite' in str(self.engine.url):
                inspector = inspect(self.engine)
                if 'customers' in inspector.get_table_names():
                    columns = inspector.get_columns('customers')
                    column_names = [col['name'] for col in columns]
                    
                    needs_migration = False
                    if 'preferred_contact_time' not in column_names:
                        needs_migration = True
                    if 'preferred_contact_days' not in column_names:
                        needs_migration = True
                    
                    if needs_migration:
                        conn = self.engine.raw_connection()
                        cursor = conn.cursor()
                        
                        try:
                            # Add preferred_contact_time if missing
                            if 'preferred_contact_time' not in column_names:
                                cursor.execute("""
                                    ALTER TABLE customers 
                                    ADD COLUMN preferred_contact_time VARCHAR(100)
                                """)
                                print("✓ Added preferred_contact_time column to customers table")
                            
                            # Add preferred_contact_days if missing
                            if 'preferred_contact_days' not in column_names:
                                cursor.execute("""
                                    ALTER TABLE customers 
                                    ADD COLUMN preferred_contact_days VARCHAR(100)
                                """)
                                print("✓ Added preferred_contact_days column to customers table")
                            
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            print(f"Warning: Migration failed (this is OK if columns already exist): {e}")
                        finally:
                            conn.close()
        except Exception as e:
            # Don't fail if migration can't run
            print(f"Warning: Could not check/run migration: {e}")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    # Customer Operations
    def create_customer(self, **kwargs) -> Customer:
        """Create a new customer record"""
        session = self.get_session()
        try:
            customer = Customer(**kwargs)
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating customer: {str(e)}")
        finally:
            session.close()
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by ID"""
        session = self.get_session()
        try:
            return session.query(Customer).filter(Customer.id == customer_id).first()
        finally:
            session.close()
    
    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get a customer by phone number"""
        session = self.get_session()
        try:
            return session.query(Customer).filter(
                (Customer.phone_primary == phone) | (Customer.phone_secondary == phone)
            ).first()
        finally:
            session.close()
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get a customer by email"""
        session = self.get_session()
        try:
            return session.query(Customer).filter(Customer.email == email).first()
        finally:
            session.close()
    
    def update_customer(self, customer_id: int, **kwargs) -> Optional[Customer]:
        """Update customer information"""
        session = self.get_session()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                for key, value in kwargs.items():
                    if hasattr(customer, key):
                        setattr(customer, key, value)
                customer.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(customer)
            return customer
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error updating customer: {str(e)}")
        finally:
            session.close()
    
    def list_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """List all customers with pagination"""
        session = self.get_session()
        try:
            return session.query(Customer).offset(offset).limit(limit).all()
        finally:
            session.close()
    
    def search_customers(self, search_term: str) -> List[Customer]:
        """Search customers by name, phone, or email"""
        session = self.get_session()
        try:
            search_pattern = f"%{search_term}%"
            return session.query(Customer).filter(
                (Customer.first_name.ilike(search_pattern)) |
                (Customer.last_name.ilike(search_pattern)) |
                (Customer.phone_primary.ilike(search_pattern)) |
                (Customer.email.ilike(search_pattern))
            ).all()
        finally:
            session.close()
    
    # Debt Operations
    def create_debt(self, customer_id: int, **kwargs) -> Debt:
        """Create a new debt record"""
        session = self.get_session()
        try:
            debt = Debt(customer_id=customer_id, **kwargs)
            session.add(debt)
            session.commit()
            session.refresh(debt)
            return debt
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating debt: {str(e)}")
        finally:
            session.close()
    
    def get_debt(self, debt_id: int) -> Optional[Debt]:
        """Get a debt by ID"""
        session = self.get_session()
        try:
            return session.query(Debt).filter(Debt.id == debt_id).first()
        finally:
            session.close()
    
    def get_customer_debts(self, customer_id: int, status: Optional[DebtStatus] = None) -> List[Debt]:
        """Get all debts for a customer, optionally filtered by status"""
        session = self.get_session()
        try:
            query = session.query(Debt).filter(Debt.customer_id == customer_id)
            if status:
                query = query.filter(Debt.status == status)
            return query.all()
        finally:
            session.close()
    
    def update_debt(self, debt_id: int, **kwargs) -> Optional[Debt]:
        """Update debt information"""
        session = self.get_session()
        try:
            debt = session.query(Debt).filter(Debt.id == debt_id).first()
            if debt:
                for key, value in kwargs.items():
                    if hasattr(debt, key):
                        setattr(debt, key, value)
                debt.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(debt)
            return debt
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error updating debt: {str(e)}")
        finally:
            session.close()
    
    def get_total_debt(self, customer_id: int) -> float:
        """Get total debt amount for a customer"""
        session = self.get_session()
        try:
            result = session.query(Debt).filter(
                Debt.customer_id == customer_id,
                Debt.status != DebtStatus.PAID_OFF
            ).all()
            return sum(debt.current_balance for debt in result)
        finally:
            session.close()
    
    # Payment Operations
    def create_payment(self, customer_id: int, debt_id: int, amount: float, **kwargs) -> Payment:
        """Create a payment record and update debt balance"""
        session = self.get_session()
        try:
            payment = Payment(customer_id=customer_id, debt_id=debt_id, amount=amount, **kwargs)
            session.add(payment)
            
            # Update debt balance
            debt = session.query(Debt).filter(Debt.id == debt_id).first()
            if debt:
                debt.current_balance = max(0, debt.current_balance - amount)
                debt.last_payment_date = payment.payment_date
                
                # Update debt status if paid off
                if debt.current_balance == 0:
                    debt.status = DebtStatus.PAID_OFF
                
                debt.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(payment)
            return payment
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating payment: {str(e)}")
        finally:
            session.close()
    
    def get_payments(self, customer_id: Optional[int] = None, debt_id: Optional[int] = None) -> List[Payment]:
        """Get payment records, optionally filtered by customer or debt"""
        session = self.get_session()
        try:
            query = session.query(Payment)
            if customer_id:
                query = query.filter(Payment.customer_id == customer_id)
            if debt_id:
                query = query.filter(Payment.debt_id == debt_id)
            return query.order_by(Payment.payment_date.desc()).all()
        finally:
            session.close()
    
    # Communication Log Operations
    def log_communication(self, customer_id: int, communication_type: CommunicationType, 
                         direction: str, **kwargs) -> CommunicationLog:
        """Log a communication with a customer"""
        session = self.get_session()
        try:
            log = CommunicationLog(
                customer_id=customer_id,
                communication_type=communication_type,
                direction=direction,
                **kwargs
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error logging communication: {str(e)}")
        finally:
            session.close()
    
    def get_communication_logs(self, customer_id: int, limit: int = 50) -> List[CommunicationLog]:
        """Get communication logs for a customer"""
        session = self.get_session()
        try:
            return session.query(CommunicationLog).filter(
                CommunicationLog.customer_id == customer_id
            ).order_by(CommunicationLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    # Account Operations
    def create_account(self, customer_id: int, **kwargs) -> Account:
        """Create a bank account record"""
        session = self.get_session()
        try:
            account = Account(customer_id=customer_id, **kwargs)
            session.add(account)
            session.commit()
            session.refresh(account)
            return account
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating account: {str(e)}")
        finally:
            session.close()
    
    def get_customer_accounts(self, customer_id: int) -> List[Account]:
        """Get all accounts for a customer"""
        session = self.get_session()
        try:
            return session.query(Account).filter(Account.customer_id == customer_id).all()
        finally:
            session.close()
    
    # Scheduled Call Operations
    def create_scheduled_call(self, customer_id: int, scheduled_time: Optional[datetime] = None, **kwargs) -> ScheduledCall:
        """Create a scheduled call"""
        session = self.get_session()
        try:
            scheduled_call = ScheduledCall(customer_id=customer_id, scheduled_time=scheduled_time, **kwargs)
            session.add(scheduled_call)
            session.commit()
            session.refresh(scheduled_call)
            return scheduled_call
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating scheduled call: {str(e)}")
        finally:
            session.close()
    
    def get_scheduled_calls(self, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[ScheduledCall]:
        """Get scheduled calls, optionally filtered by customer or status"""
        session = self.get_session()
        try:
            query = session.query(ScheduledCall)
            if customer_id:
                query = query.filter(ScheduledCall.customer_id == customer_id)
            if status:
                query = query.filter(ScheduledCall.status == status)
            return query.order_by(ScheduledCall.scheduled_time.asc()).all()
        finally:
            session.close()
    
    def update_scheduled_call(self, call_id: int, **kwargs) -> Optional[ScheduledCall]:
        """Update a scheduled call"""
        session = self.get_session()
        try:
            scheduled_call = session.query(ScheduledCall).filter(ScheduledCall.id == call_id).first()
            if scheduled_call:
                for key, value in kwargs.items():
                    if hasattr(scheduled_call, key):
                        setattr(scheduled_call, key, value)
                scheduled_call.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(scheduled_call)
            return scheduled_call
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error updating scheduled call: {str(e)}")
        finally:
            session.close()
    
    # Call Planning Script Operations
    def create_call_planning_script(self, customer_id: int, strategy_content: str, **kwargs) -> CallPlanningScript:
        """Create a call planning script"""
        session = self.get_session()
        try:
            script = CallPlanningScript(customer_id=customer_id, strategy_content=strategy_content, **kwargs)
            session.add(script)
            session.commit()
            session.refresh(script)
            return script
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating call planning script: {str(e)}")
        finally:
            session.close()
    
    def get_call_planning_scripts(self, customer_id: int, scheduled_call_id: Optional[int] = None) -> List[CallPlanningScript]:
        """Get call planning scripts for a customer"""
        session = self.get_session()
        try:
            query = session.query(CallPlanningScript).filter(CallPlanningScript.customer_id == customer_id)
            if scheduled_call_id:
                query = query.filter(CallPlanningScript.scheduled_call_id == scheduled_call_id)
            return query.order_by(CallPlanningScript.created_at.desc()).all()
        finally:
            session.close()
    
    def get_call_planning_script(self, script_id: int) -> Optional[CallPlanningScript]:
        """Get a call planning script by ID"""
        session = self.get_session()
        try:
            return session.query(CallPlanningScript).filter(CallPlanningScript.id == script_id).first()
        finally:
            session.close()
    
    # Planned Email Operations
    def create_planned_email(self, customer_id: int, communication_type: CommunicationType, content: str, **kwargs) -> PlannedEmail:
        """Create a planned email/SMS"""
        session = self.get_session()
        try:
            email = PlannedEmail(customer_id=customer_id, communication_type=communication_type, content=content, **kwargs)
            session.add(email)
            session.commit()
            session.refresh(email)
            return email
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error creating planned email: {str(e)}")
        finally:
            session.close()
    
    def get_planned_emails(self, customer_id: Optional[int] = None, status: Optional[str] = None) -> List[PlannedEmail]:
        """Get planned emails for a customer"""
        session = self.get_session()
        try:
            query = session.query(PlannedEmail)
            if customer_id:
                query = query.filter(PlannedEmail.customer_id == customer_id)
            if status:
                query = query.filter(PlannedEmail.status == status)
            return query.order_by(PlannedEmail.created_at.desc()).all()
        finally:
            session.close()
    
    def update_planned_email(self, email_id: int, **kwargs) -> Optional[PlannedEmail]:
        """Update a planned email"""
        session = self.get_session()
        try:
            email = session.query(PlannedEmail).filter(PlannedEmail.id == email_id).first()
            if email:
                for key, value in kwargs.items():
                    if hasattr(email, key):
                        setattr(email, key, value)
                email.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(email)
            return email
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error updating planned email: {str(e)}")
        finally:
            session.close()
    
    def delete_planned_email(self, email_id: int) -> bool:
        """Delete a planned email"""
        session = self.get_session()
        try:
            email = session.query(PlannedEmail).filter(PlannedEmail.id == email_id).first()
            if email:
                session.delete(email)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Error deleting planned email: {str(e)}")
        finally:
            session.close()
    
    # Utility Methods
    def get_customer_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get a comprehensive summary of a customer including debts and payment history"""
        customer = self.get_customer(customer_id)
        if not customer:
            return None
        
        debts = self.get_customer_debts(customer_id)
        total_debt = self.get_total_debt(customer_id)
        payments = self.get_payments(customer_id=customer_id)
        communications = self.get_communication_logs(customer_id, limit=10)
        
        return {
            'customer': customer,
            'debts': debts,
            'total_debt': total_debt,
            'debt_count': len(debts),
            'active_debt_count': len([d for d in debts if d.status == DebtStatus.ACTIVE]),
            'payments': payments,
            'payment_count': len(payments),
            'total_paid': sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED),
            'recent_communications': communications
        }


# Convenience function to get a database manager instance
def get_db_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """Get a database manager instance"""
    return DatabaseManager(database_url)


if __name__ == "__main__":
    # Example usage
    db = DatabaseManager()
    db.create_tables()
    
    # Create a sample customer
    customer = db.create_customer(
        first_name="John",
        last_name="Doe",
        phone_primary="+1234567890",
        email="john.doe@example.com",
        address_line1="123 Main St",
        city="New York",
        state="NY",
        zip_code="10001"
    )
    print(f"Created customer: {customer}")
    
    # Create a debt
    debt = db.create_debt(
        customer_id=customer.id,
        debt_type="credit_card",
        original_amount=10000.0,
        current_balance=10000.0,
        interest_rate=18.5,
        issue_date=datetime.utcnow(),
        due_date=datetime.utcnow()
    )
    print(f"Created debt: {debt}")
    
    # Get customer summary
    summary = db.get_customer_summary(customer.id)
    print(f"\nCustomer Summary:")
    print(f"Total Debt: ${summary['total_debt']:.2f}")
    print(f"Debt Count: {summary['debt_count']}")
