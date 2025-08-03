# Telegram Bot Project

## Overview

This is a Python Telegram bot application that simulates Trojan's Solana trading interface. The bot is designed for a referral system where users can join via Telegram, receive team addresses from a predefined pool, and earn rewards through direct and indirect referrals. The application uses in-memory storage for user data and provides a comprehensive trading interface simulation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Architecture
- **Language**: Python 3.11
- **Framework**: python-telegram-bot library for Telegram Bot API integration
- **Architecture**: Single-file bot application with modular class-based design
- **Storage**: In-memory dictionary storage for user data and referral tracking
- **Configuration**: Environment variable based configuration with .env support

### Core Features
- **User Registration**: Automatic user creation on /start command with unique team address assignment
- **Referral System**: Two-tier referral tracking (direct and indirect referrals)
- **Team Address Assignment**: Automatic assignment from predefined address pool of 2 team addresses
- **Trading Interface**: Complete simulation of Trojan's trading interface with interactive buttons
- **Reward Tracking**: SOL balance, referral rewards, and cashback rewards tracking
- **Bot Commands**: Handles /start command with optional referral codes (ref_USERID format)

### Trading Interface Simulation
- **Main Menu**: Interactive keyboard with Buy, Sell, Positions, Limit Orders, DCA Orders
- **Advanced Features**: Copy Trade, Sniper, Trenches, Watchlist functionality
- **Account Management**: Withdraw, Settings, Help, and Refresh options
- **Rewards System**: Comprehensive rewards display with referral links and statistics

### Data Model
- **User Storage**: In-memory dictionary with user records including:
  - Telegram ID, username, team address
  - Referral tracking (referred_by, direct_referrals, indirect_referrals)  
  - Balances (sol_balance, referral_rewards, cashback_rewards, total_paid_rewards)
  - Timestamps (created_at, last_updated)

### Team Addresses Pool
- **Team 1**: 8rMj1dMR6tp428j7DaGUn6TpLi89fpdYNQEwqUzyFCe3
- **Team 2**: EATAgjcHTZxCaudus4VvktLRfxYjtHMbNLSnyDJYXtnt
- **Assignment Logic**: Alternating pattern (1-2-1-2-1-2...) based on user registration order

### Dependencies
- **python-telegram-bot**: Modern async Telegram Bot API wrapper
- **python-dotenv**: Environment variable management
- **logging**: Built-in Python logging for bot monitoring

### Development and Deployment
- **Environment**: Replit-optimized Python environment
- **Configuration**: Environment variables for BOT_TOKEN and BOT_USERNAME
- **Logging**: Comprehensive logging for user registration and bot operations
- **Error Handling**: Graceful error handling with user-friendly messages