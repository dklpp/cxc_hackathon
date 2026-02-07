# Database Schema Documentation

## Overview
This document describes the database schema for the internal banking system used to track customer data and debts.

## Database Design

The database consists of 5 main tables designed to comprehensively track customer profiles, debts, payments, communications, and bank accounts.

---

## Table: `customers`
**Purpose**: Stores personal profile information for banking customers.

### Columns:
- **id** (Integer, Primary Key): Unique customer identifier
- **Personal Information**:
  - `first_name` (String, Required): Customer's first name
  - `last_name` (String, Required): Customer's last name
  - `middle_name` (String, Optional): Middle name or initial
  - `date_of_birth` (DateTime, Optional): Date of birth
  - `ssn` (String, Unique, Optional): Social Security Number (format: XXX-XX-XXXX)

- **Contact Information**:
  - `email` (String, Unique, Optional): Primary email address
  - `phone_primary` (String, Required): Primary phone number
  - `phone_secondary` (String, Optional): Secondary phone number

- **Address Information**:
  - `address_line1` (String, Optional): Street address
  - `address_line2` (String, Optional): Apartment, suite, etc.
  - `city` (String, Optional): City
  - `state` (String, Optional): State/Province
  - `zip_code` (String, Optional): ZIP/Postal code
  - `country` (String, Default: 'USA'): Country

- **Employment Information**:
  - `employer_name` (String, Optional): Current employer
  - `employment_status` (String, Optional): employed, unemployed, retired, etc.
  - `annual_income` (Float, Optional): Annual income in dollars

- **Account Status**:
  - `account_status` (String, Default: 'active'): active, closed, frozen, etc.
  - `credit_score` (Integer, Optional): Current credit score

- **Metadata**:
  - `created_at` (DateTime): Record creation timestamp
  - `updated_at` (DateTime): Last update timestamp
  - `notes` (Text, Optional): Additional notes about the customer


### Relationships:
- One-to-Many with `debts`
- One-to-Many with `payments`
- One-to-Many with `communication_logs`
- One-to-Many with `accounts`

---

## Table: `debts`
**Purpose**: Tracks individual debt records for customers.

### Columns:
- **id** (Integer, Primary Key): Unique debt identifier
- **customer_id** (Integer, Foreign Key → customers.id, Required): Reference to customer

- **Debt Information**:
  - `debt_type` (String, Required): Type of debt (credit_card, loan, mortgage, etc.)
  - `original_amount` (Float, Required): Original debt amount
  - `current_balance` (Float, Required): Current outstanding balance
  - `interest_rate` (Float, Optional): Annual percentage rate (APR)
  - `minimum_payment` (Float, Optional): Minimum monthly payment amount

- **Dates**:
  - `issue_date` (DateTime, Required): Date debt was issued/created
  - `due_date` (DateTime, Optional): Next payment due date
  - `last_payment_date` (DateTime, Optional): Date of last payment received

- **Status**:
  - `status` (Enum, Default: ACTIVE): Debt status
    - `ACTIVE`: Currently active debt
    - `PAID_OFF`: Debt has been fully paid
    - `DEFAULTED`: Customer has defaulted
    - `IN_COLLECTION`: Debt is in collection
    - `SETTLED`: Debt was settled for less than full amount
    - `WRITTEN_OFF`: Debt has been written off
  - `days_past_due` (Integer, Default: 0): Number of days past due

- **Account Information**:
  - `account_number` (String, Optional): Associated account number
  - `reference_number` (String, Optional): External reference number

- **Metadata**:
  - `created_at` (DateTime): Record creation timestamp
  - `updated_at` (DateTime): Last update timestamp
  - `notes` (Text, Optional): Additional notes about the debt

### Relationships:
- Many-to-One with `customers`
- One-to-Many with `payments`

---

## Table: `payments`
**Purpose**: Records payment history and transactions.

### Columns:
- **id** (Integer, Primary Key): Unique payment identifier
- **customer_id** (Integer, Foreign Key → customers.id, Required): Reference to customer
- **debt_id** (Integer, Foreign Key → debts.id, Required): Reference to debt being paid

- **Payment Information**:
  - `amount` (Float, Required): Payment amount
  - `payment_date` (DateTime, Required): Date payment was made/received
  - `payment_method` (String, Optional): Method of payment (credit_card, bank_transfer, check, cash, etc.)
  - `transaction_id` (String, Unique, Optional): External transaction identifier

- **Status**:
  - `status` (Enum, Default: PENDING): Payment status
    - `PENDING`: Payment is pending processing
    - `COMPLETED`: Payment successfully processed
    - `FAILED`: Payment failed
    - `REFUNDED`: Payment was refunded

- **Metadata**:
  - `created_at` (DateTime): Record creation timestamp
  - `notes` (Text, Optional): Additional notes about the payment

### Relationships:
- Many-to-One with `customers`
- Many-to-One with `debts`

### Business Logic:
- When a payment is created with status `COMPLETED`, the associated debt's `current_balance` is automatically reduced
- If balance reaches zero, debt status is automatically updated to `PAID_OFF`

---

## Table: `communication_logs`
**Purpose**: Tracks all customer communication interactions (calls, emails, SMS, etc.).

### Columns:
- **id** (Integer, Primary Key): Unique log identifier
- **customer_id** (Integer, Foreign Key → customers.id, Required): Reference to customer

