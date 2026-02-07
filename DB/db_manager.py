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
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    debts = relationship("Debt", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    communications = relationship("CommunicationLog", back_populates="customer", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    
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
        print("Database tables created successfully.")
    
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
