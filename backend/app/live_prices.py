"""Live grocery price quotes from Open Prices (Open Food Facts).

Ingredient identifiers must be actual product barcodes. No fuzzy product substitution.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
import requests

API = 'https://prices.openfoodfacts.org/api/v1/prices'
FACTORS = {'g': ('mass', Decimal('1')), 'kg': ('mass', Decimal('1000')),
           'ml': ('volume', Decimal('1')), 'l': ('volume', Decimal('1000')),
           'piece': ('count', Decimal('1')), 'unit': ('count', Decimal('1'))}


def convert(value, source, target):
    source, target = str(source).lower(), str(target).lower()
    if source not in FACTORS or target not in FACTORS or FACTORS[source][0] != FACTORS[target][0]:
        raise ValueError(f'Incompatible units: {source} and {target}')
    return Decimal(str(value)) * FACTORS[source][1] / FACTORS[target][1]


def live_recipe_cost(ingredients, currency='EUR', country='LT', session=None):
    if not isinstance(ingredients, list) or not ingredients or len(ingredients) > 30:
        raise ValueError('Provide between 1 and 30 ingredients.')
    if currency != 'EUR':
        raise ValueError('Only EUR is currently supported; no implicit FX conversion.')
    session = session or requests.Session()
    total = Decimal('0')
    details, missing = [], []
    for ingredient in ingredients:
        if not isinstance(ingredient, dict):
            raise ValueError('Each ingredient must be an object.')
        name = str(ingredient.get('name') or '').strip()[:120]
        barcode = str(ingredient.get('barcode') or '').strip()
        unit = str(ingredient.get('unit') or '').strip().lower()
        try:
            quantity = Decimal(str(ingredient.get('quantity')))
        except (InvalidOperation, TypeError):
            raise ValueError(f'Invalid quantity for {name or "ingredient"}.')
        if not quantity.is_finite() or quantity <= 0 or unit not in FACTORS:
            raise ValueError(f'Invalid quantity or unit for {name or "ingredient"}.')
        if not barcode.isdigit() or not 8 <= len(barcode) <= 14:
            missing.append({'name': name, 'reason': 'A valid product barcode (8–14 digits) is required.'})
            continue
        try:
            response = session.get(API, params={'product_code': barcode, 'page_size': 100},
                headers={'User-Agent': os.environ.get('OPEN_PRICES_USER_AGENT', 'NyamNyamCoursework/1.0 (student project)')}, timeout=12)
            response.raise_for_status()
            records = response.json().get('items', [])
        except (requests.RequestException, ValueError, AttributeError) as exc:
            missing.append({'name': name, 'reason': f'Price service unavailable: {type(exc).__name__}'})
            continue
        candidates = []
        for record in records:
            if str(record.get('product_code') or '') != barcode or record.get('currency') != currency:
                continue
            location = record.get('location') or {}
            if country and str(location.get('osm_address_country_code') or '').upper() != country.upper():
                continue
            try:
                price = Decimal(str(record['price']))
                if not price.is_finite() or price < 0:
                    continue
                price_per = str(record.get('price_per') or 'UNIT').upper()
                # Open Prices records prices per UNIT or KILOGRAM. No guessed pack weights.
                if price_per == 'KILOGRAM':
                    required = convert(quantity, unit, 'kg')
                    priced_unit = 'kg'
                elif price_per == 'UNIT':
                    required = convert(quantity, unit, 'piece')
                    priced_unit = 'piece'
                else:
                    continue
                date.fromisoformat(str(record.get('date')))
                candidates.append((record['date'], price, required, priced_unit, record))
            except (ValueError, TypeError, KeyError, InvalidOperation):
                continue
        if not candidates:
            missing.append({'name': name, 'barcode': barcode, 'reason': 'No compatible EUR price found in selected country. Check product, unit or location.'})
            continue
        latest = max(candidates, key=lambda x: x[0])
        day, price, required, priced_unit, record = latest
        subtotal = (price * required).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        total += subtotal
        details.append({'name': name, 'barcode': barcode, 'quantity': str(quantity), 'unit': unit,
                        'price': str(price), 'price_per': priced_unit, 'subtotal': str(subtotal),
                        'date': day, 'source': 'Open Prices', 'location': (record.get('location') or {}).get('osm_name', ''),
                        'source_url': f'https://prices.openfoodfacts.org/prices/{record["id"]}' if record.get('id') else 'https://prices.openfoodfacts.org/'})
    return {'currency': currency, 'country': country, 'estimated_cost': str(total.quantize(Decimal('.01'))),
            'complete': not missing, 'priced_ingredients': details, 'missing_prices': missing,
            'note': 'Observed crowdsourced prices, not guaranteed current store offers. Total is partial when complete=false.',
            'source': 'Open Prices / Open Food Facts (ODbL)'}
