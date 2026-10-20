# Nyam Nyam stability patch

## Changes
- Frontend CSRF request helper reads current Django cookie and retries once after refreshing token on HTTP 403. Django rotates CSRF on login.
- React error boundary displays errors instead of an entirely blank screen.
- Recipe ingredient estimation first attempts Open Food Facts/Open Prices. If unavailable, it uses optional **illustrative**, editable `IngredientPrice` reference entries seeded by `seed_demo`; these are **not real-time supermarket prices**.
- Missing prices are still disclosed; the total never silently includes unknown costs.
- Restaurant menus are never fabricated for real businesses. Import mapped Kaunas restaurants using `python manage.py import_osm_restaurants --limit 60`. Imported businesses have no verified menus; owners can add them.

## Commands
Backend: `pip install -r requirements.txt`, `python manage.py migrate --run-syncdb`, `python manage.py seed_demo`, `python manage.py runserver`.
Frontend: `npm install`, `npm run dev`.
Restart both servers, log out and back in, and clear old browser site data if a stale CSRF cookie persists.

## Known gaps
- Live grocery prices are sparse, especially for generic ingredients in Lithuania. Reference fallback is only an illustrative estimate and must not be described as live pricing.
- No licensed real restaurant menus or images are bundled. Owners can upload their own photos and menus.
- Full browser integration and live external API tests have not been run in this environment.
