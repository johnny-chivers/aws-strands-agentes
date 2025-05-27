import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

class SubscriptionAnalyzer:
    """
    A class to analyze subscription data extracted from emails.
    """
    
    def __init__(self):
        """
        Initialize the SubscriptionAnalyzer.
        """
        # Define service categories for classification
        self.service_categories = {
            'streaming': [
                'netflix', 'hulu', 'disney', 'spotify', 'apple music', 'youtube', 
                'hbo', 'prime video', 'paramount', 'peacock', 'crunchyroll', 
                'dazn', 'fubo', 'sling', 'tidal'
            ],
            'productivity': [
                'microsoft', 'office', 'google', 'workspace', 'dropbox', 'box', 
                'evernote', 'notion', 'airtable', 'asana', 'trello', 'slack', 
                'zoom', 'adobe', 'canva', 'grammarly'
            ],
            'gaming': [
                'xbox', 'playstation', 'nintendo', 'steam', 'epic games', 'ea play', 
                'ubisoft', 'game pass', 'ps plus', 'nintendo online'
            ],
            'fitness': [
                'peloton', 'fitbit', 'strava', 'myfitnesspal', 'beachbody', 'classpass', 
                'fitness', 'gym', 'workout'
            ],
            'news': [
                'nyt', 'new york times', 'wsj', 'wall street journal', 'washington post', 
                'economist', 'financial times', 'bloomberg', 'medium', 'substack'
            ],
            'shopping': [
                'amazon', 'walmart', 'instacart', 'doordash', 'uber eats', 'grubhub', 
                'hello fresh', 'blue apron', 'prime', 'costco'
            ],
            'security': [
                'norton', 'mcafee', 'avast', 'avg', 'kaspersky', 'bitdefender', 
                'vpn', 'password', 'lastpass', '1password', 'dashlane'
            ],
            'cloud': [
                'aws', 'amazon web', 'azure', 'google cloud', 'digitalocean', 'linode', 
                'vultr', 'heroku', 'netlify', 'vercel'
            ]
        }
    
    def categorize_subscription(self, service_name: str, email_content: str) -> str:
        """
        Categorize a subscription service based on its name and email content.
        
        Args:
            service_name: Name of the service
            email_content: Content of the email
            
        Returns:
            Category string
        """
        service_name_lower = service_name.lower()
        
        # Check if service name matches any category
        for category, services in self.service_categories.items():
            for service in services:
                if service in service_name_lower:
                    return category.title()
        
        # If no match in service name, check email content
        content_lower = email_content.lower()
        for category, services in self.service_categories.items():
            for service in services:
                if service in content_lower:
                    return category.title()
        
        # Default category if no match found
        return "Other"
    
    def calculate_monthly_cost(self, amount: float, frequency: str) -> float:
        """
        Calculate the monthly cost based on amount and billing frequency.
        
        Args:
            amount: The subscription amount
            frequency: The billing frequency (Monthly, Annual, etc.)
            
        Returns:
            Monthly cost as a float
        """
        if not frequency:
            return amount  # Default to the amount if frequency is unknown
        
        frequency = frequency.lower()
        
        if 'annual' in frequency or 'yearly' in frequency:
            return amount / 12
        elif 'quarterly' in frequency:
            return amount / 3
        elif 'weekly' in frequency:
            return amount * 4.33  # Average weeks in a month
        elif 'daily' in frequency:
            return amount * 30.42  # Average days in a month
        else:
            return amount  # Default to monthly
    
    def is_subscription_active(self, last_email_date: datetime, threshold_days: int = 60) -> bool:
        """
        Determine if a subscription is likely active based on the last email date.
        
        Args:
            last_email_date: Date of the last email for this subscription
            threshold_days: Number of days to consider a subscription inactive
            
        Returns:
            Boolean indicating if the subscription is likely active
        """
        return (datetime.now() - last_email_date).days <= threshold_days
    
    def detect_free_trial(self, email_content: str) -> Tuple[bool, Optional[datetime]]:
        """
        Detect if an email is about a free trial and when it ends.
        
        Args:
            email_content: Content of the email
            
        Returns:
            Tuple of (is_free_trial, end_date)
        """
        # Check if this is a free trial email
        trial_patterns = [
            r'free trial',
            r'trial period',
            r'trial ends',
            r'trial will end',
            r'trial expir'
        ]
        
        is_free_trial = any(re.search(pattern, email_content, re.IGNORECASE) 
                           for pattern in trial_patterns)
        
        if not is_free_trial:
            return False, None
        
        # Try to extract the trial end date
        date_patterns = [
            r'trial\s+(?:will\s+)?end(?:s|ing)?\s+on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
            r'trial\s+(?:will\s+)?end(?:s|ing)?\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'until\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
            r'expires\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, email_content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%B %d, %Y', '%B %d %Y', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y']:
                        try:
                            return True, datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        # If we found a free trial but couldn't parse the date
        return True, None
    
    def analyze_subscription_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a list of subscription emails and extract subscription details.
        
        Args:
            emails: List of email data dictionaries
            
        Returns:
            List of subscription details
        """
        subscriptions = []
        
        # Group emails by service
        service_emails = {}
        for email in emails:
            from_domain = email.get('from', '').split('@')[-1].split('>')[0] if '@' in email.get('from', '') else ''
            service_name = email.get('service_name', from_domain.split('.')[0].title())
            
            if service_name not in service_emails:
                service_emails[service_name] = []
            
            service_emails[service_name].append(email)
        
        # Process each service's emails
        for service_name, service_email_list in service_emails.items():
            # Sort emails by date (newest first)
            service_email_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            # Get the most recent email
            latest_email = service_email_list[0]
            email_date = datetime.fromtimestamp(latest_email.get('timestamp', 0))
            
            # Extract subscription details from the most recent email
            email_body = latest_email.get('body_text', '')
            
            # Extract currency amounts
            amounts = []
            if hasattr(latest_email, 'extract_currency_amounts'):
                amounts = latest_email.extract_currency_amounts(email_body)
            
            # Find the most likely subscription amount
            subscription_amount = None
            currency = 'USD'
            if amounts:
                # Use the most common amount or the first one if there's a tie
                amount_counts = {}
                for amount, curr in amounts:
                    if amount not in amount_counts:
                        amount_counts[amount] = 0
                    amount_counts[amount] += 1
                
                most_common_amount = max(amount_counts.items(), key=lambda x: x[1])[0]
                subscription_amount = most_common_amount
                
                # Find the currency for this amount
                for amount, curr in amounts:
                    if amount == subscription_amount:
                        currency = curr
                        break
            
            # Extract billing frequency
            billing_frequency = None
            if hasattr(latest_email, 'extract_billing_frequency'):
                billing_frequency = latest_email.extract_billing_frequency(email_body)
            
            if not billing_frequency:
                # Try to infer from common keywords
                if re.search(r'monthly|per month|/month', email_body, re.IGNORECASE):
                    billing_frequency = 'Monthly'
                elif re.search(r'annual|yearly|per year|/year', email_body, re.IGNORECASE):
                    billing_frequency = 'Annual'
                elif re.search(r'quarterly|per quarter|every 3 months', email_body, re.IGNORECASE):
                    billing_frequency = 'Quarterly'
                else:
                    billing_frequency = 'Unknown'
            
            # Categorize the subscription
            category = self.categorize_subscription(service_name, email_body)
            
            # Check if this is a free trial
            is_free_trial, trial_end_date = self.detect_free_trial(email_body)
            
            # Calculate monthly cost
            monthly_cost = None
            if subscription_amount is not None:
                monthly_cost = self.calculate_monthly_cost(subscription_amount, billing_frequency)
            
            # Create subscription record
            subscription = {
                'service_name': service_name,
                'category': category,
                'amount': subscription_amount,
                'currency': currency,
                'billing_frequency': billing_frequency,
                'monthly_cost': monthly_cost,
                'last_email_date': email_date,
                'is_active': self.is_subscription_active(email_date),
                'is_free_trial': is_free_trial,
                'trial_end_date': trial_end_date,
                'email_count': len(service_email_list),
                'latest_email_id': latest_email.get('id')
            }
            
            subscriptions.append(subscription)
        
        return subscriptions
    
    def generate_summary_report(self, subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary report of subscription data.
        
        Args:
            subscriptions: List of subscription details
            
        Returns:
            Dictionary with summary statistics
        """
        # Filter active subscriptions
        active_subscriptions = [s for s in subscriptions if s.get('is_active', False)]
        
        # Calculate total monthly cost
        total_monthly_cost = sum(s.get('monthly_cost', 0) for s in active_subscriptions if s.get('monthly_cost') is not None)
        
        # Calculate annual projection
        annual_projection = total_monthly_cost * 12
        
        # Group by category
        categories = {}
        for sub in active_subscriptions:
            category = sub.get('category', 'Other')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'monthly_cost': 0
                }
            
            categories[category]['count'] += 1
            categories[category]['monthly_cost'] += sub.get('monthly_cost', 0) or 0
        
        # Find free trials ending soon
        current_date = datetime.now()
        trials_ending_soon = [
            s for s in subscriptions 
            if s.get('is_free_trial', False) and s.get('trial_end_date') is not None
            and s.get('trial_end_date') > current_date
            and (s.get('trial_end_date') - current_date).days <= 14
        ]
        
        # Find potentially unused subscriptions (no emails in a while)
        unused_threshold = 60  # days
        unused_subscriptions = [
            s for s in active_subscriptions
            if (current_date - s.get('last_email_date', current_date)).days > unused_threshold
        ]
        
        # Generate summary report
        summary = {
            'total_subscriptions': len(subscriptions),
            'active_subscriptions': len(active_subscriptions),
            'total_monthly_cost': total_monthly_cost,
            'annual_projection': annual_projection,
            'categories': categories,
            'trials_ending_soon': trials_ending_soon,
            'unused_subscriptions': unused_subscriptions
        }
        
        return summary
