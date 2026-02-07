"""
Example: How to populate customer data from JSON into the database

This example demonstrates how to parse JSON customer data and create
database records using the DatabaseManager.
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager, DebtStatus, PaymentStatus, CommunicationType


# Example JSON data structure for a customer with debts
example_customer_json = """
{
    "customer": {
        "first_name": "John",
        "last_name": "Doe",
        "middle_name": "Michael",
        "date_of_birth": "1985-03-15",
        "ssn": "123-45-6789",
        "email": "john.doe@example.com",
        "phone_primary": "+1234567890",
        "phone_secondary": "+1234567891",
        "address_line1": "123 Main Street",
        "address_line2": "Apt 4B",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "country": "USA",
        "employer_name": "Tech Corp Inc",
        "employment_status": "employed",
        "annual_income": 75000.0,
        "account_status": "active",
        "credit_score": 680,
        "notes": "Customer prefers email communication"
    },
    "debts": [
        {
            "debt_type": "credit_card",
            "original_amount": 10000.0,
            "current_balance": 8500.0,
            "interest_rate": 18.5,
            "minimum_payment": 250.0,
            "issue_date": "2023-01-15",
            "due_date": "2025-03-15",
            "last_payment_date": "2024-12-01",
            "status": "active",
            "days_past_due": 0,
            "account_number": "CC-1234-5678",
            "reference_number": "REF-2023-001",
            "notes": "Primary credit card account"
        },
        {
            "debt_type": "personal_loan",
            "original_amount": 5000.0,
            "current_balance": 3200.0,
            "interest_rate": 12.0,
            "minimum_payment": 200.0,
            "issue_date": "2023-06-01",
            "due_date": "2025-06-01",
            "last_payment_date": "2024-11-15",
            "status": "active",
            "days_past_due": 15,
            "account_number": "PL-9876-5432",
            "reference_number": "REF-2023-002",
            "notes": "Personal loan for home improvement"
        }
    ],
    "payments": [
        {
            "debt_type": "credit_card",
            "amount": 500.0,
            "payment_date": "2024-12-01",
            "payment_method": "bank_transfer",
            "transaction_id": "TXN-2024-12-001",
            "status": "completed",
            "notes": "Monthly payment"
        },
        {
            "debt_type": "personal_loan",
            "amount": 200.0,
            "payment_date": "2024-11-15",
            "payment_method": "bank_transfer",
            "transaction_id": "TXN-2024-11-015",
            "status": "completed",
            "notes": "Regular payment"
        }
    ],
    "accounts": [
        {
            "account_type": "checking",
            "account_number": "CHK-1111-2222",
            "routing_number": "021000021",
            "bank_name": "First National Bank",
            "is_active": true,
            "is_primary": true,
            "notes": "Primary checking account"
        },
        {
            "account_type": "savings",
            "account_number": "SAV-3333-4444",
            "routing_number": "021000021",
            "bank_name": "First National Bank",
            "is_active": true,
            "is_primary": false,
            "notes": "Savings account"
        }
    ],
    "communications": [
        {
            "communication_type": "call",
            "direction": "outbound",
            "duration_seconds": 300,
            "contact_phone": "+1234567890",
            "outcome": "payment_promised",
            "notes": "Customer agreed to make payment by end of month",
            "timestamp": "2024-12-15T10:30:00",
            "agent_id": "agent_001"
        },
        {
            "communication_type": "email",
            "direction": "outbound",
            "contact_email": "john.doe@example.com",
            "outcome": "sent",
            "notes": "Sent payment reminder email",
            "timestamp": "2024-12-10T09:00:00",
            "agent_id": "system"
        }
    ]
}
"""


def parse_date(date_string):
    """Parse date string from JSON to datetime object"""
    if not date_string:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except:
        try:
            # Try common date formats
            return datetime.strptime(date_string, "%Y-%m-%d")
        except:
            return None


def create_customer_from_json(db: DatabaseManager, json_data: dict):
    """
    Create a customer record and all related data from JSON structure.
    
    Args:
        db: DatabaseManager instance
        json_data: Dictionary containing customer data
    """
    customer_data = json_data.get('customer', {})
    
    # Parse date of birth
    if 'date_of_birth' in customer_data:
        customer_data['date_of_birth'] = parse_date(customer_data['date_of_birth'])
    
    # Create customer record
    print("Creating customer record...")
    customer = db.create_customer(**customer_data)
    print(f"✓ Created customer: {customer.first_name} {customer.last_name} (ID: {customer.id})")
    
    # Create debts
    debts_map = {}  # Map debt_type to debt_id for payment matching
    if 'debts' in json_data:
        print("\nCreating debt records...")
        for debt_data in json_data['debts']:
            # Parse dates
            for date_field in ['issue_date', 'due_date', 'last_payment_date']:
                if date_field in debt_data:
                    debt_data[date_field] = parse_date(debt_data[date_field])
            
            # Convert status string to enum
            if 'status' in debt_data:
                status_str = debt_data['status'].upper()
                debt_data['status'] = DebtStatus[status_str] if hasattr(DebtStatus, status_str) else DebtStatus.ACTIVE
            
            # Create debt
            debt = db.create_debt(customer_id=customer.id, **debt_data)
            debts_map[debt_data['debt_type']] = debt.id
            print(f"✓ Created debt: {debt.debt_type} - ${debt.current_balance:.2f} (ID: {debt.id})")
    
    # Create payments
    if 'payments' in json_data:
        print("\nCreating payment records...")
        for payment_data in json_data['payments']:
            # Parse payment date
            if 'payment_date' in payment_data:
                payment_data['payment_date'] = parse_date(payment_data['payment_date'])
            
            # Convert status string to enum
            if 'status' in payment_data:
                status_str = payment_data['status'].upper()
                payment_data['status'] = PaymentStatus[status_str] if hasattr(PaymentStatus, status_str) else PaymentStatus.PENDING
            
            # Find debt_id by debt_type
            debt_type = payment_data.pop('debt_type', None)
            if debt_type and debt_type in debts_map:
                debt_id = debts_map[debt_type]
                payment = db.create_payment(
                    customer_id=customer.id,
                    debt_id=debt_id,
                    **payment_data
                )
                print(f"✓ Created payment: ${payment.amount:.2f} for {debt_type} (ID: {payment.id})")
            else:
                print(f"⚠ Warning: Could not find debt for payment type '{debt_type}'")
    
    # Create accounts
    if 'accounts' in json_data:
        print("\nCreating account records...")
        for account_data in json_data['accounts']:
            account = db.create_account(customer_id=customer.id, **account_data)
            print(f"✓ Created account: {account.account_type} - {account.account_number[:4]}*** (ID: {account.id})")
    
    # Create communication logs
    if 'communications' in json_data:
        print("\nCreating communication logs...")
        for comm_data in json_data['communications']:
            # Parse timestamp
            if 'timestamp' in comm_data:
                comm_data['timestamp'] = parse_date(comm_data['timestamp'])
            
            # Convert communication_type string to enum
            if 'communication_type' in comm_data:
                comm_type_str = comm_data['communication_type'].upper()
                comm_data['communication_type'] = CommunicationType[comm_type_str] if hasattr(CommunicationType, comm_type_str) else CommunicationType.CALL
            
            log = db.log_communication(customer_id=customer.id, **comm_data)
            print(f"✓ Created communication log: {log.communication_type.value} - {log.direction} (ID: {log.id})")
    
    return customer


def main():
    """Main example function"""
    # Initialize database
    print("Initializing database...")
    db = DatabaseManager()
    db.create_tables()
    print("✓ Database initialized\n")
    
    # Parse JSON data
    print("Parsing JSON data...")
    json_data = json.loads(example_customer_json)
    print("✓ JSON parsed\n")
    
    # Create customer from JSON
    print("=" * 60)
    print("CREATING CUSTOMER FROM JSON")
    print("=" * 60)
    customer = create_customer_from_json(db, json_data)
    
    # Display summary
    print("\n" + "=" * 60)
    print("CUSTOMER SUMMARY")
    print("=" * 60)
    summary = db.get_customer_summary(customer.id)
    
    print(f"\nCustomer: {summary['customer'].first_name} {summary['customer'].last_name}")
    print(f"Phone: {summary['customer'].phone_primary}")
    print(f"Email: {summary['customer'].email}")
    print(f"Total Debt: ${summary['total_debt']:.2f}")
    print(f"Active Debts: {summary['active_debt_count']}")
    print(f"Total Paid: ${summary['total_paid']:.2f}")
    print(f"Payment Count: {summary['payment_count']}")
    print(f"Recent Communications: {len(summary['recent_communications'])}")
    
    print("\n" + "-" * 60)
    print("Debt Details:")
    for debt in summary['debts']:
        print(f"  • {debt.debt_type}: ${debt.current_balance:.2f} (Status: {debt.status.value})")
    
    print("\n" + "-" * 60)
    print("Recent Payments:")
    for payment in summary['payments'][:5]:  # Show last 5 payments
        print(f"  • ${payment.amount:.2f} on {payment.payment_date.strftime('%Y-%m-%d')} ({payment.status.value})")
    
    print("\n" + "-" * 60)
    print("Recent Communications:")
    for comm in summary['recent_communications'][:5]:  # Show last 5 communications
        print(f"  • {comm.communication_type.value} ({comm.direction}) on {comm.timestamp.strftime('%Y-%m-%d %H:%M')}")
        if comm.outcome:
            print(f"    Outcome: {comm.outcome}")


# Example: Loading from a JSON file
def load_customer_from_file(db: DatabaseManager, file_path: str):
    """
    Load customer data from a JSON file and create database records.
    
    Args:
        db: DatabaseManager instance
        file_path: Path to JSON file
    """
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    
    return create_customer_from_json(db, json_data)


# Example: Loading multiple customers from JSON array
def load_multiple_customers_from_json(db: DatabaseManager, json_data: list):
    """
    Load multiple customers from a JSON array.
    
    Args:
        db: DatabaseManager instance
        json_data: List of customer dictionaries
    """
    customers = []
    for customer_json in json_data:
        customer = create_customer_from_json(db, customer_json)
        customers.append(customer)
    return customers


if __name__ == "__main__":
    main()
