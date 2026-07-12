# AssetFlow
# Hackathon
Enterprise Asset & Resource Management System

AssetFlow is a centralized ERP platform designed to help organizations manage departments, employees, physical assets, shared resources, bookings, maintenance workflows, audits, notifications, and reports.

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI
- Database: PostgreSQL / SQLite (dev)
- ORM: SQLAlchemy
- Authentication: JWT

## Core Modules

- Authentication and Role-Based Access Control
- Organization Setup (Departments, Categories, Employees)
- Asset Registration and Directory
- Asset Allocation and Transfer
- Resource Booking
- Maintenance Management
- Asset Audit
- Dashboard
- Reports and Analytics
- Activity Logs and Notifications

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
python seed.py          # initialise DB and seed demo data
uvicorn app.main:app --reload
```

API docs available at: http://127.0.0.1:8000/docs

## Demo Accounts

| Role           | Email                    | Password     |
|----------------|--------------------------|--------------|
| Admin          | admin@assetflow.com      | admin123     |
| Asset Manager  | manager@assetflow.com    | manager123   |
| Department Head| head@assetflow.com       | head123      |
| Employee       | employee@assetflow.com   | employee123  |
