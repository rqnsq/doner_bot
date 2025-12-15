"""
Main entry point for Mama Doner Mini App.

Responsibilities:
1. Initialize application configuration
2. Setup and start both web server and Telegram bot
3. Register database schema
4. Register bot handlers
"""

import asyncio
import logging
from aiohttp import web
try:
    import aiohttp_cors
    HAS_CORS = True
except ImportError:
    aiohttp_cors = None  # type: ignore
    HAS_CORS = False

from app.core.config import settings
from app.database import service as db_service
from app.web import routes as web_routes
from app.bot import handlers as bot_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup() -> tuple[web.AppRunner, web.Application]:
    """Initialize database, setup web server, and register bot handlers.

    Returns:
        Tuple of (AppRunner, Application) for lifecycle management.
    """
    # Initialize database schema and seed data
    await db_service.init_db(settings.DB_NAME)

    # Create aiohttp application and attach context
    app = web.Application()
    app['db_path'] = settings.DB_NAME
    app['bot'] = None  # Will be set by the caller if bot token exists
    app['provider_token'] = settings.PROVIDER_TOKEN
    app['currency'] = settings.CURRENCY

    # Register web routes
    app.add_routes(web_routes.router)

    # Add static file serving for CSS, JS, and other assets
    app.router.add_static('/static', path='static', name='static')

    # Setup CORS (allow all origins for simplicity) if aiohttp_cors is available
    if HAS_CORS and aiohttp_cors is not None:
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        for route in list(app.router.routes()):
            cors.add(route)

    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', settings.WEB_SERVER_PORT)
    await site.start()
    logger.info('Web server running on port %s', settings.WEB_SERVER_PORT)
    logger.info('WebApp URL should be configured as: %s', settings.WEBAPP_URL)

    return runner, app


async def main() -> None:
    """Start the application.

    Runs web server in all cases.
    If BOT_TOKEN is configured, also starts Telegram bot polling.
    """
    # Setup web server and database
    runner, app = await on_startup()

    # Initialize Telegram bot if token is provided
    if settings.BOT_TOKEN:
        from aiogram import Bot, Dispatcher
        
        bot = Bot(token=settings.BOT_TOKEN)
        dp = Dispatcher()
        
        # Attach bot to web app context for handlers to use (before app startup)
        app['bot'] = bot

        # Register bot handlers
        bot_handlers.register_handlers(
            dp=dp,
            bot=bot,
            db_path=settings.DB_NAME,
            webapp_url=settings.WEBAPP_URL,
            admin_ids=settings.ADMIN_IDS
        )

        logger.info('Starting Telegram bot polling...')
        
        try:
            # Remove any pending webhook and start polling
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        except Exception as e:
            logger.error('Bot polling error: %s', e, exc_info=True)
    else:
        # Run web-only mode (keep web server alive)
        logger.info('BOT_TOKEN not provided — running in web-only mode.')
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    asyncio.run(main())
