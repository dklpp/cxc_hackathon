"""
Update Customer Communication Preferences

This script analyzes all customers and updates their preferred_communication_method
field based on:
1. Explicit preferences mentioned in notes
2. Communication history (most successful channel)
3. Default logic based on customer profile
"""

import sys
import os
from datetime import datetime
from collections import Counter
from typing import Optional, Dict
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager, CommunicationType


def parse_preference_from_notes(notes: Optional[str]) -> Optional[CommunicationType]:
    """
    Parse communication preference from customer notes.
    
    Returns CommunicationType if found, None otherwise.
    """
    if not notes:
        return None
    
    notes_lower = notes.lower()
    
    # Check for explicit preferences
    if "prefer" in notes_lower or "preference" in notes_lower:
        if "email" in notes_lower:
            return CommunicationType.EMAIL
        elif "phone" in notes_lower or "call" in notes_lower:
            return CommunicationType.CALL
        elif "sms" in notes_lower or "text" in notes_lower:
            return CommunicationType.SMS
        elif "letter" in notes_lower or "mail" in notes_lower:
            return CommunicationType.LETTER
    
    # Check for digital/tech-savvy indicators (likely prefer email/SMS)
    digital_indicators = ["digital", "tech-savvy", "online", "app", "mobile"]
    if any(indicator in notes_lower for indicator in digital_indicators):
        return CommunicationType.EMAIL
    
    # Check for phone preference indicators
    phone_indicators = ["phone", "call", "speak", "talk"]
    if any(indicator in notes_lower for indicator in phone_indicators):
        return CommunicationType.CALL
    
    return None


def analyze_communication_history(db: DatabaseManager, customer_id: int) -> Optional[CommunicationType]:
    """
    Analyze communication history to determine most successful channel.
    
    Returns CommunicationType of the most successful channel, or None if no history.
    """
    communications = db.get_communication_logs(customer_id, limit=50)
    
    if not communications:
        return None
    
    # Positive outcomes that indicate successful communication
    positive_outcomes = [
        "payment_promised", "payment_made", "agreed_to_pay", 
        "payment_plan_setup", "resolved", "answered", "responded"
    ]
    
    # Count successful communications by type
    successful_by_type = Counter()
    total_by_type = Counter()
    
    for comm in communications:
        comm_type = comm.communication_type
        total_by_type[comm_type] += 1
        
        # Check for positive outcomes
        if comm.outcome:
            outcome_lower = comm.outcome.lower()
            if any(po in outcome_lower for po in positive_outcomes):
                successful_by_type[comm_type] += 1
        
        # Inbound communications are generally positive
        if comm.direction == "inbound":
            successful_by_type[comm_type] += 0.5
    
    if not total_by_type:
        return None
    
    # Calculate success rate for each type
    success_rates = {}
    for comm_type, total in total_by_type.items():
        successful = successful_by_type.get(comm_type, 0)
        success_rates[comm_type] = successful / total if total > 0 else 0
    
    # Return the type with highest success rate (if above threshold)
    if success_rates:
        best_type = max(success_rates.items(), key=lambda x: x[1])
        # Only use if success rate is reasonable (at least 30%)
        if best_type[1] >= 0.3:
            return best_type[0]
    
    # Fallback: return most used type
    if total_by_type:
        most_used = total_by_type.most_common(1)[0][0]
        return most_used
    
    return None


def determine_default_preference(customer) -> CommunicationType:
    """
    Determine default communication preference based on customer profile.
    """
    # If customer has email but no phone preference, prefer email
    if customer.email and not customer.phone_secondary:
        return CommunicationType.EMAIL
    
    # If customer has good credit score, they might prefer digital
    if customer.credit_score and customer.credit_score > 700:
        return CommunicationType.EMAIL
    
    # Employment status can indicate preference
    if customer.employment_status:
        emp_status = customer.employment_status.lower()
        if emp_status in ["employed", "self-employed"]:
            # Working professionals often prefer email
            return CommunicationType.EMAIL
    
    # Default to phone call (most personal and effective for debt collection)
    return CommunicationType.CALL


