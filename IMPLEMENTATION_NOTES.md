# Nyam Nyam: changes after usability review

## Roles
Public sign-up offers **Guest / Customer** and **Restaurant Owner**. Only customers complete the allergy, flavor and budget survey. Admins are deliberately **not self-registerable**: create them with `python manage.py createsuperuser`. An untrusted visitor selecting "admin" must never grant administrative privileges.

## Recipes and price estimates
The Create Recipe form now takes structured ingredient **names, quantities and units**. No barcode input. The backend searches Open Food Facts for a plausibly named product, then attempts to match its product code against observed Open Prices records in Lithuania. Cost is calculated **when saving**, not entered by the author. Results store the source and missing ingredients in `cost_details`. If a quote is incomplete, the displayed recipe cost is **unavailable** instead of treating a partial total as a complete cost.

**Known limitation:** Open Prices is crowdsourced and has sparse Lithuanian coverage. A named ingredient can match different brands or package formats. Unit prices cannot be converted to grams without an actual compatible per-kg observation. The API cannot guarantee a complete estimate for every recipe, current supermarket checkout prices, or a unique best product. This is an observed-price estimate, not an official store integration.

## Photos
Authenticated users can upload JPEG, PNG or WebP images (max 5 MB) from their device for recipe/restaurant creation. Uploaded media is served by Django in local DEBUG mode. In production, configure a media server/object storage, file scanning and access policy. Restaurant menu item upload field is included.

## Restaurants and geolocation
Use `python manage.py import_osm_restaurants --limit 60` to import **real mapped restaurant locations** from OpenStreetMap into the catalog. Imported entries identify OSM provenance and have **no invented menus**. They are not owner-verified. Restaurant owners can create their own pages, attach photos, select a geocoded address and manage menus. A third-party menu source or direct restaurant permission is needed to publish **verified menus and prices** for imported businesses. Geocoding uses Nominatim, which is rate-limited and needs a compliant deployment policy.

## Run
```
cd backend
pip install -r requirements.txt
python manage.py makemigrations app
python manage.py migrate
python manage.py createsuperuser
python manage.py import_osm_restaurants --limit 60
python manage.py runserver
```
In a separate terminal: `cd frontend && npm install && npm run dev`.

`seed_demo` creates demo accounts and sample recipes but **no fake restaurant listings**. Do not use demo accounts in a public deployment.

## Verification status
Python syntax compilation passed. Django migrations, automated Django tests, frontend bundling, API connectivity, browser interaction and live OpenStreetMap import have **not been executed in this environment**. The source requires an integration test pass before being represented as production-ready.
