"""
Example: Using Gemini AI to Generate Personalized Debt Collection Strategies

This script demonstrates how to use Gemini API to generate AI-powered
strategies for contacting customers about their debts.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_planning.strategy_pipeline import GeminiStrategyGenerator, print_gemini_strategy
from DB.db_manager import DatabaseManager


def main():
    """Example usage of Gemini strategy generator"""
    
    # Initialize database and generator
    db = DatabaseManager()
    
    try:
        # Initialize Gemini generator (reads API key from OPENROUTERS_API_KEY env var)
        generator = GeminiStrategyGenerator(db)
        
        print("=" * 80)
        print("GEMINI AI STRATEGY GENERATOR")
        print("=" * 80)
        print()
        
        # Example: Generate strategy for customer ID 1
        customer_id = 1
        
        print(f"Generating AI-powered strategy for customer ID {customer_id}...")
        print("This may take a few seconds...\n")
        
        strategy = generator.generate_strategy(customer_id)
        
        # Print the generated strategy
        print_gemini_strategy(strategy)
        
        # Example: Access specific parts of the strategy
        print("\n" + "=" * 80)
        print("STRATEGY SUMMARY")
        print("=" * 80)
        print(f"Customer: {strategy.customer_name}")
        print(f"Channel: {strategy.communication_channel}")
        print(f"Tone: {strategy.tone_recommendation}")
        print(f"Best Time: {strategy.best_contact_time}")
        
        if strategy.call_script:
            print(f"\nCall script length: {len(strategy.call_script)} characters")
        
        if strategy.email_subject:
            print(f"Email subject: {strategy.email_subject}")
        
        if strategy.sms_message:
            print(f"SMS: {strategy.sms_message}")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure OPENROUTERS_API_KEY is set in your .env file")
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall requests:")
        print("  uv add requests")
    except Exception as e:
        print(f"Error generating strategy: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
