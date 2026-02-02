# 🛠️ Helpdesk Ticket Management System

A **Flask-based Helpdesk Ticket Management System** that allows users to raise support tickets, admins to assign tickets to agents, and agents to manage ticket status and communication — built with **secure authentication, role-based access control, and audit tracking**.

---

## 🚀 Features

### 👤 User
- Register & Login (secure password hashing)
- Create support tickets
- View own tickets
- Chat-style ticket conversation
- Track ticket status

### 🧑‍💼 Admin
- Admin dashboard
- View all tickets
- Assign tickets to agents
- View ticket analytics:
  - Total tickets
  - Open / In Progress / Resolved
  - Tickets per agent

### 🧑‍🔧 Agent
- View assigned tickets
- Update ticket status (Open → In Progress → Resolved)
- Reply to ticket conversations

### 🔐 Security & Architecture
- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control (User / Agent / Admin)
- Status history tracking (audit log)
- Clean modular Flask structure

---

## 🧰 Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (via SQLAlchemy)
- **Frontend:** HTML, CSS, Jinja2 Templates
- **Authentication:** Flask Sessions
- **Version Control:** Git & GitHub

---

## 📂 Project Structure

