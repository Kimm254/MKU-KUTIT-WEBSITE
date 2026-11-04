MKU KUTIT WEBSITE — LOCAL SETUP
================================

WHAT IS INCLUDED
- Flask-powered responsive website
- About, activities, events and contact sections
- Student registration form
- Registrations saved locally to data/registrations.csv
- Mobile-friendly navigation

RUN ON WINDOWS (Python already installed)
1. Extract this ZIP into a folder, for example Desktop\MKU_KUTIT_Website.
2. Open that folder in File Explorer.
3. Click the address bar, type cmd, and press Enter.
4. Run these commands:

   py -m pip install -r requirements.txt
   py app.py

   If "py" does not work, try:
   python -m pip install -r requirements.txt
   python app.py

5. Open this address in your browser:
   http://127.0.0.1:5000

6. Keep the Command Prompt window open while using the website.
   Press CTRL+C in that window to stop the server.

REGISTRATION DATA
Submitted registrations are stored in:
data/registrations.csv

PAYMENTS
This version collects registration details only. It does NOT initiate M-PESA STK Push
or automatically confirm payments. To enable real M-PESA payments, the association
will need an approved Daraja account, registered callback URL, business credentials,
and a secure server configuration. Do not put payment passwords or API keys in HTML.

DEPLOYMENT
For Render or another Python host:
- Build command: pip install -r requirements.txt
- Start command: gunicorn app:app
- Add gunicorn to requirements.txt before deploying:
  Flask>=3.0,<4.0
  gunicorn>=22.0,<24.0

CUSTOMISING
- Edit page content in templates/index.html
- Edit colours/layout in static/style.css
- Edit behaviour in static/script.js
- Replace the placeholder event details with confirmed association information.
