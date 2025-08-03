# Trojan Telegram Bot

A Telegram bot that simulates Trojan's Solana trading interface with team address assignment and referral system.

## Features

- **Team Address Assignment**: Automatically assigns team addresses from a predefined pool
- **Referral System**: Two-tier referral tracking (direct and indirect referrals)
- **Trading Interface**: Main menu with trading buttons (Buy, Sell, Positions, etc.)
- **Rewards System**: Shows referral statistics and cashback information
- **User Management**: Tracks user data including SOL balance and rewards

## Setup

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Choose a name and username for your bot
   - Copy the bot token

2. Set environment variables:
   - Copy `.env.example` to `.env`
   - Set `BOT_TOKEN` to your bot token
   - Set `BOT_USERNAME` to your bot username (without @)

3. Run the bot:
   ```bash
   python main.py
   ```

## Bot Commands

- `/start` - Start the bot and get team address
- `/start ref_USERID` - Start with referral code

## Team Addresses

The bot uses these predefined team addresses:
- Team 1: `8rMj1dMR6tp428j7DaGUn6TpLi89fpdYNQEwqUzyFCe3`
- Team 2: `EATAgjcHTZxCaudus4VvktLRfxYjtHMbNLSnyDJYXtnt`

## Main Menu Buttons

- **Buy / Sell**: Trading interface
- **Positions / Limit Orders / DCA Orders**: Order management
- **Copy Trade / Sniper**: Advanced trading features
- **Trenches / Watchlist**: Portfolio management
- **Rewards**: View referral and cashback rewards
- **Withdraw / Settings**: Account management
- **Help / Refresh**: Support and refresh data