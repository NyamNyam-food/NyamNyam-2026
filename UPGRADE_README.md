# Nyam Nyam integrated upgrade

This is a development build, **not a verified production release**.

## Included
- Existing PageRank power-iteration and KNN-style taste matching in `backend/app/logic.py`.
- Existing Open Food Facts / Open Prices ingredient price API integration, with explicitly marked reference estimates where available. Price availability depends on third-party coverage; missing prices are never presented as real observations.
- New `GET /api/distance/route/?lat=...&lon=...&target_lat=...&target_lon=...` uses OSRM public routing API for driving distance. When unavailable it returns `distance_type=straight_line_fallback` with Haversine kilometres. Public demo API is not intended for heavy production usage.
- Nominatim address search and address-to-coordinate resolution on restaurant create/update, with explicit errors and map-pin fallback.
- Restaurant editing uses a form instead of browser prompt for name, description, cuisine and address.
- Unset restaurant and recipe photos use a clearly labeled neutral placeholder, not an unrelated stock image.

## Limitations / remaining work
- Live ingredient prices may not exist for arbitrary ingredients in Lithuania. The API does not guarantee coverage.
- Full React build and Django tests must pass locally before deploying; they were not confirmed during this build.
- Public OSM geocoding / OSRM APIs have rate limits and no uptime guarantees. Cache requests and use a contracted provider for production.
- Route endpoint is available, but restaurant discovery currently displays straight-line nearby distance. Integrating driving distances into each discovery card requires explicit user interaction to avoid overwhelming the public OSRM API.
- Some UML entities remain represented with JSON fields rather than distinct normalized tables. Full 100% UML correspondence is not yet established.
- Existing recommendation engine needs independently verified end-to-end data and safety tests.

## Run
Backend: `pip install -r requirements.txt`, `python manage.py migrate --run-syncdb`, `python manage.py test app`, `python manage.py runserver`.
Frontend: `npm ci`, `npm run build`, `npm run dev`.

Do not commit `.env`, `.venv`, database files, media uploads containing private information, or API credentials.
