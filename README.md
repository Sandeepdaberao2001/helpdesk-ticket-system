# Helpdesk System

This project now runs as a single-link browser app:

- Flask serves the API under `/api/*`
- Flask also serves the browser UI from `/`
- MongoDB stores users, tickets, and comments
- JWT auth is used for browser sessions

## What Was Fixed

- Removed the hardcoded default admin account
- Added a real browser entrypoint at `/`
- Made backend imports package-safe for deployment
- Made `.env` loading explicit to `backend/.env`
- Made CORS configurable instead of localhost-only
- Replaced the broken SQLAlchemy leftovers with migration-safe compatibility files

## Local Setup

1. Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Create your environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

3. Edit `backend/.env` and set a strong `JWT_SECRET_KEY`.
4. Make sure MongoDB is running and matches `MONGO_URI`.
5. Create your first admin account:

```powershell
.\.venv\Scripts\python.exe -m backend.bootstrap_admin --email admin@example.com --username admin --password "ChangeThisNow123!"
```

6. Start the app:

```powershell
.\.venv\Scripts\python.exe run.py
```

7. Open it in your browser:

```text
http://localhost:5000
```

## Run Tests

Use the standard library test suite to validate the critical config and workflow guards:

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## MongoDB Atlas Setup

If you want to use MongoDB Atlas instead of local MongoDB:

1. Create a free cluster in MongoDB Atlas.
2. Create a database user with a username and password.
3. In Network Access, allow your current IP address.
4. Copy your Atlas connection string.
5. Update `backend/.env` like this:

```env
MONGO_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority&appName=HelpdeskApp
MONGO_DB_NAME=helpdesk_db
```

6. If your password contains special characters like `@`, `:`, `/`, or `#`, URL-encode it first.
7. Then run the admin bootstrap and start the app the same way as above.

## Deployment Notes

- Use `backend.app:app` as the WSGI entrypoint on hosting platforms.
- If the UI is served by Flask from the same domain, normal browser use does not need extra CORS changes.
- If you deploy a separate frontend domain, add that domain to `CORS_ORIGINS`.
- Do not deploy with an empty or weak `JWT_SECRET_KEY`.

## Browser Features

- User registration and login
- Ticket creation
- Ticket list with filters and pagination
- Ticket details with comments
- Agent and admin ticket updates
- Ticket assignment
- Internal notes for agents and admins
- Admin stats
- Admin user role management
- Admin user activation and deactivation
