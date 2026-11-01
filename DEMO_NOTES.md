# Demo walkthrough (about 3 minutes)

1. Sign in as Admin (`admin` / `Admin@123`).
2. Show dashboard metrics and low-stock alerts.
3. Open Products and add a sample item; point out that catalogue changes are Admin-only.
4. Record Stock In, then Stock Out. Try taking out more than available to show validation.
5. Show the transaction history and download the CSV report.
6. Log out and sign in as Manager (`manager` / `Manager@123`). Show that the product catalogue is view-only while stock movements remain available.

## Explain honestly
This is a functional MVP using Streamlit and SQLite to demonstrate the main inventory workflow. The original plan's React/Node/MySQL architecture, email notifications, and production-grade authentication are not implemented in this prototype. The login and role controls are intended for a local classroom demo only.
