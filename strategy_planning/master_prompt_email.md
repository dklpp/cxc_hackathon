# Email Generation Prompt

## Task
Generate a personalized email or SMS message for a customer regarding their overdue debt payment. Use the customer information provided from the database to create a professional, empathetic, and effective communication.

---

## Customer Information from Database

The following customer data fields are available and will be populated with actual values:

### Personal Information
- **Name:** {{CUSTOMER_FIRST_NAME}} {{CUSTOMER_LAST_NAME}}
- **Age:** {{CUSTOMER_AGE}}
- **Date of Birth:** {{CUSTOMER_DOB}}
- **Email:** {{CUSTOMER_EMAIL}}
- **Phone:** {{CUSTOMER_PHONE_PRIMARY}}
- **Secondary Phone:** {{CUSTOMER_PHONE_SECONDARY}}
- **Address:** {{CUSTOMER_ADDRESS}}, {{CUSTOMER_CITY}}, {{CUSTOMER_STATE}} {{CUSTOMER_ZIP}}

### Employment & Financial Information
- **Employer:** {{EMPLOYER_NAME}}
- **Employment Status:** {{EMPLOYMENT_STATUS}}
- **Annual Income:** {{ANNUAL_INCOME}}
- **Credit Score:** {{CREDIT_SCORE}}
- **Account Status:** {{ACCOUNT_STATUS}}
- **Customer Notes:** {{CUSTOMER_NOTES}}

### Debt Information
- **Total Debt:** {{TOTAL_DEBT}}
- **Days Past Due:** {{DAYS_PAST_DUE}}
- **Debt Type:** {{DEBT_TYPE}}
- **Original Amount:** {{ORIGINAL_AMOUNT}}
- **Current Balance:** {{CURRENT_BALANCE}}
- **Minimum Payment:** {{MINIMUM_PAYMENT}}
- **Due Date:** {{DUE_DATE}}
- **Last Payment Date:** {{LAST_PAYMENT_DATE}}
- **Debt Status:** {{DEBT_STATUS}}
- **Debt Details:** {{DEBT_DETAILS_LIST}}

### Payment History
- **Total Payments Made:** {{PAYMENT_HISTORY_COUNT}}
- **Total Amount Paid:** {{TOTAL_PAID}}
- **Recent Payments:** {{RECENT_PAYMENTS_LIST}}

### Communication History
- **Previous Communications:** {{COMMUNICATION_HISTORY_LIST}}
- **Last Contact Date:** {{LAST_CONTACT_DATE}}
- **Last Contact Outcome:** {{LAST_CONTACT_OUTCOME}}
- **Preferred Contact Time:** {{PREFERRED_CONTACT_TIME}}

### Profile Classification
- **Profile Type:** {{PROFILE_TYPE}}
- **Risk Level:** {{RISK_LEVEL}}

### Institution Information
- **Institution Name:** {{INSTITUTION_NAME}}
- **Support Phone:** {{SUPPORT_PHONE}}
- **Support Email:** {{SUPPORT_EMAIL}}
- **Payment Portal:** {{PAYMENT_PORTAL_URL}}
- **Current Date:** {{CURRENT_DATE}}

---

## Instructions

Based on the customer information provided above, generate a personalized email or SMS message that:

1. **Addresses the customer by name** and acknowledges their situation
2. **Clearly states the account status** including:
   - Current balance owed
   - Days past due
   - Minimum payment amount (if applicable)
   - Due date (if applicable)

3. **Uses an appropriate tone** based on:
   - Profile type and risk level
   - Days past due
   - Payment history
   - Previous communication outcomes

4. **Provides clear action options** such as:
   - Making a payment online via the payment portal
   - Contacting support for assistance
   - Discussing payment plan options
   - Requesting hardship assistance (if applicable)

5. **Includes required compliance language**:
   - "This is an attempt to collect a debt. Any information obtained will be used for that purpose."

6. **Is professional and empathetic**, treating the customer with respect and dignity

---

## Output Format

Generate the email content directly. Include:

- **Subject line** (for emails only)
- **Email body** with proper formatting
- Use the customer's name, specific account details, and relevant information from the database
- Include contact information (support phone, email, payment portal)
- Keep the tone appropriate for the customer's profile type and situation

---

## Guidelines

- Use the actual values from the database fields (they will be replaced automatically)
- Personalize the message based on the customer's specific situation
- Be empathetic and solution-oriented
- Avoid threatening or aggressive language
- Make it easy for the customer to take action
- Keep SMS messages under 160 characters if generating SMS
- For emails, use clear formatting with paragraphs and bullet points where helpful

Generate the email now using the customer information provided above.
