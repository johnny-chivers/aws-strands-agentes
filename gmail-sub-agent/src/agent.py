import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel

from .gmail_scanner import GmailScanner
from .subscription_analyzer import SubscriptionAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('gmail_sub_agent')

class GmailSubAgent:
    """
    A Strands agent for scanning Gmail for subscription information.
    """
    
    def __init__(self, region: str = 'us-east-1', profile_name: str = 'default'):
        """
        Initialize the Gmail Subscription Agent.
        
        Args:
            region: AWS region for Bedrock
            profile_name: AWS profile name
        """
        self.region = region
        self.profile_name = profile_name
        self.gmail_scanner = GmailScanner()
        self.subscription_analyzer = SubscriptionAnalyzer()
        self.agent = self._create_agent()
        self.subscriptions = []
        self.summary = {}
    
    def _create_agent(self) -> Agent:
        """
        Create and configure the Strands agent.
        
        Returns:
            Configured Strands Agent
        """
        # Create a BedrockModel with Amazon Nova Pro
        bedrock_model = BedrockModel(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",  # Using Claude 3.5 Sonnet as Nova Pro
            region_name=self.region,
            profile_name=self.profile_name,
            temperature=0.2,  # Lower temperature for more deterministic responses
        )
        
        # Define the agent with tools
        agent = Agent(
            model=bedrock_model,
            tools=[
                self.analyze_email_content,
                self.categorize_subscription,
                self.calculate_costs,
                self.generate_summary
            ],
            system_prompt="""
            You are a Subscription Audit & Cancellation Assistant. Your job is to help users identify 
            and manage their recurring subscriptions by analyzing their Gmail inbox.
            
            You can:
            1. Analyze email content to extract subscription details
            2. Categorize subscriptions by type (streaming, productivity, etc.)
            3. Calculate costs and provide financial insights
            4. Generate summary reports of all subscriptions
            
            Be precise when extracting financial information and dates. Look for patterns in 
            subscription emails including amounts in USD, GBP, and EUR. Pay special attention to 
            recurring billing language, free trial periods, and cancellation options.
            """
        )
        
        return agent
    
    @tool
    def analyze_email_content(self, email_content: str) -> Dict[str, Any]:
        """
        Extract subscription details from email content.
        
        Args:
            email_content: The content of the email to analyze
            
        Returns:
            Dictionary with extracted subscription details
        """
        # Extract currency amounts
        amounts = self.gmail_scanner.extract_currency_amounts(email_content)
        
        # Extract billing frequency
        billing_frequency = self.gmail_scanner.extract_billing_frequency(email_content)
        
        # Check for free trial language
        is_free_trial = any(phrase in email_content.lower() for phrase in 
                           ['free trial', 'trial period', 'trial ends'])
        
        return {
            'amounts': amounts,
            'billing_frequency': billing_frequency,
            'is_free_trial': is_free_trial,
            'content_length': len(email_content)
        }
    
    @tool
    def categorize_subscription(self, service_name: str, email_content: str) -> str:
        """
        Identify service type (streaming, productivity, etc.).
        
        Args:
            service_name: Name of the service
            email_content: Content of the email
            
        Returns:
            Category string
        """
        return self.subscription_analyzer.categorize_subscription(service_name, email_content)
    
    @tool
    def calculate_costs(self, amount: float, frequency: str) -> Dict[str, float]:
        """
        Parse amounts and billing frequency to calculate costs.
        
        Args:
            amount: The subscription amount
            frequency: The billing frequency (Monthly, Annual, etc.)
            
        Returns:
            Dictionary with calculated costs
        """
        monthly_cost = self.subscription_analyzer.calculate_monthly_cost(amount, frequency)
        annual_cost = monthly_cost * 12
        
        return {
            'monthly_cost': monthly_cost,
            'annual_cost': annual_cost,
            'original_amount': amount,
            'frequency': frequency
        }
    
    @tool
    def generate_summary(self, subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create formatted report of subscription data.
        
        Args:
            subscriptions: List of subscription details
            
        Returns:
            Dictionary with summary statistics
        """
        return self.subscription_analyzer.generate_summary_report(subscriptions)
    
    def scan_gmail(self, days_back: int = 365, max_results: int = 500) -> List[Dict[str, Any]]:
        """
        Scan Gmail for subscription emails.
        
        Args:
            days_back: Number of days back to search
            max_results: Maximum number of results per query
            
        Returns:
            List of processed subscription details
        """
        # Authenticate with Gmail
        if not self.gmail_scanner.authenticate():
            logger.error("Gmail authentication failed. Check credentials.")
            return []
        
        # Scan for subscription emails
        logger.info(f"Scanning Gmail for subscription emails (last {days_back} days)...")
        emails = self.gmail_scanner.scan_for_subscriptions(days_back, max_results)
        logger.info(f"Found {len(emails)} potential subscription-related emails")
        
        # Process emails to extract subscription details
        processed_emails = []
        for email in emails:
            # Extract service name
            service_name = self.gmail_scanner.extract_service_name(email)
            email['service_name'] = service_name
            
            # Use the agent to analyze the email content
            email_content = email.get('body_text', '')
            if email_content:
                analysis_result = self.agent(f"Analyze this email content to extract subscription details: {email_content[:5000]}").message
                email['agent_analysis'] = analysis_result
            
            processed_emails.append(email)
        
        # Analyze subscription data
        self.subscriptions = self.subscription_analyzer.analyze_subscription_emails(processed_emails)
        
        # Generate summary
        self.summary = self.subscription_analyzer.generate_summary_report(self.subscriptions)
        
        return self.subscriptions
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Export subscription data to CSV.
        
        Args:
            filepath: Path to save the CSV file
            
        Returns:
            Boolean indicating success
        """
        if not self.subscriptions:
            logger.warning("No subscription data to export")
            return False
        
        try:
            import csv
            
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = [
                    'service_name', 'category', 'amount', 'currency', 
                    'billing_frequency', 'monthly_cost', 'last_email_date',
                    'is_active', 'is_free_trial'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for sub in self.subscriptions:
                    # Convert datetime objects to strings
                    if 'last_email_date' in sub and isinstance(sub['last_email_date'], datetime):
                        sub['last_email_date'] = sub['last_email_date'].strftime('%Y-%m-%d')
                    
                    if 'trial_end_date' in sub and isinstance(sub['trial_end_date'], datetime):
                        sub['trial_end_date'] = sub['trial_end_date'].strftime('%Y-%m-%d')
                    
                    # Write only the fields in fieldnames
                    row = {field: sub.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Exported subscription data to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get the summary report of subscription data.
        
        Returns:
            Dictionary with summary statistics
        """
        return self.summary
