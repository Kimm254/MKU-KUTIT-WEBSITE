MKU KUTIT WEBSITE + ADMIN DASHBOARD
===================================

FEATURES
- Public student registration form
- Database-backed member records (PostgreSQL on Render; SQLite locally)
- Admin login
- Member search
- Payment status tracking (manual Paid/Pending)
- CSV export
- Responsive public website

LOCAL RUN (Windows)
1. Extract this ZIP.
2. Open the extracted folder in File Explorer.
3. Click the address bar, type cmd, press Enter.
4. Run:
   py -m pip install -r requirements.txt
   py app.py
5. Visit http://127.0.0.1:5000
6. Local SQLite database is created as kutit_local.db.

ADMIN LOGIN SETUP
For local testing, set environment variables in the same CMD window before starting:
   set ADMIN_USERNAME=kutitadmin
   set ADMIN_PASSWORD=Choose-A-Long-Unique-Password
   set SECRET_KEY=Use-A-Long-Random-Secret-Value
   py app.py

Open:
   http://127.0.0.1:5000/admin

RENDER DEPLOYMENT
1. Replace the files in your existing GitHub repository with the contents of this ZIP.
2. Commit the changes. Render should redeploy automatically.
3. In Render, create a PostgreSQL database (New + -> PostgreSQL).
4. Copy its Internal Database URL.
5. Open your web service -> Environment and add:
   DATABASE_URL = [Internal Database URL]
   ADMIN_USERNAME = [your chosen admin username]
   ADMIN_PASSWORD = [a long unique password]
   SECRET_KEY = [a long random secret]
6. Save changes / redeploy.
7. Visit https://YOUR-SERVICE.onrender.com/admin

IMPORTANT SECURITY & DATA NOTES
- Do not share ADMIN_PASSWORD or SECRET_KEY.
- Do not put secrets in HTML, GitHub files, or screenshots.
- Use a strong, unique admin password.
- Use the PostgreSQL Internal Database URL in the Render web service environment.
- Confirm the PostgreSQL database is in the same Render region as the web service.
- Existing registrations stored in the old CSV or temporary Render filesystem are NOT automatically imported into the new database. Export/back up any existing registrations before replacing the old app.
- The dashboard's Paid/Pending field is manually set by an authorised admin. It does NOT confirm M-PESA payments automatically.
- For live production use, configure database backups and privacy/access procedures for student data.
