import os
import pickle
import base64
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import html2text
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes required for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailScanner:
    """
    A class to handle Gmail API authentication and email scanning for subscription information.
    """
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Initialize the GmailScanner with paths to credentials and token files.
        
        Args:
            credentials_path: Path to the credentials.json file
            token_path: Path to the token.json file
        """
        self.credentials_path = credentials_path or os.path.join(
            Path(__file__).parent.parent, 'config', 'credentials.json'
        )
        self.token_path = token_path or os.path.join(
            Path(__file__).parent.parent, 'config', 'token.json'
        )
        self.service = None
        
        # Define search queries for finding subscription emails
        self.subscription_queries = [
            'subject:"subscription confirmation"',
            'subject:"your subscription"',
            'subject:"payment receipt"',
            'subject:"recurring payment"',
            'from:(stripe.com OR paypal.com OR square.com)',
            '"monthly subscription" OR "annual subscription"',
            '"free trial" OR "trial ends" OR "trial period"',
            'subject:"invoice" AND ("monthly" OR "annually")'
        ]
        
        # Define common service providers to search for
        self.service_providers = [
            'netflix.com', 'spotify.com', 'adobe.com', 'dropbox.com',
            'amazon.com', 'apple.com', 'microsoft.com', 'google.com',
            'hulu.com', 'disney.com', 'hbo.com', 'github.com',
            'notion.so', 'canva.com', 'grammarly.com', 'zoom.us'
        ]
    
    def authenticate(self) -> bool:
        """
        Authenticate with the Gmail API using OAuth2.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        creds = None
        
        # Check if token.json exists with valid credentials
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_info(
                eval(open(self.token_path, 'r').read()), SCOPES
            )
        
        # If credentials don't exist or are invalid, refresh or get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(self.token_path, 'w') as token:
                token.write(str(creds.to_json()))
        
        # Build the Gmail API service
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def search_emails(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for emails matching the given query.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results to return
            
        Returns:
            List of email message dictionaries
        """
        if not self.service:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get message IDs matching the query
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details for each message ID
            detailed_messages = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                detailed_messages.append(msg)
            
            return detailed_messages
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def extract_email_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant content from an email message.
        
        Args:
            message: Gmail API message object
            
        Returns:
            Dictionary with extracted email content
        """
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        
        # Extract basic email metadata
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'timestamp': int(message['internalDate']) / 1000,  # Convert to seconds
            'body_text': '',
            'body_html': ''
        }
        
        # Extract email body
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        email_data['body_text'] = base64.urlsafe_b64decode(
                            part['body']['data']).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        email_data['body_html'] = base64.urlsafe_b64decode(
                            part['body']['data']).decode('utf-8')
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            # Handle single-part messages
            data = message['payload']['body']['data']
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
            
            if message['payload']['mimeType'] == 'text/plain':
                email_data['body_text'] = decoded_data
            elif message['payload']['mimeType'] == 'text/html':
                email_data['body_html'] = decoded_data
        
        # If we have HTML but no plain text, convert HTML to text
        if not email_data['body_text'] and email_data['body_html']:
            h = html2text.HTML2Text()
            h.ignore_links = False
            email_data['body_text'] = h.handle(email_data['body_html'])
        
        return email_data
    
    def scan_for_subscriptions(self, days_back: int = 365, max_results: int = 500) -> List[Dict[str, Any]]:
        """
        Scan Gmail for subscription-related emails.
        
        Args:
            days_back: Number of days back to search
            max_results: Maximum number of results per query
            
        Returns:
            List of subscription-related emails
        """
        if not self.service:
            if not self.authenticate():
                raise ValueError("Authentication failed. Check credentials.")
        
        # Calculate date range for search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_range = f"after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"
        
        all_subscription_emails = []
        
        # Search using subscription queries
        for query in self.subscription_queries:
            full_query = f"{query} {date_range}"
            messages = self.search_emails(full_query, max_results)
            
            for message in messages:
                email_content = self.extract_email_content(message)
                all_subscription_emails.append(email_content)
        
        # Search for emails from specific service providers
        for provider in self.service_providers:
            full_query = f"from:({provider}) {date_range}"
            messages = self.search_emails(full_query, max_results)
            
            for message in messages:
                email_content = self.extract_email_content(message)
                all_subscription_emails.append(email_content)
        
        # Remove duplicates based on message ID
        unique_emails = {email['id']: email for email in all_subscription_emails}
        return list(unique_emails.values())
    
    def extract_currency_amounts(self, text: str) -> List[Tuple[float, str]]:
        """
        Extract currency amounts from text.
        
        Args:
            text: Text to search for currency amounts
            
        Returns:
            List of tuples with (amount, currency)
        """
        # Pattern for USD, GBP, and EUR
        # Matches patterns like $10.99, £10.99, €10.99, 10.99 USD, 10.99 GBP, 10.99 EUR
        patterns = [
            r'[$£€]\s*(\d+(?:[.,]\d+)?)',  # $10.99, £10.99, €10.99
            r'(\d+(?:[.,]\d+)?)\s*[$£€]',  # 10.99$, 10.99£, 10.99€
            r'(\d+(?:[.,]\d+)?)\s*(?:USD|GBP|EUR|dollars|pounds|euros)',  # 10.99 USD
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '.')
                try:
                    amount = float(amount_str)
                    
                    # Determine currency
                    if '$' in match.group(0) or 'USD' in match.group(0) or 'dollars' in match.group(0).lower():
                        currency = 'USD'
                    elif '£' in match.group(0) or 'GBP' in match.group(0) or 'pounds' in match.group(0).lower():
                        currency = 'GBP'
                    elif '€' in match.group(0) or 'EUR' in match.group(0) or 'euros' in match.group(0).lower():
                        currency = 'EUR'
                    else:
                        currency = 'USD'  # Default to USD if unclear
                    
                    amounts.append((amount, currency))
                except ValueError:
                    continue
        
        return amounts
    
    def extract_billing_frequency(self, text: str) -> Optional[str]:
        """
        Extract billing frequency from text.
        
        Args:
            text: Text to search for billing frequency
            
        Returns:
            String indicating billing frequency or None if not found
        """
        monthly_patterns = [
            r'monthly(?:\s+subscription)?',
            r'per month',
            r'each month',
            r'every month',
            r'/month',
            r'month-to-month'
        ]
        
        annual_patterns = [
            r'annual(?:\s+subscription)?',
            r'yearly(?:\s+subscription)?',
            r'per year',
            r'each year',
            r'every year',
            r'/year',
            r'12-month'
        ]
        
        quarterly_patterns = [
            r'quarterly(?:\s+subscription)?',
            r'per quarter',
            r'every quarter',
            r'3-month',
            r'three-month'
        ]
        
        weekly_patterns = [
            r'weekly(?:\s+subscription)?',
            r'per week',
            r'each week',
            r'every week',
            r'/week'
        ]
        
        # Check for each pattern
        for pattern in monthly_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 'Monthly'
        
        for pattern in annual_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 'Annual'
        
        for pattern in quarterly_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 'Quarterly'
        
        for pattern in weekly_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 'Weekly'
        
        return None
    
    def extract_service_name(self, email_data: Dict[str, Any]) -> str:
        """
        Extract service name from email data.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Service name string
        """
        # Try to extract from the From field
        from_field = email_data.get('from', '')
        if '@' in from_field:
            domain = from_field.split('@')[-1].split('>')[0]
            company = domain.split('.')[0]
            if company not in ['gmail', 'yahoo', 'hotmail', 'outlook', 'mail']:
                return company.title()
        
        # Try to extract from subject
        subject = email_data.get('subject', '')
        for provider in self.service_providers:
            provider_name = provider.split('.')[0]
            if provider_name in subject.lower():
                return provider_name.title()
        
        # Default to a generic name based on the from field
        if from_field:
            return from_field.split(' ')[0].replace('"', '').replace('<', '').title()
        
        return "Unknown Service"
