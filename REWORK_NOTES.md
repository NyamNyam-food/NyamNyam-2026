# Nyam Nyam UML-aligned revision (20 October 2026)

## Implemented in this revision
- All three roles can register/update dietary, allergy, and 0–10 flavor preferences. Admins are created via `python manage.py createsuperuser`; owner/customer via signup.
- Removed My Pantry and separate Live Prices from UI/API. Recipe creation still estimates named ingredient costs and labels reference estimates separately from verified observed prices.
- Removed stored typical meal budget from Profile; a per-search budget remains optional in recommendations.
- Today's mood uses a checklist. Recipes have mood labels and home recommendations can filter by them.
- Account deletion; admin account restriction/restoration; admin user deletion; flagged reviews with moderator hide/dismiss actions.
- Reviews accept star rating with or without text; authors can edit/delete their reviews.
- Restaurant creation supports selecting coordinates with a click on the map. Nearby search uses Haversine, independent of Overpass. Distances are straight-line, not walking/driving distances.
- Optional uploads for recipe, restaurant, and menu photos; menu item editing via the restaurant detail page.
- Recipe ingredient details show quantity, unit, and name.

## IMPORTANT: current limitations
- This is a substantial revision, NOT a certified 100% UML implementation. In particular, the class diagram's distinct RatingSummary, ReviewFlag attributes, TasteFilter, SurveyResponse, and RecipeIngredient relational entities are not all separate database tables; some are represented in JSON fields or computed views.
- Current rating displays are averages. The recommendation graph uses PageRank, but rating adjustment is not yet a dedicated PageRank-weighted RatingSummary model.
- Recipe price lookup is best-effort; no external service guarantees live supermarket ingredient prices. Seed prices are illustrative and explicitly labeled.
- No independently verified restaurant menus are supplied. Owners enter actual menus and prices.
- No end-to-end browser or Django integration suite was executed in this environment. Run checks below before publishing.
- The project has no checked-in Django migrations. For a fresh *development* SQLite database, `python manage.py migrate --run-syncdb` creates the new tables. For existing data, do NOT delete your database: create proper migrations and back up the database before migrating.

## Run locally
Backend (from backend/):
```
python -m pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py test app
python manage.py runserver
```
Frontend (from frontend/):
```
npm install
npm run build
npm run dev
```

If updating an older local SQLite database, first back it up. Existing schema needs migrations for the new mood/review fields; `--run-syncdb` does not alter existing tables. For a clean demonstration environment only, rename `backend/db.sqlite3` to a backup filename and rerun `migrate --run-syncdb`.

## Before GitHub
Review `git status` and ensure no `.env`, SQLite database, media uploads, `.venv`, or `node_modules` are staged. Never publish secrets or user-uploaded photos without consent.
