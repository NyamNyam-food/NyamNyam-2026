# Nyam Nyam: integrated candidate build

This archive contains the Django/React source, original diagrams, and an improved location feature. **It is not a certified production release.** Full end-to-end testing and live grocery-price verification are still necessary.

## Run locally

Python 3.11+, Node.js 20+, and optionally PostgreSQL. From `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations app
python manage.py migrate
python manage.py seed_demo
python manage.py test app
python manage.py runserver
```

From `frontend` in another terminal:

```powershell
npm install
npm run build
npm run dev
```

Visit http://localhost:5173. The geolocation feature needs localhost or HTTPS and browser permission. Restaurants must already have coordinates stored. Click **Restaurants → Restaurants near me** and select a radius. Distances are Haversine straight-line estimates, not driving or walking routes. No Overpass service is called during this request.

## PostgreSQL
Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` environment variables before running migrations. Without these, local SQLite is used for development.

## GitHub

```powershell
git init
git add .
git commit -m "Initial Nyam Nyam application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Create an empty GitHub repository first, and replace the example URL. Never commit `.env`, database files, uploaded user images, or secrets.

## Known limitations
- Live Open Prices has incomplete ingredient coverage; fallback prices are **illustrative**, not verified store quotes.
- OSM restaurant import can be rate limited; the local catalog and distance API work without it.
- Real restaurant menus and images must be supplied by verified owners or licensed sources; do not present demo data as real menus.
- Browser integration, PostgreSQL migration, and external API availability must be tested on the deployment environment.
