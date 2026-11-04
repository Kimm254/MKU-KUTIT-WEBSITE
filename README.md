# MKU KUTIT Website

## Included features
- Public KUTIT homepage and membership registration
- Congratulations/welcome message after successful registration (no payment prompt)
- Protected admin login and dashboard
- Member list, search, CSV export and manual payment-status tracking
- Activities/events with optional poster upload
- Announcements
- Event gallery uploads
- Executive committee management
- SQLite for local testing; PostgreSQL for Render deployment

## Run locally on Windows
1. Extract this ZIP.
2. Open PowerShell or Command Prompt inside the extracted `MKU_KUTIT_Working_Website` folder.
3. Run `py -m pip install -r requirements.txt`
4. Run `py app.py`
5. Open `http://127.0.0.1:5000`

The local version uses SQLite automatically. It does not install a PostgreSQL driver, avoiding the Python 3.15 `psycopg[binary]` wheel error.

## Admin login locally
Set credentials before starting the app.

PowerShell:
```powershell
$env:SECRET_KEY="replace-with-a-long-random-secret"
$env:ADMIN_USERNAME="your-admin-name"
$env:ADMIN_PASSWORD="choose-a-strong-password"
py app.py
```

Then visit `http://127.0.0.1:5000/admin/login`.

## Deploy to Render with PostgreSQL
1. Push the extracted project files to a GitHub repository.
2. Create a Render Web Service from that repository.
3. Set Build Command to: `pip install -r requirements-render.txt`
4. Set Start Command to: `gunicorn app:app`
5. Add environment variables:
   - `SECRET_KEY` = a long random secret
   - `ADMIN_USERNAME` = your chosen admin username
   - `ADMIN_PASSWORD` = your strong admin password
   - `DATABASE_URL` = your Render PostgreSQL **Internal Database URL**
6. Deploy.

`requirements-render.txt` installs `psycopg2-binary` for PostgreSQL. The app converts Render's PostgreSQL URL to the matching SQLAlchemy driver.

## Important data note
Do not replace or delete an existing production database if it contains member registrations. `db.create_all()` creates missing tables but does not migrate changed columns or remove old data. Back up an existing database before changing deployments.
