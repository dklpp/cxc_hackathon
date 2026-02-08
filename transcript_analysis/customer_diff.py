"""
Customer Data Diff Utility

Compares information extracted from call transcripts against
existing customer database records and proposes updates.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ChangeType(Enum):
    """Type of change detected"""
    UPDATE = "update"           # Field value changed
    NEW_INFO = "new_info"       # New information not in DB
    CONFIRMATION = "confirm"    # Transcript confirms existing data
    CONFLICT = "conflict"       # Transcript conflicts with DB


@dataclass
class FieldDiff:
    """Represents a difference in a single field"""
    field_name: str
    change_type: ChangeType
    current_value: Any
    new_value: Any
    confidence: str  # high, medium, low
    source: str      # where in transcript this came from
    notes: str = ""


@dataclass
class CustomerDiffReport:
    """Complete diff report for a customer"""
    customer_id: str
    customer_name: str
    transcript_id: str
    analysis_timestamp: str
    changes: List[FieldDiff]
    summary: str
    recommended_actions: List[str]

    def to_dict(self) -> Dict:
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "transcript_id": self.transcript_id,
            "analysis_timestamp": self.analysis_timestamp,
            "total_changes": len(self.changes),
            "changes": [
                {
                    "field": c.field_name,
                    "change_type": c.change_type.value,
                    "current_value": c.current_value,
                    "new_value": c.new_value,
                    "confidence": c.confidence,
                    "source": c.source,
                    "notes": c.notes
                }
                for c in self.changes
            ],
            "summary": self.summary,
            "recommended_actions": self.recommended_actions
        }


def load_customer_json(file_path: str) -> Dict[str, Any]:
    """Load customer data from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def compare_customer_data(
    transcript_analysis: Dict[str, Any],
    customer_data: Dict[str, Any],
    transcript_id: Optional[str] = None
) -> CustomerDiffReport:
    """
    Compare transcript analysis results against customer database.

    Args:
        transcript_analysis: Output from TranscriptAnalyzer
        customer_data: Customer JSON data from DB
        transcript_id: Optional transcript/call ID

    Returns:
        CustomerDiffReport with all detected differences
    """
    changes: List[FieldDiff] = []
    customer = customer_data.get("customer", {})
    debts = customer_data.get("debts", [])

    # Extract info from transcript
    extracted = transcript_analysis.get("customer_info_extracted", {})
    payment_info = transcript_analysis.get("payment_info", {})
    recommendations = transcript_analysis.get("recommendations", {})
    call_outcome = transcript_analysis.get("call_outcome", {})

    # --- Compare Employment Status ---
    new_employment = extracted.get("employment_status_update")
    if new_employment:
        current_employment = customer.get("employment_status", "unknown")
        if new_employment.lower() != current_employment.lower():
            changes.append(FieldDiff(
                field_name="customer.employment_status",
                change_type=ChangeType.UPDATE,
                current_value=current_employment,
                new_value=new_employment,
                confidence="medium",
                source="customer_info_extracted.employment_status_update",
                notes="Customer mentioned employment change during call"
            ))

    # --- Check for Life Events ---
    life_events = extracted.get("life_events_mentioned", [])
    if life_events:
        current_notes = customer.get("notes", "")
        new_events = [e for e in life_events if e.lower() not in current_notes.lower()]
        if new_events:
            changes.append(FieldDiff(
                field_name="customer.notes",
                change_type=ChangeType.NEW_INFO,
                current_value=current_notes,
                new_value=f"{current_notes} | Life events: {', '.join(new_events)}",
                confidence="high",
                source="customer_info_extracted.life_events_mentioned",
                notes=f"New life events detected: {', '.join(new_events)}"
            ))

    # --- Check Financial Hardship ---
    hardship_indicators = extracted.get("financial_hardship_indicators", [])
    if hardship_indicators:
        changes.append(FieldDiff(
            field_name="customer.financial_hardship_flag",
            change_type=ChangeType.NEW_INFO,
            current_value=None,
            new_value=hardship_indicators,
            confidence="medium",
            source="customer_info_extracted.financial_hardship_indicators",
            notes="Customer showing signs of financial hardship"
        ))

    # --- Check Reason for Non-Payment ---
    reason = extracted.get("reason_for_non_payment")
    if reason:
        # Check if this is different from existing notes
        current_notes = customer.get("notes", "")
        if reason.lower() not in current_notes.lower():
            changes.append(FieldDiff(
                field_name="customer.notes",
                change_type=ChangeType.NEW_INFO,
                current_value=current_notes,
                new_value=f"{current_notes} | Non-payment reason: {reason}",
                confidence="high",
                source="customer_info_extracted.reason_for_non_payment"
            ))

    # --- Compare Payment Promises ---
    if payment_info.get("payment_promised"):
        payment_details = {
            "amount": payment_info.get("payment_amount"),
            "date": payment_info.get("payment_date"),
            "method": payment_info.get("payment_method")
        }
        changes.append(FieldDiff(
            field_name="debts[0].promised_payment",
            change_type=ChangeType.NEW_INFO,
            current_value=None,
            new_value=payment_details,
            confidence="high",
            source="payment_info",
            notes="Customer promised payment during call"
        ))

    # --- Check Payment Plan ---
    plan_details = payment_info.get("payment_plan_details", {})
    if plan_details.get("monthly_amount"):
        changes.append(FieldDiff(
            field_name="debts[0].payment_plan",
            change_type=ChangeType.NEW_INFO,
            current_value=None,
            new_value=plan_details,
            confidence="high",
            source="payment_info.payment_plan_details",
            notes="Payment plan agreed during call"
        ))

    # --- Profile Type Update ---
    new_profile = recommendations.get("profile_type_update")
    if new_profile:
        changes.append(FieldDiff(
            field_name="customer.profile_type",
            change_type=ChangeType.UPDATE,
            current_value=customer_data.get("profile_type", "unknown"),
            new_value=new_profile,
            confidence="medium",
            source="recommendations.profile_type_update",
            notes="AI recommends profile type change based on call"
        ))

    # --- Risk Level Update ---
    new_risk = recommendations.get("risk_level_update")
    if new_risk:
        changes.append(FieldDiff(
            field_name="customer.risk_level",
            change_type=ChangeType.UPDATE,
            current_value=customer_data.get("risk_level", "unknown"),
            new_value=new_risk,
            confidence="medium",
            source="recommendations.risk_level_update",
            notes="Risk level updated based on call analysis"
        ))

    # --- Days Past Due Update ---
    # If payment was made or promised, days_past_due should be updated
    if call_outcome.get("primary_outcome") == "payment_made":
        if debts:
            changes.append(FieldDiff(
                field_name="debts[0].days_past_due",
                change_type=ChangeType.UPDATE,
                current_value=debts[0].get("days_past_due", 0),
                new_value=0,
                confidence="high",
                source="call_outcome.primary_outcome",
                notes="Payment confirmed during call"
            ))

    # --- Build Summary ---
    summary = _build_summary(changes, extracted, call_outcome)

    # --- Recommended Actions ---
    actions = _build_recommended_actions(changes, recommendations, call_outcome)

    return CustomerDiffReport(
        customer_id=str(transcript_analysis.get("call_metadata", {}).get("customer_id", "unknown")),
        customer_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
        transcript_id=transcript_id or transcript_analysis.get("call_metadata", {}).get("call_id", "unknown"),
        analysis_timestamp=datetime.now().isoformat(),
        changes=changes,
        summary=summary,
        recommended_actions=actions
    )


