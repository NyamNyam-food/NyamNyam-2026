# Nyam Nyam Complete Studio: verification status

This is a substantial working-source iteration, **not a certified production release**.

## Functionality
- Django REST Framework and React application with customer, restaurant owner and staff roles.
- Profile flavors, dietary preferences and allergies, mood-aware recipes, CRUD, reviews, moderation and recommendation history.
- Weighted PageRank iteration + taste similarity; unknown-price recipes and menu-less restaurants remain discoverable without inventing costs or declaring unverified items allergy-safe.
- Open Food Facts / Open Prices API with optional clearly marked illustrative reference estimates. Live grocery price coverage is not guaranteed.
- Nominatim address lookup, Leaflet restaurant map and map pin, Haversine radius search and optional OSRM road-distance endpoint. Geolocation is optional; users can enter a street address.
- No Overpass dependency for browsing or calculating distance.

## Important limitations
- Full end-to-end test coverage and deployment hardening remain necessary.
- Real restaurants and real menus are not fabricated; add them via owner accounts or verified import.
- Public geocoding, routing and price APIs can rate-limit or fail.
- Cost cannot be asserted when ingredient prices are missing.
- A restaurant without a published menu cannot be certified safe for allergy/diet filters.

## Commands
Backend: `cd backend && pip install -r requirements.txt && python manage.py migrate --run-syncdb && python manage.py test app && python manage.py runserver`
Frontend: `cd frontend && npm install && npm run build && npm run dev`

Do not commit secrets, `.env`, local databases or private media.

## Verification in this build environment
Python compileall passed. npm installation timed out due to unavailable dependency download; frontend build and Django integration tests are **not** verified.
