"""
Example: Using Transcript Analyzer to Analyze Call Transcripts

This script demonstrates how to use the TranscriptAnalyzer to analyze
call transcripts and extract key information for dashboard tracking.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcript_analysis.transcript_analyzer import TranscriptAnalyzer
from DB.db_manager import DatabaseManager


def main():
    """Example usage of transcript analyzer"""
    
    # Initialize database manager
    db = DatabaseManager()
    
    try:
        # Initialize analyzer (reads API key from OPENROUTERS_API_KEY env var)
        analyzer = TranscriptAnalyzer(db_manager=db)
        
        print("=" * 80)
        print("TRANSCRIPT ANALYZER - EXAMPLE USAGE")
        print("=" * 80)
        print()
        
        # Example 1: Analyze a sample transcript with customer context
        print("Example 1: Analyzing sample transcript with customer context")
        print("-" * 80)
        
        sample_transcript = """
Agent: Hello, this is Alex from First National Bank. Am I speaking with Maria Santos?

Customer: Yes, this is Maria.

Agent: Hi Maria, I'm calling about your credit card account. We noticed a payment was missed.
Is everything okay?

Customer: Oh yes, I'm so sorry about that. I was traveling for work and my autopay card expired.
I completely forgot to update it.

Agent: I completely understand, that happens. Your account shows $2,340 outstanding.
Would you like to make a payment today?

Customer: Yes, absolutely. Can I pay the full amount right now?

Agent: Of course! I can process that for you. And as a courtesy for your excellent history with us,
I'm waiving the late fee.

Customer: Thank you so much, I really appreciate that.

Agent: You're welcome. I'll also help you update your autopay so this doesn't happen again.
        """
        
        # Analyze with customer ID 1 (Maria Santos)
        result = analyzer.analyze_transcript(
            transcript=sample_transcript,
            customer_id=1,
            call_id="call_001"
        )
        
        # Print key results
        print(f"Call Outcome: {result['call_outcome']['primary_outcome']}")
        print(f"Success Score: {result['call_outcome']['success_score']:.2f}")
        print(f"Payment Promised: {result['payment_info']['payment_promised']}")
        if result['payment_info']['payment_amount']:
            print(f"Payment Amount: ${result['payment_info']['payment_amount']:.2f}")
        print(f"Customer Sentiment: {result['customer_sentiment']['overall_sentiment']}")
        print(f"Follow-up Required: {result['call_outcome']['follow_up_required']}")
        print()
        
        # Example 2: Analyze from a file
        print("Example 2: Analyzing transcript from file")
        print("-" * 80)
        print("To analyze a transcript file, use:")
        print("  python transcript_analysis/transcript_analyzer.py <transcript_file> --customer-id 1 --output results.json")
        print()
        
        # Example 3: Update database
        print("Example 3: Updating database with analysis results")
        print("-" * 80)
        print("To update the database, add --update-db flag:")
        print("  python transcript_analysis/transcript_analyzer.py <transcript_file> --customer-id 1 --update-db")
        print()
        
        # Show full result structure
        print("=" * 80)
        print("FULL ANALYSIS RESULT STRUCTURE")
        print("=" * 80)
        import json
        print(json.dumps(result, indent=2, default=str))
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure OPENROUTERS_API_KEY is set in your .env file")
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall requests:")
        print("  uv add requests")
    except Exception as e:
        print(f"Error analyzing transcript: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
