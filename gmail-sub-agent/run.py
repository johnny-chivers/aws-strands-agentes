#!/usr/bin/env python3

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

import colorama
from colorama import Fore, Style, Back
from tabulate import tabulate
from tqdm import tqdm

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.agent import GmailSubAgent

# Initialize colorama
colorama.init(autoreset=True)

def print_banner():
    """Print a colorful ASCII art banner."""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
{Fore.CYAN}║ {Fore.YELLOW}  _____                 _ _   {Fore.GREEN}  _____       _        {Fore.CYAN}      ║
{Fore.CYAN}║ {Fore.YELLOW} / ____|               (_) |  {Fore.GREEN} / ____|     | |       {Fore.CYAN}      ║
{Fore.CYAN}║ {Fore.YELLOW}| |  __ _ __ ___   __ _ _| |  {Fore.GREEN}| (___  _   _| |__     {Fore.CYAN}      ║
{Fore.CYAN}║ {Fore.YELLOW}| | |_ | '_ ` _ \\ / _` | | |  {Fore.GREEN} \\___ \\| | | | '_ \\    {Fore.CYAN}      ║
{Fore.CYAN}║ {Fore.YELLOW}| |__| | | | | | | (_| | | |  {Fore.GREEN} ____) | |_| | |_) |   {Fore.CYAN}      ║
{Fore.CYAN}║ {Fore.YELLOW} \\_____|_| |_| |_|\\__,_|_|_|  {Fore.GREEN}|_____/ \\__,_|_.__/    {Fore.CYAN}      ║
{Fore.CYAN}║                                                               ║
{Fore.CYAN}║ {Fore.WHITE}Subscription Audit & Cancellation Agent                      {Fore.CYAN}║
{Fore.CYAN}║ {Fore.WHITE}Powered by AWS Strands & Amazon Nova                         {Fore.CYAN}║
{Fore.CYAN}╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_section_header(title):
    """Print a formatted section header."""
    width = 60
    print(f"\n{Fore.CYAN}{'═' * width}")
    print(f"{Fore.CYAN}  {title}")
    print(f"{Fore.CYAN}{'═' * width}")

def format_currency(amount, currency='USD'):
    """Format a currency amount with the appropriate symbol."""
    if amount is None:
        return "N/A"
    
    symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€'
    }
    
    symbol = symbols.get(currency, '$')
    return f"{symbol}{amount:.2f}"

def format_date(date_obj):
    """Format a date object to a readable string."""
    if date_obj is None:
        return "N/A"
    
    return date_obj.strftime("%b %d")

def main():
    """Main function to run the Gmail Subscription Agent."""
    parser = argparse.ArgumentParser(description='Gmail Subscription Audit & Cancellation Agent')
    parser.add_argument('--days', type=int, default=365, help='Number of days back to search')
    parser.add_argument('--max-results', type=int, default=500, help='Maximum number of results per query')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region for Bedrock')
    parser.add_argument('--profile', type=str, default='default', help='AWS profile name')
    parser.add_argument('--export', type=str, help='Export results to CSV file')
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Create the agent
    print(f"{Fore.WHITE}Initializing Gmail Subscription Agent...")
    agent = GmailSubAgent(region=args.region, profile_name=args.profile)
    
    # Check/request Gmail authentication
    print_section_header("Gmail Authentication")
    print(f"{Fore.WHITE}Checking Gmail authentication...")
    
    # Create a progress spinner
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spinner_idx = 0
    
    # Try to authenticate
    auth_success = False
    try:
        auth_success = agent.gmail_scanner.authenticate()
    except Exception as e:
        print(f"{Fore.RED}Error during authentication: {e}")
    
    if auth_success:
        print(f"{Fore.GREEN}✓ Gmail authentication successful")
    else:
        print(f"{Fore.RED}✗ Gmail authentication failed")
        print(f"{Fore.YELLOW}Please ensure you have:")
        print(f"{Fore.YELLOW}1. Created a Google Cloud project")
        print(f"{Fore.YELLOW}2. Enabled the Gmail API")
        print(f"{Fore.YELLOW}3. Created OAuth credentials")
        print(f"{Fore.YELLOW}4. Downloaded credentials.json to the config/ directory")
        sys.exit(1)
    
    # Scan Gmail for subscriptions
    print_section_header("Scanning Gmail")
    print(f"{Fore.WHITE}Scanning for subscription emails (last {args.days} days)...")
    
    # Show scanning progress with spinner
    progress_thread = None
    try:
        # Scan for subscriptions
        subscriptions = agent.scan_gmail(days_back=args.days, max_results=args.max_results)
        
        print(f"{Fore.GREEN}✓ Scan complete! Found {len(subscriptions)} subscriptions")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error during scan: {e}")
        sys.exit(1)
    
    # Display results
    if subscriptions:
        print_section_header("📊 SUBSCRIPTION AUDIT RESULTS")
        
        # Filter active subscriptions
        active_subs = [s for s in subscriptions if s.get('is_active', False)]
        
        # Prepare table data
        table_data = []
        for sub in active_subs:
            service_name = sub.get('service_name', 'Unknown')
            amount = format_currency(sub.get('amount'), sub.get('currency', 'USD'))
            frequency = sub.get('billing_frequency', 'Unknown')
            last_charged = format_date(sub.get('last_email_date'))
            
            table_data.append([service_name, amount, frequency, last_charged])
        
        # Sort by service name
        table_data.sort(key=lambda x: x[0])
        
        # Print active subscriptions table
        print(f"\n{Fore.GREEN}Active Subscriptions Found:")
        print(tabulate(
            table_data,
            headers=['Service', 'Cost', 'Frequency', 'Last Charged'],
            tablefmt='pretty'
        ))
        
        # Get summary data
        summary = agent.get_summary()
        total_monthly = summary.get('total_monthly_cost', 0)
        annual_projection = summary.get('annual_projection', 0)
        
        # Print summary statistics
        print(f"\n{Fore.YELLOW}💰 Monthly Total: {format_currency(total_monthly)}")
        print(f"{Fore.YELLOW}📅 Annual Projection: {format_currency(annual_projection)}")
        
        # Print unused subscriptions
        unused_subs = summary.get('unused_subscriptions', [])
        if unused_subs:
            print(f"\n{Fore.RED}⚠️  Unused Subscriptions (no emails in 60+ days):")
            for sub in unused_subs:
                service = sub.get('service_name', 'Unknown')
                cost = format_currency(sub.get('monthly_cost'), sub.get('currency', 'USD'))
                frequency = sub.get('billing_frequency', 'month').lower()
                print(f"{Fore.RED}- {service} ({cost}/{frequency})")
        
        # Print free trials ending soon
        trials = summary.get('trials_ending_soon', [])
        if trials:
            print(f"\n{Fore.MAGENTA}🔔 Free Trials Ending Soon:")
            for trial in trials:
                service = trial.get('service_name', 'Unknown')
                end_date = format_date(trial.get('trial_end_date'))
                print(f"{Fore.MAGENTA}- {service} (Ends: {end_date})")
        
        # Export to CSV if requested
        if args.export:
            export_path = args.export
            if not export_path.endswith('.csv'):
                export_path += '.csv'
            
            if agent.export_to_csv(export_path):
                print(f"\n{Fore.GREEN}✓ Results exported to {export_path}")
            else:
                print(f"\n{Fore.RED}✗ Failed to export results")
    else:
        print(f"\n{Fore.YELLOW}No subscription data found in your Gmail account.")

if __name__ == "__main__":
    main()
