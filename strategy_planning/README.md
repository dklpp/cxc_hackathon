# Strategy Pipeline

Intelligent debt collection strategy generator that analyzes customer data and generates optimal contact strategies.

## Overview

The Strategy Pipeline analyzes customer profiles, debt history, payment patterns, and communication history to recommend:

- **Communication Channel**: Call, Email, SMS, or Multi-channel
- **Urgency Level**: Low, Medium, High, or Critical
- **Message Tone**: Friendly Reminder, Professional, Urgent, or Final Notice
- **Contact Timing**: Best time of day to reach the customer
- **Payment Suggestions**: Recommended payment amounts and payment plans
- **Risk Assessment**: Risk score and payment probability estimates

## Features

### Analysis Components

1. **Payment History Analysis**
   - Calculates payment completion rate
   - Analyzes recent payment patterns
   - Identifies failed payment trends

2. **Communication Responsiveness**
   - Tracks response rates to outbound communications
   - Identifies successful communication channels
   - Analyzes communication outcomes

3. **Risk Scoring**
   - Debt amount assessment
   - Days past due analysis
   - Employment status evaluation
   - Credit score consideration

4. **Strategy Generation**
   - Channel recommendation based on customer preferences and history
   - Tone selection based on urgency and payment history
   - Message generation tailored to customer profile
   - Payment amount suggestions based on debt and income

## Usage

### Basic Usage (Rule-Based Analysis)

```python
from strategy_planning.strategy_pipeline import StrategyAnalyzer, print_strategy
from DB.db_manager import DatabaseManager

# Initialize
db = DatabaseManager()
analyzer = StrategyAnalyzer(db)

# Analyze a specific customer
strategy = analyzer.analyze_customer(customer_id=1)
print_strategy(strategy)
```

### AI-Powered Strategy Generation with Gemini (via OpenRouter)

Generate personalized strategies using Google's Gemini AI through OpenRouter:

```python
from strategy_planning.strategy_pipeline import GeminiStrategyGenerator, print_gemini_strategy
from DB.db_manager import DatabaseManager

# Initialize
db = DatabaseManager()
generator = GeminiStrategyGenerator(db)

# Generate AI-powered strategy for a customer
strategy = generator.generate_strategy(customer_id=1)
print_gemini_strategy(strategy)
```