def _build_summary(changes: List[FieldDiff], extracted: Dict, call_outcome: Dict) -> str:
    """Build human-readable summary"""
    if not changes:
        return "No significant changes detected between transcript and customer database."

    parts = []
    parts.append(f"Found {len(changes)} potential update(s) from call analysis.")

    update_count = sum(1 for c in changes if c.change_type == ChangeType.UPDATE)
    new_info_count = sum(1 for c in changes if c.change_type == ChangeType.NEW_INFO)

    if update_count:
        parts.append(f"{update_count} field(s) need updating.")
    if new_info_count:
        parts.append(f"{new_info_count} new piece(s) of information to add.")

    situation = extracted.get("current_situation")
    if situation:
        parts.append(f"Customer situation: {situation}")

    return " ".join(parts)


def _build_recommended_actions(changes: List[FieldDiff], recommendations: Dict, call_outcome: Dict) -> List[str]:
    """Build list of recommended actions"""
    actions = []

    for change in changes:
        if change.change_type == ChangeType.UPDATE:
            actions.append(f"Update {change.field_name}: '{change.current_value}' → '{change.new_value}'")
        elif change.change_type == ChangeType.NEW_INFO:
            actions.append(f"Add to {change.field_name}: {change.new_value}")

    strategy = recommendations.get("strategy_adjustment")
    if strategy:
        actions.append(f"Adjust strategy: {strategy}")

    if call_outcome.get("follow_up_required"):
        actions.append("Schedule follow-up contact")

    return actions


