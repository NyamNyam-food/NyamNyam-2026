# Nyam Nyam 🍓

A full-stack meal discovery application based on the supplied *Meal Suggestion Web Application* coursework report. **All website UI text is in English.**

## Stack
- React 18 + Vite + React Router + Leaflet (OpenStreetMap tiles)
- Django 5 + Django REST Framework + Django sessions and CSRF
- PostgreSQL (SQLite fallback for local development)

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations app
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser  # optional, for administrator
python manage.py runserver
```

### Frontend (second terminal)
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173**. The Vite dev server proxies `/api` to Django.

Demo users: `demo` / `DemoPass123!` (customer), `owner` / `OwnerPass123!` (restaurant owner). **Change demo passwords or remove demo accounts before deployment.**

### PostgreSQL (recommended, as specified by report)
Create a PostgreSQL database, then configure these environment variables for the backend:
```bash
POSTGRES_DB=nyamnyam
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_SECRET_KEY=your-long-random-secret
DEBUG=1
```
If `POSTGRES_DB` is absent, local SQLite is used for convenience.

## Implemented use cases
- Customer registration, login, logout, profile deletion, onboarding survey, taste vector generation and profile updates
- Filtered meal recommendations and persistent recommendation history with selective or full deletion
- Recipe listing, creation, editing via API, deletion, cost field, ingredients and steps
- Restaurant listing, creation, editing via API, deletion, menu management and OpenStreetMap display
- Reviews, ratings, edit via API, deletion and administrator moderation log
- Administrator user list, survey inspection, user deletion, Django admin console

## API routes
`/api/csrf/`, `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/account/`, `/api/recipes/`, `/api/recipes/<id>/`, `/api/restaurants/`, `/api/restaurants/<id>/`, `/api/restaurants/<id>/menu/`, `/api/menu/<id>/`, `/api/reviews/`, `/api/reviews/<id>/`, `/api/recommendations/`, `/api/geocode/?q=...`, `/api/admin/users/`.

## Tests
```bash
cd backend
python manage.py test
```

## Important implementation boundaries
This is a functional **coursework starter implementation**, not a verified production deployment. The taste profile uses normalized weighted features and a cosine-friendly vector, while ranking is **PageRank-inspired weighted scoring**, not a graph PageRank or trained KNN/ANN model. Grocery pricing is a manually entered cost estimate, **not a live grocery price API**. The Nominatim geocoding endpoint is available, but automatic distance-based filtering and restaurant verification are not implemented. Demo restaurants and addresses are **fictional sample entries**, not verified businesses. Avoid treating demo prices or restaurant locations as real-world facts. Production readiness needs deployment hardening, more tests, rate limiting, and real integrations.

## Requirements traceability
| Report subsystem | Implementation |
| --- | --- |
| User preference & onboarding | Registration form, profile editor, `taste_vector` |
| Smart recommendation matching | Discover page, ranking logic, saved history |
| Home recipe generation | Recipe CRUD endpoints, ingredients, steps, cost |
| Restaurant discovery & menus | Restaurant catalog, owner CRUD, menu items, Leaflet map |
| Feedback | Review endpoints, star ratings, moderator removal |

## Security notes
Passwords are hashed by Django; role permissions are checked server-side. Session authentication requires CSRF for mutations. `DEBUG=1` and the default secret key are development-only. HTTPS, secure cookie settings, CORS origin restrictions, audit retention and backups must be configured for production.

## October 2026 algorithm upgrade and diagram archive
The `reference_diagrams/` directory contains all 39 supplied UML/architecture/schema JPGs from `info.zip` for traceability.

- **Taste vectors**: six-dimensional L2-normalized flavor/budget representation.
- **K-nearest matching**: cosine similarity of normalized taste vectors, with seven nearest candidates influencing graph edge weights. This is a deterministic nearest-neighbor method, not a trained neural network or an approximate nearest-neighbor index.
- **PageRank**: genuine damped weighted graph power iteration (not just a weighted scoring formula); personalized recommendation score combines its output with taste similarity, ratings, affordability, cuisine and distance.
- **Distance**: great-circle haversine distances and optional radius hard filter; browser geolocation requires user permission. Restaurants without coordinates cannot match a location-constrained request.
- **Cost**: `/api/recipes/estimate/` computes quantity × unit price from an admin-maintained ingredient reference catalog and explicitly reports missing ingredients. **There is no verified live grocery-price provider configured**; adding a live provider requires a real documented API and credentials. Unverified grocery prices are never presented as live data.
- **Pantry**: `/api/pantry/` GET/POST, `/api/pantry/<id>/` PATCH/DELETE; per-user ownership checks and pantry page in React.
- **Prices**: `/api/ingredient-prices/` GET public and POST admin only. Structured ingredient format: `[{"name":"Rice","quantity":0.5,"unit":"kg"}]`.

**Important:** The code has been checked for Python syntax, but a complete Django integration run and React production build could not be executed in this environment because external package registries were unreachable. Treat this as an expanded, unverified source project, **not a certified fully tested production release**. The diagrams are source specifications, not a guarantee that every branch has been implemented. No external API key or provider for real-time grocery prices was supplied. For real deployment, validate all flows and replace demo data, credentials and development settings.

## Live grocery price API (Open Prices)

The **Live prices** page (login required) queries `https://prices.openfoodfacts.org/api/v1/prices` directly from the Django server. It uses real product barcodes, checks EUR and Lithuanian country metadata, chooses the most recently dated compatible price, converts mass/count units, and shows provenance and missing items. Endpoint: `POST /api/recipes/estimate-live/`.

Example JSON: `{"country":"LT","currency":"EUR","ingredients":[{"name":"Pasta","barcode":"YOUR_REAL_BARCODE","quantity":2,"unit":"piece"}]}`.

Only `KILOGRAM` and `UNIT` quotes are currently handled. A piece cannot be converted to grams without actual package weight; liter-based quotes are not guessed. Some products/locations have no matching price and return a partial total with `complete: false`. The API is crowdsourced, not a guaranteed real-time retailer feed. Set `OPEN_PRICES_USER_AGENT` to a descriptive application user-agent including a contact address before deployment. Respect Open Prices API limits and ODbL attribution; production use should add server-side caching. This endpoint does not automatically overwrite a recipe's stored cost, to avoid treating incomplete totals as verified prices.