- **Communication Details**:
  - `communication_type` (Enum, Required): Type of communication
    - `CALL`: Phone call
    - `EMAIL`: Email message
    - `SMS`: Text message
    - `LETTER`: Physical mail
    - `IN_PERSON`: In-person meeting
  - `direction` (String, Required): Direction of communication (inbound, outbound)
  - `duration_seconds` (Integer, Optional): Duration in seconds (for calls)

- **Contact Information Used**:
  - `contact_phone` (String, Optional): Phone number used for contact
  - `contact_email` (String, Optional): Email address used for contact

- **Outcome**:
  - `outcome` (String, Optional): Result of communication (payment_promised, no_answer, voicemail, etc.)
  - `notes` (Text, Optional): Detailed notes about the interaction

- **Metadata**:
  - `timestamp` (DateTime, Required): When the communication occurred
  - `agent_id` (String, Optional): ID of the agent/system that made the contact

### Relationships:
- Many-to-One with `customers`

---

## Table: `accounts`
**Purpose**: Stores bank account information for customers.

### Columns:
- **id** (Integer, Primary Key): Unique account identifier
- **customer_id** (Integer, Foreign Key → customers.id, Required): Reference to customer

- **Account Information**:
  - `account_type` (String, Required): Type of account (checking, savings, credit_card, etc.)
  - `account_number` (String, Unique, Required): Account number (stored securely)
  - `routing_number` (String, Optional): Bank routing number
  - `bank_name` (String, Optional): Name of the bank/institution

- **Status**:
  - `is_active` (Boolean, Default: True): Whether account is currently active
  - `is_primary` (Boolean, Default: False): Whether this is the primary account

- **Metadata**:
  - `created_at` (DateTime): Record creation timestamp
  - `updated_at` (DateTime): Last update timestamp
  - `notes` (Text, Optional): Additional notes about the account

### Relationships:
- Many-to-One with `customers`

---

## Database Schema Design Rationale

### Key Design Decisions:

1. **Separation of Concerns**: 
   - Customer profile data is separate from debt records, allowing multiple debts per customer
   - Payment history is tracked separately for audit and reporting purposes

2. **Status Tracking**:
   - Debt status uses an enum to ensure data integrity and consistent state management
   - Payment status allows tracking of pending/failed transactions

3. **Communication Logging**:
   - Comprehensive logging of all customer interactions for compliance and collection purposes
   - Supports multiple communication channels (calls, emails, SMS, etc.)

4. **Flexibility**:
   - Optional fields allow for gradual data collection
   - Notes fields provide flexibility for additional information

5. **Audit Trail**:
   - `created_at` and `updated_at` timestamps on all tables
   - Payment history provides complete audit trail

6. **Data Integrity**:
   - Foreign key constraints ensure referential integrity
   - Unique constraints prevent duplicate records (SSN, email, account numbers)

---

## Usage Examples

### Creating a Customer with Debt:
```python
from DB.db_manager import DatabaseManager, DebtStatus
from datetime import datetime

db = DatabaseManager()
db.create_tables()

# Create customer
customer = db.create_customer(
    first_name="Jane",
    last_name="Smith",
    phone_primary="+1987654321",
    email="jane.smith@example.com",
    address_line1="456 Oak Ave",
    city="Los Angeles",
    state="CA",
    zip_code="90001"
)

# Create debt
debt = db.create_debt(
    customer_id=customer.id,
    debt_type="credit_card",
    original_amount=5000.0,
    current_balance=5000.0,
    interest_rate=19.99,
    minimum_payment=150.0,
    issue_date=datetime(2024, 1, 15),
    due_date=datetime(2025, 2, 15),
    status=DebtStatus.ACTIVE
)
```

### Recording a Payment:
```python
from DB.db_manager import PaymentStatus

payment = db.create_payment(
    customer_id=customer.id,
    debt_id=debt.id,
    amount=200.0,
    payment_date=datetime.utcnow(),
    payment_method="bank_transfer",
    status=PaymentStatus.COMPLETED
)
# Debt balance is automatically updated to $4800.00
```

### Logging Communication:
```python
from DB.db_manager import CommunicationType

log = db.log_communication(
    customer_id=customer.id,
    communication_type=CommunicationType.CALL,
    direction="outbound",
    duration_seconds=180,
    contact_phone="+1987654321",
    outcome="payment_promised",
    notes="Customer agreed to make payment by end of week",
    agent_id="agent_001"
)
```

### Getting Customer Summary:
```python
summary = db.get_customer_summary(customer.id)
print(f"Total Debt: ${summary['total_debt']:.2f}")
print(f"Active Debts: {summary['active_debt_count']}")
print(f"Total Paid: ${summary['total_paid']:.2f}")
```

---

## Security Considerations

1. **Sensitive Data**: 
   - SSN and account numbers should be encrypted at rest in production
   - Consider using encryption for PII fields

2. **Access Control**:
   - Implement role-based access control (RBAC) for database access
   - Use parameterized queries (SQLAlchemy handles this automatically)

3. **Audit Logging**:
   - All customer interactions are logged in `communication_logs`
   - Payment history provides complete audit trail

4. **Data Retention**:
   - Consider implementing data retention policies
   - Archive old records rather than deleting for compliance

---

## Future Enhancements

Potential additions to consider:
- Payment plans/schedules table
- Interest calculation history
- Credit report integration
- Document storage references
- Legal action tracking
- Settlement agreements
