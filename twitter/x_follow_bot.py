#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import time
import json
import os
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("x_follow_bot.log"),
        logging.StreamHandler()
    ]
)

def login_to_twitter(page, username, password):
    """
    Log into X.com (Twitter) with the provided credentials.
    """
    logging.info("Logging into X.com...")
    page.goto("https://x.com/login")
    
    # Enter username
    page.wait_for_selector('input[autocomplete="username"]')
    page.fill('input[autocomplete="username"]', username)
    page.click('button[role="button"]:has-text("Next")')
    
    # Enter password
    page.wait_for_selector('input[type="password"]')
    page.fill('input[type="password"]', password)
    
    # Click login button
    page.click('div:has-text("Log in")')
    
    # Wait for login to complete
    try:
        # Wait for home timeline to appear
        page.wait_for_selector('div[data-testid="primaryColumn"]', timeout=30000)
        logging.info("Successfully logged in!")
        return True
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        
        # Check for verification or other challenges
        if page.is_visible('text=Verify your identity'):
            logging.info("Verification required. Please complete it manually.")
            # Wait for manual verification (adjust timeout as needed)
            page.wait_for_selector('div[data-testid="primaryColumn"]', timeout=120000)
            return True
        return False

def follow_accounts(page, accounts_list):
    """
    Follow each account in the provided list.
    """
    logging.info(f"Starting to follow {len(accounts_list)} accounts...")
    
    for account in accounts_list:
        try:
            # Remove @ from the username if present
            username = account.replace('@', '')
            logging.info(f"Visiting profile: {username}")
            
            # Go to the user profile
            page.goto(f"https://x.com/{username}")
            page.wait_for_load_state('networkidle')
            
            # Check if the account exists
            if page.is_visible('text=This account doesn\'t exist'):
                logging.info(f"Account @{username} doesn't exist. Skipping.")
                continue
            
            # Find the follow button
            follow_button_selector = 'div[data-testid="followButton"]'
            if page.is_visible(follow_button_selector):
                logging.info(f"Following @{username}...")
                page.click(follow_button_selector)
                
                # Confirm if there's a confirmation dialog (for protected accounts)
                try:
                    confirm_button = page.wait_for_selector('div[data-testid="confirmationSheetConfirm"]', timeout=3000)
                    if confirm_button:
                        confirm_button.click()
                        logging.info("Confirmed follow request for protected account")
                except Exception:
                    # No confirmation needed, continue
                    pass
            else:
                logging.info(f"Already following @{username} or cannot follow.")
            
            # Add delay between follows to avoid rate limiting
            delay = 2 + random.random() * 3  # 2-5 seconds
            time.sleep(delay)
            
        except Exception as e:
            logging.error(f"Error following {account}: {str(e)}")
    
    logging.info("Finished following all accounts!")

def main():
    """
    Main function to run the X.com follow bot.
    """
    try:
        # Read config file
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as file:
            config = json.load(file)
        
        if not config.get('username') or not config.get('password'):
            raise ValueError('Username and password must be provided in config.json')
        
        if not config.get('accounts_to_follow') or len(config['accounts_to_follow']) == 0:
            raise ValueError('No accounts specified to follow in config.json')
        
        with sync_playwright() as p:
            # Launch browser
            browser_type = p.chromium
            browser = browser_type.launch(
                headless=config.get('headless', False),
                slow_mo=100
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Login
            logged_in = login_to_twitter(page, config['username'], config['password'])
            if not logged_in:
                raise Exception('Failed to login. Please check your credentials.')
            
            # Follow accounts
            follow_accounts(page, config['accounts_to_follow'])
            
            # Close browser
            browser.close()
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