def print_diff_report(report: CustomerDiffReport) -> None:
    """Pretty print the diff report"""
    print("\n" + "=" * 70)
    print("CUSTOMER DATA DIFF REPORT")
    print("=" * 70)
    print(f"Customer: {report.customer_name} (ID: {report.customer_id})")
    print(f"Transcript: {report.transcript_id}")
    print(f"Analyzed: {report.analysis_timestamp}")
    print("-" * 70)
    print(f"\nSUMMARY: {report.summary}")

    if report.changes:
        print("\n" + "-" * 70)
        print("DETECTED CHANGES:")
        print("-" * 70)
        for i, change in enumerate(report.changes, 1):
            print(f"\n{i}. [{change.change_type.value.upper()}] {change.field_name}")
            print(f"   Current: {change.current_value}")
            print(f"   New:     {change.new_value}")
            print(f"   Confidence: {change.confidence}")
            if change.notes:
                print(f"   Notes: {change.notes}")

    if report.recommended_actions:
        print("\n" + "-" * 70)
        print("RECOMMENDED ACTIONS:")
        print("-" * 70)
        for action in report.recommended_actions:
            print(f"  • {action}")

    print("\n" + "=" * 70)


def save_diff_report(report: CustomerDiffReport, output_path: str) -> None:
    """Save diff report to JSON file"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    print(f"Report saved to: {output_path}")


# --- Example Usage ---
if __name__ == "__main__":
    # Example transcript analysis result (from TranscriptAnalyzer)
    sample_transcript_analysis = {
        "call_metadata": {
            "call_id": "call_12345",
            "customer_id": "1",
            "customer_name": "Maria Santos"
        },
        "call_outcome": {
            "primary_outcome": "payment_promised",
            "follow_up_required": True
        },
        "customer_info_extracted": {
            "current_situation": "Customer was traveling for work, missed payment due to expired card",
            "employment_status_update": "employed",
            "financial_hardship_indicators": [],
            "reason_for_non_payment": "Card on file expired while traveling internationally",
            "life_events_mentioned": ["travel", "work_conference"]
        },
        "payment_info": {
            "payment_promised": True,
            "payment_amount": 500.0,
            "payment_date": "2025-02-10",
            "payment_method": "bank_transfer",
            "payment_plan_details": {}
        },
        "recommendations": {
            "profile_type_update": 1,
            "risk_level_update": "low",
            "strategy_adjustment": "Continue friendly approach, offer autopay setup"
        }
    }

    # Load sample customer data
    sample_customer_path = Path(__file__).parent.parent / "DB" / "customers" / "01_maria_santos.json"

    if sample_customer_path.exists():
        customer_data = load_customer_json(str(sample_customer_path))

        # Generate diff report
        report = compare_customer_data(
            transcript_analysis=sample_transcript_analysis,
            customer_data=customer_data,
            transcript_id="call_12345"
        )

        # Print report
        print_diff_report(report)

        # Optionally save to file
        # save_diff_report(report, "diff_reports/maria_santos_diff.json")
    else:
        print(f"Sample customer file not found: {sample_customer_path}")
        print("Run with your own data using compare_customer_data()")