"""
Web routes module for Mama Doner Mini App.

Single responsibility: HTTP request handlers and route definitions.
All database calls delegate to app.database.service.

Public API:
- router: aiohttp RouteTableDef with all registered routes
"""

import logging
from aiohttp import web
from aiogram.types import LabeledPrice

from app.database import service as db_service
from app.utils.files import read_file

logging.basicConfig(level=logging.INFO)

router = web.RouteTableDef()


@router.post('/api/create-invoice')
async def create_invoice(request: web.Request) -> web.Response:
    """Create and return Telegram Stars invoice link for payment.

    Expects JSON body:
    {
        "cart": [
            {"id": 1, "count": 2, "price": 120.0, "name": "..."},
            ...
        ]
    }

    Returns:
    {
        "invoice_link": "https://..."
    }
    """
    try:
        data = await request.json()
        cart = data.get('cart', [])

        if not cart:
            return web.json_response({'error': 'Cart is empty'}, status=400)

        db_path = request.app['db_path']
        menu_items = await db_service.fetch_menu(db_path)
        menu_map = {item['id']: item for item in menu_items}

        provider_token = request.app['provider_token']
        currency = request.app['currency']
        bot = request.app['bot']

        prices = []

        for item in cart:
            menu_item = menu_map.get(item['id'])
            if menu_item:
                count = item.get('count', 1)
                if count > 0:
                    label = f"{menu_item['name']} (x{count})" if count > 1 else menu_item['name']
                    # Telegram requires amount in smallest currency units (cents)
                    amount = int(menu_item['price'] * count * 100)
                    prices.append(LabeledPrice(label=label, amount=amount))

        if not prices:
            return web.json_response({'error': 'Unable to generate invoice'}, status=400)

        # Save draft order
        order_id = await db_service.save_pending_cart(db_path, cart)

        try:
            link = await bot.create_invoice_link(
                title="Mama Doner Order",
                description=f"Order #{order_id}",
                payload=str(order_id),
                provider_token=provider_token,
                currency=currency,
                prices=prices,
                need_name=True,
                need_phone_number=True,
                is_flexible=False
            )
        except Exception as telegram_error:
            logging.error(f"Telegram Invoice Error: {telegram_error}")
            return web.json_response(
                {'error': f"Telegram API Error: {str(telegram_error)}"},
                status=500
            )

        return web.json_response({'invoice_link': link})

    except Exception as e:
        logging.error('Server Error: %s', e, exc_info=True)
        return web.json_response({'error': f'Internal server error: {str(e)}'}, status=500)


@router.get('/api/menu')
async def api_get_menu(request: web.Request) -> web.Response:
    """GET /api/menu - Return list of all active menu items."""
    try:
        menu = await db_service.fetch_menu(request.app['db_path'])
        return web.json_response(menu)
    except Exception as e:
        logging.error('API Error: %s', e)
        return web.json_response({'error': str(e)}, status=500)


@router.get('/api/categories')
async def api_get_categories(request: web.Request) -> web.Response:
    """GET /api/categories - Return list of all menu categories."""
    try:
        categories = await db_service.fetch_categories(request.app['db_path'])
        return web.json_response(categories)
    except Exception as e:
        logging.error('API Categories Error: %s', e)
        return web.json_response({'error': str(e)}, status=500)


@router.get('/')
async def index_handler(request: web.Request) -> web.Response:
    """GET / - Serve index.html."""
    content = read_file('static/index.html')
    if content is None:
        return web.Response(text='index.html not found', status=404)
    return web.Response(text=content, content_type='text/html')
