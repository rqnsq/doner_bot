# Doner - Telegram Mini App

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-0066CC?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

Full-featured food delivery application built as a Telegram Mini App with embedded web interface.

## Overview

Doner is a complete food ordering system that operates entirely within Telegram. Users can browse menus, manage shopping carts, and process payments without leaving the messaging app. Administrators can manage menu items through simple bot commands.

The application is built with:
- **Aiogram 3.x** for Telegram bot functionality
- **Aiohttp** for the web server and REST API
- **Aiosqlite** for asynchronous database operations
- **SQLite** for data persistence
- **Vanilla JavaScript** for frontend logic

## Features

### User Features
- Interactive web menu with real-time search
- Shopping cart with quantity management
- Secure payment processing via Telegram Payments API
- Complete order history and receipts
- Responsive design optimized for mobile

### Administrator Features
- Menu item management (`/add`, `/del` commands)
- Data validation for prices and item properties
- Complete action logging for audit purposes
- Simple command-based interface

### Technical Features
- Asynchronous architecture for handling concurrent users
- SQLite database for order and menu persistence
- Docker containerization for easy deployment
- CORS support for cross-domain requests
- Error handling and logging throughout the application

## Quick Start

### Using Docker

```bash
git clone https://github.com/yourusername/doner.git
cd doner
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d --build
```

The application will be available at http://localhost:8080

### Local Development

```bash
git clone https://github.com/yourusername/doner.git
cd doner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python -m app.main
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather
PROVIDER_TOKEN=your_payment_provider_token
WEBAPP_URL=http://localhost:8080
ADMIN_ID=123456789

# Application
CURRENCY=USD
WEB_SERVER_PORT=8080
DB_NAME=data/orders.db
```

### Getting Started with Tokens

**BOT_TOKEN**: Contact @BotFather on Telegram and use `/newbot` command

**PROVIDER_TOKEN**: Configure payments at @BotFather under your bot's Payments section

**ADMIN_ID**: Check application logs after sending a message to your bot

## Project Structure

```
doner/
├── app/
│   ├── main.py                 # Application entry point
│   ├── core/config.py          # Configuration management
│   ├── bot/handlers.py         # Telegram bot command handlers
│   ├── database/service.py     # Database operations
│   ├── web/routes.py           # HTTP API routes
│   └── static/                 # Frontend assets
│       ├── index.html
│       ├── js/script.js
│       └── css/styles.css
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE
```

## Database Schema

### orders
- id: INTEGER PRIMARY KEY
- user_id: INTEGER
- items_json: TEXT
- total_price: REAL
- timestamp: DATETIME

### menu
- id: INTEGER PRIMARY KEY
- name: TEXT UNIQUE
- price: REAL
- description: TEXT
- category: TEXT
- emoji: TEXT

### pending_orders
- id: INTEGER PRIMARY KEY
- cart_json: TEXT
- created_at: DATETIME

## Administrator Commands

### Add Menu Item
```
/add Pizza 15.99 MainCourse "Fresh Italian pizza"
```

### Delete Menu Item
```
/del Pizza
```

## Deployment

### Docker Compose

```bash
docker-compose up -d --build
docker-compose logs -f
```

### Manual VPS Deployment

```bash
git clone https://github.com/rqnsq/doner_bot
cd doner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure .env
nohup python -m app.main > app.log 2>&1 &
```

### Process Management with Supervisor

Create configuration file:
```ini
[program:doner]
directory=/path/to/doner
command=/path/to/venv/bin/python -m app.main
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/doner.log
```

Then:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start doner
```

## Architecture

The application follows a three-layer architecture:

1. **Frontend Layer**: Telegram Mini App with HTML/CSS/JavaScript
2. **Application Layer**: Python async backend (Aiogram + Aiohttp)
3. **Data Layer**: SQLite database

## Security

- Sensitive data stored in environment variables only
- `.env` file excluded from Git (see `.gitignore`)
- `.env.example` contains no real credentials
- Database files excluded from version control
- No sensitive data logged or displayed

## Troubleshooting

### Application won't start
- Check BOT_TOKEN is set correctly
- Verify Python 3.9+ is installed
- Check all dependencies: `pip list`

### Web interface not accessible
- Verify WEB_SERVER_PORT is open
- Check WEBAPP_URL matches your setup
- Review logs: `docker-compose logs`

### Database issues
- SQLite database is auto-created
- Reset with: `rm data/orders.db`
- Check file permissions: `chmod -R 755 data/`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For issues or questions:
1. Review the configuration in `.env`
2. Check application logs
3. Verify environment variables are set correctly
4. Ensure all dependencies are installed

## Contributing

Contributions are welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

rqn