**Setup:**
1. Get an OpenRouter API key from [OpenRouter](https://openrouter.ai/keys)
2. Add to `.env` file:
   ```
   OPENROUTERS_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```bash
   uv add requests
   ```
   
**Note:** This uses OpenRouter to access Google's Gemini model. OpenRouter provides unified access to multiple AI models including Gemini.

**Command Line Usage:**
```bash
# Generate strategy using Gemini AI
uv run python strategy_planning/strategy_pipeline.py --customer-id 1 --use-gemini

# Or use traditional rule-based analysis
uv run python strategy_planning/strategy_pipeline.py --customer-id 1
```

### Generate Strategies for All Customers

```python
# Get strategies for all customers with active debts
strategies = analyzer.generate_strategies_for_all_customers(
    min_debt=0.0,  # Minimum debt amount to include
    status=DebtStatus.ACTIVE  # Only active debts
)

# Sort by urgency
strategies.sort(key=lambda s: s.urgency_level.value, reverse=True)

# Process each strategy
for strategy in strategies:
    print_strategy(strategy)
```

### Filter by Criteria

```python
# High-risk customers
high_risk = [s for s in strategies if s.risk_score > 70]

# Critical urgency cases
critical = [s for s in strategies if s.urgency_level == UrgencyLevel.CRITICAL]

# Customers needing phone calls
phone_calls = [s for s in strategies 
               if s.recommended_channel == CommunicationChannel.CALL]
```

## Strategy Components

### ContactStrategy Object

Each strategy contains:

- **Customer Information**: ID, name
- **Recommendations**: Channel, urgency, tone, timing
- **Messaging**: Suggested message, payment amount, payment plan
- **Analysis**: Risk score, payment probability, reasoning
- **Context**: Total debt, days past due, payment history score

### Urgency Levels

- **LOW**: Recent debt, low amount, good payment history
- **MEDIUM**: Moderate debt, some days past due
- **HIGH**: Significant debt, 30-60 days past due
- **CRITICAL**: Large debt, 90+ days past due, high risk

### Communication Channels

- **CALL**: Best for urgent matters, low responsiveness
- **EMAIL**: Good for customers with email preference, high responsiveness
- **SMS**: Quick reminders, less urgent matters
- **MULTI_CHANNEL**: Critical cases requiring multiple contact methods

### Message Tones

- **FRIENDLY_REMINDER**: For customers with good payment history
- **PROFESSIONAL**: Standard business communication
- **URGENT**: For accounts significantly past due
- **FINAL_NOTICE**: For critical cases requiring immediate action

## Scoring System

### Payment History Score (0-100)
- Based on payment completion rate
- Recent payment bonus
- Failed payment penalties

### Communication Responsiveness (0-100)
- Response rate to outbound communications
- Positive outcome rate (payments promised/made)
- Inbound communication frequency

### Risk Score (0-100)
- Higher = more risk
- Factors: debt amount, days past due, payment history, employment status

### Payment Probability (0-100)
- Estimated likelihood of receiving payment
- Based on history, responsiveness, and customer profile

## Example Output

```
================================================================================
CONTACT STRATEGY: John Doe (ID: 1)
================================================================================

📊 ANALYSIS:
  Total Debt: $11,700.00
  Days Past Due: 45
  Risk Score: 65.0/100
  Payment Probability: 72.5%
  Payment History Score: 75.0/100
  Communication Responsiveness: 70.0/100

🎯 RECOMMENDATIONS:
  Urgency Level: HIGH
  Channel: CALL
  Tone: Urgent
  Best Time: MORNING
  Days Since Last Contact: 7
  Suggested Payment: $375.00

💡 PAYMENT PLAN:
  Consider a 6-month payment plan at $1,950.00/month. Based on your payment 
  history, you may qualify for reduced interest.

💬 SUGGESTED MESSAGE:
  John, your account has an outstanding balance of $11,700.00 that requires 
  immediate attention. Please contact us today to resolve this matter and avoid 
  additional fees or collection actions.

📝 REASONING:
  • Total debt: $11,700.00
  • Days past due: 45
  • Payment history score: 75.0/100
  • Communication responsiveness: 70.0/100
  • HIGH priority: Account is significantly past due
  • Recommended channel: call (best for this customer profile)
```

## Integration

The strategy pipeline integrates seamlessly with:

- **Database Manager**: Uses customer, debt, payment, and communication data
- **Communication Logs**: Analyzes past communication effectiveness
- **Payment History**: Evaluates payment patterns and reliability

## Running Examples

```bash
# Run the example script
uv run python strategy_planning/example_usage.py

# Or run the pipeline directly
uv run python strategy_planning/strategy_pipeline.py
```

## Gemini AI Integration (via OpenRouter)

The Gemini AI integration uses OpenRouter to access Google's Gemini model. This provides:

- **Personalized Call Scripts**: Full conversation scripts tailored to each customer
- **Email Templates**: Subject lines and body content optimized for response
- **SMS Messages**: Concise, action-oriented text messages
- **Talking Points**: Key points to cover during conversations
- **Context-Aware**: Considers customer's preferred communication method, payment history, and debt situation
- **Empathetic Approach**: AI generates strategies that balance firmness with empathy

### Example Output

The Gemini generator creates:
- **Call Scripts**: Natural conversation flow with greeting, main points, and closing
- **Email Content**: Professional but warm tone with clear call-to-action
- **SMS Messages**: Under 160 characters, friendly and action-oriented
- **Payment Suggestions**: Realistic amounts based on customer income and debt
- **Timing Recommendations**: Best time to contact based on customer profile

## Future Enhancements

Potential improvements:

- Machine learning models for payment probability prediction
- A/B testing framework for strategy effectiveness
- Integration with communication systems (Twilio, email services)
- Automated strategy execution
- Performance tracking and optimization
- Timezone-aware contact timing
- Multi-language message generation
- Fine-tuned Gemini models for debt collection

## OpenRouter Integration

This project uses [OpenRouter](https://openrouter.ai/) to access Gemini models. OpenRouter provides:
- Unified API for multiple AI models
- Easy API key management
- Cost tracking and analytics
- Access to various Gemini model variants (gemini-pro, gemini-pro-vision, etc.)

To use a different Gemini model, pass the model name when initializing:
```python
generator = GeminiStrategyGenerator(db, model="google/gemini-2.5-pro")
```

Available Gemini models on OpenRouter:
- `google/gemini-2.5-pro` (default)
- `google/gemini-2.0-flash-exp`
- `google/gemini-pro-vision`
- See [OpenRouter Models](https://openrouter.ai/models) for the full list
