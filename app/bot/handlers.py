"""
Bot handlers module for Mama Doner Mini App.

Single responsibility: registers Aiogram handlers and orchestrates bot logic.
Delegates database operations to app.database.service module.

Public API:
- register_handlers(dispatcher, bot, db_path, webapp_url, admin_ids)
"""

import logging
from typing import Optional, List

from aiogram import types, F, Dispatcher, Bot
from aiogram.filters import Command

from app.database import service as db_service

logging.basicConfig(level=logging.INFO)


def register_handlers(
    dp: Dispatcher,
    bot: Bot,
    db_path: str,
    webapp_url: str,
    admin_ids: Optional[List[int]] = None
) -> None:
    """Register all bot handlers on the provided Dispatcher instance.

    Args:
        dp: Aiogram Dispatcher instance.
        bot: Aiogram Bot instance.
        db_path: Path to SQLite database file.
        webapp_url: URL to the Telegram Mini App web interface.
        admin_ids: List of admin user IDs for privileged commands. Defaults to empty list.
    """
    if admin_ids is None:
        admin_ids = []

    async def cmd_start(message: types.Message) -> None:
        """Handle /start command - show welcome message with web app button."""
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text="Order Food",
                        web_app=types.WebAppInfo(url=webapp_url)
                    )
                ]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "Welcome!\nTap the button below to open the menu.",
            reply_markup=keyboard
        )

    async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery) -> None:
        """Handle pre-checkout query - Telegram asks for payment confirmation."""
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    async def process_successful_payment(message: types.Message) -> None:
        """Handle successful payment - save order and send receipt to user."""
        payment_info = message.successful_payment
        if payment_info is None:
            await message.answer("Error: Payment information is not available.")
            return
        total_amount = payment_info.total_amount / 100.0
        currency = payment_info.currency
        payload = payment_info.invoice_payload

        try:
            # Payload is str(order_id), load cart from database
            order_id = int(payload)
            cart_items = await db_service.fetch_pending_cart(db_path, order_id)
            if not cart_items:
                await message.answer("Error: Order not found. Please contact support.")
                return
        except ValueError:
            await message.answer("Error: Invalid order payload.")
            return

        # Save order to database
        if message.from_user is None:
            await message.answer("Error: User information is not available.")
            return
        await db_service.save_order(
            db_path=db_path,
            user_id=message.from_user.id,
            cart_items=cart_items,
            total_price=total_amount
        )

        # Delete pending order after successful payment
        await db_service.delete_pending_cart(db_path, order_id)

        # Format and send receipt
        currency_symbol = 'Br' if currency == 'BYN' else currency
        receipt_text = '✓ <b>Payment Successful!</b>\n\n'
        receipt_text += '📋 <b>Your Receipt:</b>\n'
        for item in cart_items:
            line_total = item['price'] * item['count']
            receipt_text += f"• {item['name']} x{item['count']} — {line_total:.2f} {currency_symbol}\n"
        receipt_text += f"\n<b>Total Paid: {total_amount:.2f} {currency_symbol}</b>"
        receipt_text += "\n\nThe kitchen is preparing your order!"

        await message.answer(receipt_text, parse_mode='HTML')

    async def cmd_add_item(message: types.Message) -> None:
        """Handle /add command - admin-only menu item addition."""
        if message.from_user is None:
            await message.answer('Error: User information is not available.')
            return
        if message.from_user.id not in admin_ids:
            await message.answer('You do not have administrator permissions.')
            return

        try:
            if message.text is None:
                await message.answer('Error: Message does not contain text.')
                return
            parts = message.text.split()
            if len(parts) < 6:
                await message.answer(
                    "Usage: /add <name> <price> <category> <emoji> <description>"
                )
                return

            name = parts[1]
            price = float(parts[2])
            category = parts[3]
            emoji = parts[4]
            description = " ".join(parts[5:])

            try:
                await db_service.add_menu_item(db_path, name, price, description, category, emoji)
                await message.answer(f"Menu item '{name}' added successfully.")
            except ValueError as ve:
                reason = str(ve)
                if reason == 'exists':
                    await message.answer(f"Menu item '{name}' already exists.")
                elif reason == 'invalid_price':
                    await message.answer('Error: Invalid price.')
                elif reason == 'invalid_name':
                    await message.answer('Error: Invalid menu item name.')
                else:
                    await message.answer('Cannot add menu item: invalid data provided.')
        except ValueError:
            await message.answer('Error: Price must be a number.')
        except Exception as e:
            logging.error('Error adding menu item: %s', e, exc_info=True)
            await message.answer('An error occurred while adding menu item. Check server logs.')

    async def cmd_delete_item(message: types.Message) -> None:
        """Handle /del command - admin-only menu item deletion."""
        if message.from_user is None:
            await message.answer('Error: User information is not available.')
            return
        if message.from_user.id not in admin_ids:
            await message.answer('You do not have administrator permissions.')
            return

        try:
            if message.text is None:
                await message.answer('Error: Message does not contain text.')
                return
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.answer('Usage: /del <dish_name>')
                return

            item_name = parts[1]
            deleted = await db_service.delete_menu_item(db_path, item_name)
            if not deleted:
                await message.answer(f"Menu item '{item_name}' not found.")
                return
            await message.answer(f"Menu item '{item_name}' deleted successfully.")
        except Exception as e:
            logging.error('Error deleting menu item: %s', e)
            await message.answer('An error occurred while deleting menu item.')

    # Register handlers with dispatcher
    dp.message.register(cmd_start, Command('start'))
    dp.pre_checkout_query.register(process_pre_checkout_query)
    dp.message.register(process_successful_payment, F.successful_payment)
    dp.message.register(cmd_add_item, Command('add'))
    dp.message.register(cmd_delete_item, Command('del'))
