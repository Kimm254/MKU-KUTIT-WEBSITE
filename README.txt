MKU KUTIT COMPLETE ADMIN WEBSITE
================================

WHAT THIS UPDATE ADDS
- Admin login via Render environment variables.
- Activities & events: create, publish/draft, add date/time/venue, optional poster, delete.
- Announcements: create, publish/draft, delete.
- Membership: view/search registrations, update Paid/Pending manually, export CSV.
- Posters & gallery: upload and delete images.
- Executive committee: add and delete leaders with position/contact details and display order.
- Public homepage automatically displays published activities and announcements, gallery images and executive profiles.
- PostgreSQL database stores records AND image bytes. Image uploads are limited to 5 MB and JPG/PNG/WEBP/GIF.

IMPORTANT BEFORE DEPLOYING
1. Back up existing registrations from your current website before replacing code. The new version keeps the existing Member table and its columns, so current member records in the SAME PostgreSQL database should remain.
2. If your old website used SQLite or a different database, registrations will not magically move. Export them first.
3. Keep the same Render PostgreSQL DATABASE_URL so this version connects to the database you created.
4. Do not delete your Render web service or PostgreSQL database.

REPLACE GITHUB FILES
1. Extract this ZIP on your computer.
2. Open your existing GitHub repository.
3. Replace app.py, requirements.txt, render.yaml, templates/index.html and static/style.css/static/script.js.
4. Upload the entire templates/admin folder (base.html, dashboard.html, members.html, activities.html, announcements.html, gallery.html, executives.html, login.html).
5. Commit changes. Render should deploy automatically.

RENDER ENVIRONMENT
Keep/add these on your existing web service:
DATABASE_URL = Internal Database URL from your Render PostgreSQL database
ADMIN_USERNAME = your chosen admin username
ADMIN_PASSWORD = a strong unique password
SECRET_KEY = a long random secret string

Do not paste database URLs, passwords or secret keys into GitHub or public chats.

ADMIN
https://YOUR-SERVICE.onrender.com/admin

LOCAL TEST (Windows)
Open CMD in extracted folder:
  py -m pip install -r requirements.txt
  set ADMIN_USERNAME=kutitadmin
  set ADMIN_PASSWORD=Choose-A-Strong-Password
  set SECRET_KEY=Use-A-Long-Random-Secret
  py app.py
Open http://127.0.0.1:5000/admin

PAYMENT NOTE
Paid/Pending is a manual admin record only. It does not automatically verify M-PESA payments.

PRIVACY
Only authorised KUTIT administrators should access the dashboard. Collect and publish only information the association is authorised to use. Executive contact details are displayed publicly when entered.
