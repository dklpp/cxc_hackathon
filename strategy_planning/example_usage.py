"""
Example usage of the Strategy Pipeline

This script demonstrates how to use the strategy pipeline to analyze customers
and generate contact strategies.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_planning.strategy_pipeline import StrategyAnalyzer, print_strategy
from DB.db_manager import DatabaseManager, DebtStatus


def main():
    """Example usage of the strategy pipeline"""
    # Initialize database and analyzer
    db = DatabaseManager()
    analyzer = StrategyAnalyzer(db)
    
    print("=" * 80)
    print("STRATEGY PIPELINE - CUSTOMER CONTACT ANALYSIS")
    print("=" * 80)
    print()
    
    # Option 1: Analyze a specific customer
    print("Example 1: Analyzing a specific customer (ID: 1)")
    print("-" * 80)
    try:
        strategy = analyzer.analyze_customer(1)
        print_strategy(strategy)
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Option 2: Generate strategies for all customers with debts
    print("\n" + "=" * 80)
    print("Example 2: Generating strategies for all customers with active debts")
    print("-" * 80)
    
    strategies = analyzer.generate_strategies_for_all_customers(
        min_debt=0.0,  # Include all customers with any debt
        status=DebtStatus.ACTIVE
    )
    
    # Sort by urgency (critical first) and risk score
    strategies.sort(key=lambda s: (
        s.urgency_level.value == "critical",
        s.urgency_level.value == "high",
        -s.risk_score
    ), reverse=True)
    
    print(f"\nFound {len(strategies)} customers with active debts\n")
    
    # Show top 5 most urgent
    print("TOP 5 MOST URGENT CASES:")
    print("=" * 80)
    for i, strategy in enumerate(strategies[:5], 1):
        print(f"\n{i}. {strategy.customer_name}")
        print(f"   Urgency: {strategy.urgency_level.value.upper()} | "
              f"Risk: {strategy.risk_score:.1f}/100 | "
              f"Debt: ${strategy.total_debt:,.2f}")
        print(f"   Recommended: {strategy.recommended_channel.value.upper()} - "
              f"{strategy.tone.value.replace('_', ' ').title()}")
    
    # Show summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    urgency_counts = {}
    channel_counts = {}
    total_debt_all = 0
    
    for strategy in strategies:
        urgency_counts[strategy.urgency_level.value] = \
            urgency_counts.get(strategy.urgency_level.value, 0) + 1
        channel_counts[strategy.recommended_channel.value] = \
            channel_counts.get(strategy.recommended_channel.value, 0) + 1
        total_debt_all += strategy.total_debt
    
    print(f"\nTotal Customers: {len(strategies)}")
    print(f"Total Debt: ${total_debt_all:,.2f}")
    print(f"Average Debt: ${total_debt_all/len(strategies):,.2f}" if strategies else "N/A")
    
    print(f"\nUrgency Distribution:")
    for urgency, count in sorted(urgency_counts.items(), 
                                 key=lambda x: ["low", "medium", "high", "critical"].index(x[0])):
        print(f"  {urgency.upper()}: {count}")
    
    print(f"\nRecommended Channels:")
    for channel, count in sorted(channel_counts.items(), key=lambda x: -x[1]):
        print(f"  {channel.upper()}: {count}")
    
    # Option 3: Filter by specific criteria
    print("\n" + "=" * 80)
    print("Example 3: High-risk customers (risk score > 70)")
    print("-" * 80)
    
    high_risk = [s for s in strategies if s.risk_score > 70]
    print(f"\nFound {len(high_risk)} high-risk customers:")
    for strategy in high_risk[:3]:  # Show first 3
        print(f"  • {strategy.customer_name}: Risk {strategy.risk_score:.1f}/100, "
              f"Debt ${strategy.total_debt:,.2f}")


if __name__ == "__main__":
    main()
