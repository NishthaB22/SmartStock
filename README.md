# SmartStock — Inventory Management Demo

A beginner-friendly inventory management prototype built with Python, Streamlit and SQLite.

## Features
- Demo sign-in with Admin and Manager roles
- Dashboard metrics and low-stock alerts
- Product catalogue with Admin-only add/edit/delete
- Stock-in and stock-out recording with quantity validation
- Transaction history and CSV reports
- Local SQLite database created automatically

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Demo credentials
- Admin: `admin` / `Admin@123`
- Manager: `manager` / `Manager@123`

The credentials are intentionally visible for a classroom demonstration. This is not production authentication. Do not use real or reused passwords. For a public deployment, replace the demo credential setup with proper secret management and a production authentication system.

## Notes
- The database file `smartstock.db` is created in this folder on first run.
- Sample products are inserted automatically on first run.
- The current database is local to the machine running the app.
- This MVP does not include email alerts, multi-user cloud sync, or a trained forecasting model.
