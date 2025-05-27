# Gmail Subscription Agent

A Subscription Audit & Cancellation Agent built with AWS Strands SDK that scans your Gmail inbox to identify and track recurring subscriptions.

## Features

- **Gmail Integration**: Securely connects to your Gmail account to scan for subscription-related emails
- **Subscription Detection**: Identifies recurring payments, subscriptions, and free trials
- **Multi-Currency Support**: Recognizes amounts in USD, GBP, and EUR
- **Intelligent Categorization**: Automatically categorizes subscriptions (streaming, productivity, etc.)
- **Cost Analysis**: Calculates monthly and annual spending on subscriptions
- **Unused Subscription Detection**: Identifies potentially forgotten subscriptions
- **Free Trial Tracking**: Warns about free trials that are ending soon
- **CSV Export**: Export all subscription data for further analysis

## Prerequisites

- Python 3.8+
- AWS account with access to Amazon Bedrock
- Gmail account with OAuth credentials

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd gmail-sub-agent
   ```

2. Run the setup script:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

3. Set up Gmail API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials.json file
   - Place it in the `config/` directory

## Usage

Run the agent with:

```
python run.py
```

### Command Line Options

- `--days`: Number of days back to search (default: 365)
- `--max-results`: Maximum number of results per query (default: 500)
- `--region`: AWS region for Bedrock (default: us-east-1)
- `--profile`: AWS profile name (default: default)
- `--export`: Export results to CSV file (e.g., `--export=subscriptions.csv`)

Example:
```
python run.py --days=180 --export=my_subscriptions.csv
```

## How It Works

1. **Authentication**: Securely connects to your Gmail account using OAuth2
2. **Email Scanning**: Searches for emails matching subscription patterns
3. **Content Analysis**: Uses AWS Strands with Amazon Nova to analyze email content
4. **Data Extraction**: Identifies subscription details, costs, and billing frequency
5. **Reporting**: Generates a comprehensive report of all subscriptions

## Project Structure

```
gmail-sub-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py            # Strands agent implementation
│   ├── gmail_scanner.py    # Gmail API integration
│   └── subscription_analyzer.py  # Subscription analysis logic
├── config/
│   └── .gitignore          # Ignores credentials.json and token.json
├── requirements.txt        # Project dependencies
├── setup.sh                # Installation script
├── run.py                  # CLI interface
└── README.md               # This file
```

## Security

This application:
- Uses OAuth 2.0 for Gmail authentication (no password storage)
- Stores authentication tokens locally in your config directory
- Only requests read-only access to your Gmail
- Does not send your email data to any external services (all processing is done locally)

## License

[MIT License](LICENSE)
