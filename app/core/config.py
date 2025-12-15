"""
Configuration module for Mama Doner Mini App.

Single responsibility: centralize environment variable loading and application settings.
All configuration is loaded once at startup and made available to other modules.
"""

import os
import logging
from typing import List

logging.basicConfig(level=logging.INFO)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        """Initialize settings from environment."""
        # Telegram Bot Configuration
        self.BOT_TOKEN: str | None = os.environ.get('BOT_TOKEN')
        self.PROVIDER_TOKEN: str | None = os.environ.get('PROVIDER_TOKEN')
        self.WEBAPP_URL: str = os.environ.get('WEBAPP_URL', 'https://your-webapp-url.com')

        # Database Configuration
        self.DB_NAME: str = os.environ.get('DB_NAME', 'data/orders.db')

        # Web Server Configuration
        self.WEB_SERVER_PORT: int = int(os.environ.get('WEB_SERVER_PORT', 8080))

        # Payment Configuration
        self.CURRENCY: str = os.environ.get('CURRENCY', 'USD')

        # Admin IDs
        self._admin_ids_raw: str = os.environ.get('ADMIN_ID', '')
        self.ADMIN_IDS: List[int] = self._parse_admin_ids()

        # Validate critical settings
        self._validate()

    def _parse_admin_ids(self) -> List[int]:
        """Parse ADMIN_ID environment variable (single id or comma-separated)."""
        admin_ids = []
        if self._admin_ids_raw:
            for part in self._admin_ids_raw.split(','):
                try:
                    admin_ids.append(int(part.strip()))
                except (ValueError, AttributeError):
                    logging.warning('Invalid ADMIN_ID entry: %s', part)
        return admin_ids

    def _validate(self) -> None:
        """Validate critical configuration at startup."""
        if not self.BOT_TOKEN:
            logging.error('BOT_TOKEN is not set. The bot will not start without a token.')
        if not self.PROVIDER_TOKEN:
            logging.error(
                'PROVIDER_TOKEN (from @BotFather for BePaid) is not set. Payments will not work.'
            )


# Singleton instance to be imported across the app
settings = Settings()
