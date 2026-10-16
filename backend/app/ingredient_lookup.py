"""Best-effort public product search and observed price matching, never fabricated quotes."""
from decimal import Decimal, InvalidOperation
from .live_prices import live_recipe_cost
from .models import IngredientPrice
import requests

SEARCH = 'https://world.openfoodfacts.org/cgi/search.pl'

def estimate_named_ingredients(items, country='LT', session=None):
    if not isinstance(items, list) or not 1 <= len(items) <= 25:
        raise ValueError('Provide 1–25 ingredients.')
    session = session or requests.Session()
    details, missing, estimated = [], [], []
    total = Decimal('0')
    for raw in items:
        if not isinstance(raw, dict):
            raise ValueError('Ingredients must be objects with name, quantity and unit.')
        name = str(raw.get('name', '')).strip()
        unit = str(raw.get('unit', 'g')).lower()
        try: qty = Decimal(str(raw.get('quantity', 0)))
        except (InvalidOperation, TypeError): raise ValueError(f'Invalid quantity: {name}')
        if not name or len(name)>100 or not qty.is_finite() or qty<=0 or unit not in ('g','kg','ml','l','piece'):
            raise ValueError('Each ingredient needs a name, positive quantity and valid unit.')
        try:
            r=session.get(SEARCH, params={'search_terms':name,'search_simple':1,'action':'process','json':1,'page_size':12,'fields':'code,product_name,quantity'}, timeout=3,headers={'User-Agent':'NyamNyam/1.0 (coursework; product lookup)'})
            r.raise_for_status()
            products=r.json().get('products',[])
        except (requests.RequestException, ValueError, AttributeError):
            products=[]
        # Only accept plausible product names; no fuzzy substitution that silently changes ingredients.
        candidates=[p for p in products if name.casefold() in str(p.get('product_name','')).casefold() and str(p.get('code','')).isdigit()]
        quote=None
        for product in candidates[:5]:
            result=live_recipe_cost([{'name':name,'barcode':product['code'],'quantity':str(qty),'unit':unit}],country=country,session=session)
            if result['complete']:
                quote=result['priced_ingredients'][0]
                quote['matched_product']=product.get('product_name','')
                break
        if quote:
            total+=Decimal(quote['subtotal']);details.append(quote)
        else:
            # Optional, explicitly labeled fallback to editable reference estimates.
            # Never misrepresent these estimates as live prices.
            from .live_prices import convert
            reference=IngredientPrice.objects.filter(name__iexact=name).first()
            if reference:
                try:
                    amount=convert(qty,unit,reference.unit)
                    subtotal=(amount*reference.price).quantize(Decimal('.01'))
                    total+=subtotal
                    estimated.append({'name':name,'quantity':str(qty),'unit':unit,
                                      'subtotal':str(subtotal),'source':reference.source,
                                      'price_per':reference.unit,'reference_price':str(reference.price),
                                      'updated':reference.updated.date().isoformat()})
                except ValueError:
                    missing.append({'name':name,'reason':'No compatible price unit in reference catalog'})
            else:
                missing.append({'name':name,'reason':'No observed or reference price available'})
    return {'estimated_cost':str(total.quantize(Decimal('.01'))),'currency':'EUR','complete':not missing,
        'priced_ingredients':details,'reference_estimates':estimated,'missing_prices':missing,'source':'Open Prices + optional editable reference estimates',
        'note':'Live observed prices when available. Reference estimates are illustrative and not verified store offers. Missing items are excluded.'}
