# AWS Strands Agents Tutorial 

## Intro 
In this step-by-step tutorial, I'll show you how to build a powerful Gmail Subscription Audit & Cancellation Agent using the AWS Strands Agents SDK. This practical project helps you track and manage your recurring subscriptions by scanning your Gmail inbox for payment receipts and subscription notifications.

Youtube Video: https://youtu.be/qe0WYtcsNSI 

## Prompt Used For Video 
I want to create a "Gmail Sub Agent" - a Subscription Audit & Cancellation Agent using AWS Strands SDK. This should look for amount sin USD, GBP, and EUROs. The emails may also be in HTML Format. The documentation fo AWS strands is located here: https://github.com/strands-agents/sdk-python. However, you have access to the strands MCP server for documentation. This should run using my default aws profile in us-east-1 where I have amazon Nova running. 

### Project Requirements:

#### 1. Initial Setup
- Create a new project in the current directory called `gmail-sub-agent`
- Set up a Python virtual environment
- Create a clean project structure:
  ```
  gmail-sub-agent/
  ├── src/
  │   ├── __init__.py
  │   ├── agent.py
  │   ├── gmail_scanner.py
  │   └── subscription_analyzer.py
  ├── config/
  │   └── .gitignore (include credentials.json, token.json)
  ├── requirements.txt
  ├── setup.sh (installation script)
  ├── run.py
  └── README.md
  ```

#### 2. Dependencies (requirements.txt):
- strands-agents
- boto3
- google-auth
- google-auth-oauthlib
- google-auth-httplib2
- google-api-python-client
- python-dateutil
- tabulate
- colorama

#### 3. AWS Strands Configuration:
- Use BedrockModel with Amazon Nova Pro 
- Configure using AWS CLI profile for authentication
- Set up the agent with appropriate tools for email analysis

#### 4. Gmail Integration Features:
Create a gmail_scanner.py that:
- Handles OAuth2 authentication flow
- Implements email search with these queries:
  ```python
  subscription_queries = [
      'subject:"subscription confirmation"',
      'subject:"your subscription"',
      'subject:"payment receipt"',
      'subject:"recurring payment"',
      'from:(stripe.com OR paypal.com OR square.com)',
      '"monthly subscription" OR "annual subscription"',
      '"free trial" OR "trial ends" OR "trial period"',
      'subject:"invoice" AND ("monthly" OR "annually")'
  ]
  
  service_providers = [
      'netflix.com', 'spotify.com', 'adobe.com', 'dropbox.com',
      'amazon.com', 'apple.com', 'microsoft.com', 'google.com',
      'hulu.com', 'disney.com', 'hbo.com', 'github.com',
      'notion.so', 'canva.com', 'grammarly.com', 'zoom.us'
  ]
  ```

#### 5. Core Agent Tools:
Create these tools for the Strands agent:
- `analyze_email_content`: Extract subscription details from email body
- `categorize_subscription`: Identify service type (streaming, productivity, etc.)
- `calculate_costs`: Parse amounts and billing frequency
- `generate_summary`: Create formatted report

#### 6. CLI Interface (run.py):
```python
# Should have this flow:
1. Friendly ASCII art welcome banner
2. Check/request Gmail authentication
3. Show scanning progress with spinner
4. Display results in a formatted table
5. Summary statistics (total monthly cost, potential savings)
6. Export option to CSV
```

#### 7. Demo-Ready Features:
- Colored output using colorama
- Progress indicators during scanning
- Clear section headers
- Example output format:
  ```
  📊 SUBSCRIPTION AUDIT RESULTS
  ════════════════════════════════════════

  Active Subscriptions Found:
  ┌─────────────────┬──────────┬───────────┬─────────────┐
  │ Service         │ Cost     │ Frequency │ Last Charged│
  ├─────────────────┼──────────┼───────────┼─────────────┤
  │ Netflix         │ $15.99   │ Monthly   │ Oct 15      │
  │ Spotify Family  │ $16.99   │ Monthly   │ Oct 20      │
  └─────────────────┴──────────┴───────────┴─────────────┘

  💰 Monthly Total: $91.96
  📅 Annual Projection: $1,103.52
  
  ⚠️  Unused Subscriptions (no emails in 60+ days):
  - FitnessApp Pro ($12.99/month)
  ```

#### 8. Setup Script (setup.sh):
Create a bash script that:
- Creates virtual environment
- Installs dependencies
- Checks for AWS credentials
- Provides Gmail API setup instructions
- Creates necessary directories

#### 9. Error Handling:
- Graceful handling of API rate limits
- Clear error messages for auth issues
- Timeout handling for large inboxes

#### 10. Additional Features:
- Option to scan specific date ranges
- Ability to ignore certain subscriptions
- Detection of duplicate subscriptions
- Free trial expiration warnings

Please implement this step by step, starting with the project structure and setup script.

## Creators

**Johnny Chivers**

- <https://github.com/johnny-chivers/>

## Useful Links

- [youtube video](https://youtu.be/iGvj1gjbwl0) 
- [website](https://www.johnnychivers.co.uk)
- [buy me a coffee](https://www.buymeacoffee.com/johnnychivers)


Enjoy :metal:
