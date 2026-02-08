"""
Populate Contact Time Preferences for Existing Customers

This script assigns preferred_contact_time and preferred_contact_days
to existing customers based on their profile and communication patterns.
"""

import sys
import os
from datetime import datetime
from typing import Optional, Dict
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager


def determine_preferred_time(customer) -> Optional[str]:
    """Determine preferred contact time based on customer profile"""
    employment_status = (customer.employment_status or "").lower()
    
    # Retired customers - prefer mornings/early afternoons
    if "retired" in employment_status or "retirement" in employment_status:
        return random.choice([
            "9 AM - 12 PM",
            "10 AM - 2 PM",
            "Morning hours",
            "9 AM - 11 AM"
        ])
    
    # Unemployed - prefer mid-day
    elif "unemployed" in employment_status or "unemployment" in employment_status:
        return random.choice([
            "10 AM - 2 PM",
            "11 AM - 3 PM",
            "Afternoon",
            "Any time"
        ])
    
    # Employed - prefer evenings or early mornings
    elif "employed" in employment_status or "employment" in employment_status or customer.employer_name:
        return random.choice([
            "5 PM - 7 PM",
            "6 PM - 8 PM",
            "Evenings",
            "8 AM - 9 AM"
        ])
    
    # Default based on age if available
    if customer.date_of_birth:
        age = (datetime.now() - customer.date_of_birth).days // 365
        if age >= 65:
            return random.choice([
                "10 AM - 12 PM",
                "Morning hours",
                "9 AM - 11 AM"
            ])
        elif age < 30:
            return random.choice([
                "Evenings",
                "5 PM - 8 PM",
                "6 PM - 9 PM"
            ])
    
    # Default: business hours
    return random.choice([
        "9 AM - 5 PM",
        "10 AM - 4 PM",
        "Business hours"
    ])


def determine_preferred_days(customer) -> Optional[str]:
    """Determine preferred contact days based on customer profile"""
    employment_status = (customer.employment_status or "").lower()
    
    # Retired/unemployed - any day
    if "retired" in employment_status or "retirement" in employment_status:
        return random.choice([
            "Any day",
            "Weekdays",
            "Monday - Friday"
        ])
    
    elif "unemployed" in employment_status or "unemployment" in employment_status:
        return random.choice([
            "Any day",
            "Weekdays",
            "All days"
        ])
    
    # Employed - prefer weekdays
    elif "employed" in employment_status or "employment" in employment_status or customer.employer_name:
        return random.choice([
            "Weekdays",
            "Monday - Friday",
            "Weekdays only"
        ])
    
    # Default: weekdays
    return "Weekdays"


def update_all_customers(dry_run: bool = True, overwrite_existing: bool = False) -> Dict[str, int]:
    """
    Update all customers with preferred contact time and days.
    
    Args:
        dry_run: If True, only show what would be updated without making changes
        overwrite_existing: If True, overwrite existing preferences
    
    Returns:
        Dictionary with statistics about updates
    """
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        from db_manager import Customer
        
        # Get all customers
        customers = session.query(Customer).all()
        
        stats = {
            "total_customers": len(customers),
            "updated": 0,
            "skipped": 0,
            "already_set": 0
        }
        
        print(f"Found {len(customers)} customers")
        print("=" * 60)
        
        for customer in customers:
            # Check if preferences already exist
            has_time = customer.preferred_contact_time is not None and customer.preferred_contact_time.strip() != ""
            has_days = customer.preferred_contact_days is not None and customer.preferred_contact_days.strip() != ""
            
            if has_time and has_days and not overwrite_existing:
                stats["already_set"] += 1
                if dry_run:
                    print(f"⏭  {customer.first_name} {customer.last_name} (ID: {customer.id}) - Already has preferences")
                continue
            
            # Determine preferences
            preferred_time = determine_preferred_time(customer)
            preferred_days = determine_preferred_days(customer)
            
            if dry_run:
                print(f"📝 {customer.first_name} {customer.last_name} (ID: {customer.id})")
                print(f"   Time: {preferred_time}")
                print(f"   Days: {preferred_days}")
                print()
            else:
                # Update customer
                customer.preferred_contact_time = preferred_time
                customer.preferred_contact_days = preferred_days
                session.commit()
                stats["updated"] += 1
                print(f"✓ Updated {customer.first_name} {customer.last_name} (ID: {customer.id})")
        
        if dry_run:
            print("=" * 60)
            print("DRY RUN - No changes made")
            print(f"Would update: {stats['total_customers'] - stats['already_set']} customers")
            print(f"Already have preferences: {stats['already_set']} customers")
        else:
            print("=" * 60)
            print(f"✓ Updated {stats['updated']} customers")
            print(f"⏭  Skipped {stats['already_set']} customers (already have preferences)")
        
        return stats
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate contact time preferences for customers")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually update the database (default is dry-run)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing preferences"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("POPULATE CONTACT TIME PREFERENCES")
    print("=" * 60)
    print()
    
    if not args.execute:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print("   Use --execute to actually update the database")
        print()
    
    stats = update_all_customers(dry_run=not args.execute, overwrite_existing=args.overwrite)
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total customers: {stats['total_customers']}")
    if args.execute:
        print(f"Updated: {stats['updated']}")
        print(f"Skipped (already set): {stats['already_set']}")
    else:
        print(f"Would update: {stats['total_customers'] - stats['already_set']}")
        print(f"Already have preferences: {stats['already_set']}")


if __name__ == "__main__":
    main()
