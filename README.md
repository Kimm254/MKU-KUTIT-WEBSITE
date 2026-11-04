# MKU KUTIT Website

A Flask website with public membership registration and a protected administration area.

## Features
- Public homepage and membership registration
- Friendly congratulations message after registration (no payment step)
- Admin dashboard overview
- Member directory, search, CSV export and manual payment-status tracking
- Activities and events management with optional poster upload
- Announcements management
- Gallery uploads
- Executive committee management
- SQLite for local testing and PostgreSQL support on Render

## Run locally (Windows)
1. Install Python 3.11 or newer.
2. Open Command Prompt in this folder.
3. Create an environment: `py -m venv .venv`
4. Activate it: `.venv\\Scripts\\activate`
5. Install packages: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and set a strong `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD`.
7. Set the environment variables in your terminal, or use a local environment-variable manager.
8. Start: `python app.py`
9. Visit `http://127.0.0.1:5000`

The app reads environment variables directly. For local Windows Command Prompt, set them before running:
`set SECRET_KEY=your-long-secret`
`set ADMIN_USERNAME=admin`
`set ADMIN_PASSWORD=your-strong-password`

## Deploy to Render
- Push the contents of this folder to a new GitHub repository.
- Create a Render Web Service connected to that repository.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add environment variables: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `DATABASE_URL`.
- For persistent member data, create a Render PostgreSQL database and use its **internal** connection URL as `DATABASE_URL`.

Do not delete an existing production database if it contains registrations. This fresh project creates missing tables; it does not intentionally drop tables.

## Admin
Open `/admin/login` and use the username and password configured in the environment variables. Do not use the example credentials in production.