def update_customer_preference(db: DatabaseManager, customer_id: int, 
                               preference: CommunicationType, 
                               reason: str, dry_run: bool = False) -> bool:
    """
    Update customer's preferred communication method.
    
    Returns True if updated, False if already set or error.
    """
    customer = db.get_customer(customer_id)
    if not customer:
        print(f"  ✗ Customer {customer_id} not found")
        return False
    
    # Skip if already set (unless dry_run, then just report)
    if customer.preferred_communication_method and not dry_run:
        print(f"  ⚠ Customer {customer_id} already has preference: {customer.preferred_communication_method.value}")
        return False
    
    if dry_run:
        print(f"  [DRY RUN] Would set {customer.first_name} {customer.last_name} (ID: {customer_id}) "
              f"to {preference.value} - Reason: {reason}")
        return True
    
    try:
        db.update_customer(customer_id, preferred_communication_method=preference)
        print(f"  ✓ Updated {customer.first_name} {customer.last_name} (ID: {customer_id}) "
              f"→ {preference.value} ({reason})")
        return True
    except Exception as e:
        print(f"  ✗ Error updating customer {customer_id}: {e}")
        return False


def check_column_exists(db: DatabaseManager) -> bool:
    """Check if preferred_communication_method column exists"""
    session = db.get_session()
    try:
        from sqlalchemy import text
        result = session.execute(text("SELECT preferred_communication_method FROM customers LIMIT 1"))
        return True
    except Exception:
        return False
    finally:
        session.close()


def update_all_customers(dry_run: bool = False, 
                        overwrite_existing: bool = False) -> Dict[str, int]:
    """
    Update all customers with preferred communication methods.
    
    Args:
        dry_run: If True, only show what would be updated without making changes
        overwrite_existing: If True, update even if preference is already set
    
    Returns:
        Dictionary with statistics about updates
    """
    db = DatabaseManager()
    
    print("=" * 80)
    print("UPDATING CUSTOMER COMMUNICATION PREFERENCES")
    print("=" * 80)
    if dry_run:
        print("⚠ DRY RUN MODE - No changes will be made\n")
    print()
    
    # Check if column exists
    if not check_column_exists(db):
        print("✗ ERROR: Column 'preferred_communication_method' does not exist!")
        print()
        print("Please recreate tables to add the new column:")
        print("  python -c \"from DB.db_manager import DatabaseManager, Base; db = DatabaseManager(); Base.metadata.drop_all(bind=db.engine); Base.metadata.create_all(bind=db.engine)\"")
        print()
        print("Then reload your data:")
        print("  uv run python DB/db_usage_example.py")
        print()
        return {"error": "Column does not exist"}
    
    # Get all customers
    customers = db.list_customers(limit=1000)  # Adjust limit if needed
    print(f"Found {len(customers)} customers to process\n")
    
    stats = {
        "total": len(customers),
        "updated": 0,
        "skipped": 0,
        "from_notes": 0,
        "from_history": 0,
        "from_default": 0,
        "already_set": 0,
        "errors": 0
    }
    
    for customer in customers:
        customer_id = customer.id
        name = f"{customer.first_name} {customer.last_name}"
        
        print(f"Processing: {name} (ID: {customer_id})")
        
        # Skip if already set and not overwriting
        if customer.preferred_communication_method and not overwrite_existing and not dry_run:
            print(f"  ⚠ Already set to: {customer.preferred_communication_method.value}")
            stats["already_set"] += 1
            stats["skipped"] += 1
            print()
            continue
        
        preference = None
        reason = ""
        
        # Method 1: Check notes for explicit preference
        preference = parse_preference_from_notes(customer.notes)
        if preference:
            reason = "parsed from notes"
            stats["from_notes"] += 1
        else:
            # Method 2: Analyze communication history
            preference = analyze_communication_history(db, customer_id)
            if preference:
                reason = "based on communication history"
                stats["from_history"] += 1
        
        # Method 3: Use default logic
        if not preference:
            preference = determine_default_preference(customer)
            reason = "default logic (profile-based)"
            stats["from_default"] += 1
        
        # Update the customer
        if update_customer_preference(db, customer_id, preference, reason, dry_run):
            stats["updated"] += 1
        else:
            if not dry_run:
                stats["errors"] += 1
            stats["skipped"] += 1
        
        print()
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total customers: {stats['total']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Already had preference: {stats['already_set']}")
    print(f"Errors: {stats['errors']}")
    print()
    print("Update sources:")
    print(f"  From notes: {stats['from_notes']}")
    print(f"  From communication history: {stats['from_history']}")
    print(f"  From default logic: {stats['from_default']}")
    
    return stats


def main():
    """Main function with command-line argument support"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update customer communication preferences"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Update even if preference is already set"
    )
    
    args = parser.parse_args()
    
    stats = update_all_customers(
        dry_run=args.dry_run,
        overwrite_existing=args.overwrite
    )
    
    if args.dry_run:
        print("\n⚠ This was a dry run. Use without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
