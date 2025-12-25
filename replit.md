# TBIB Medical Booking Platform

## Overview

TBIB is a bilingual (French/Arabic) medical appointment booking platform designed for the Algerian healthcare market. It provides a "Search-First" public interface where patients can find and book appointments with doctors, and a comprehensive dashboard for doctors to manage their schedules, patients, and consultations.

The platform features two booking modes:
- **TICKET_QUEUE**: Traditional queue-based waiting system with real-time ticket numbers
- **SMART_RDV**: Calendar-based dynamic appointment scheduling with variable consultation durations

Key capabilities include patient reliability scoring, smart slot generation, doctor availability management, and an anonymized ministry dashboard for public health monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask 3.x** with application factory pattern (`create_app()`)
- **SQLAlchemy ORM** for database operations with Flask-Migrate for schema migrations
- **Flask-Login** for session-based authentication
- Password hashing uses `pbkdf2:sha256` via Werkzeug

### Database Models
Core entities follow a strict separation pattern:
- **User**: Unified model for patients and doctors (role-based: 'patient' or 'doctor')
- **DoctorProfile**: Extended profile linked to User via foreign key
- **Appointment**: Booking records with status tracking, queue numbers, and scheduling data
- **ConsultationType**: Variable duration consultation types per doctor (drives calendar slot generation)
- **DoctorAvailability**: Weekly schedule configuration (day_of_week, start_time, end_time)
- **DoctorAbsence**: Vacation/absence periods
- **HealthRecord**: Patient health information
- **Relative**: Family members linked to patients

### Privacy by Design
- Epidemiological data table has NO foreign keys to User table (anonymity requirement)
- Ministry dashboard shows only aggregated statistics, never individual patient data
- KYC verification status gates doctor access to patient records

### Frontend Architecture
- **Jinja2 templates** with base layout inheritance
- **TailwindCSS via CDN** for styling (no build step required)
- **Alpine.js** for reactive UI components
- **FullCalendar v6** for doctor scheduling cockpit
- Fonts: Inter (French), Cairo (Arabic with RTL support)

### File Organization
```
TBIB/
├── app.py          # Application factory, configuration, logging
├── extensions.py   # Flask extensions initialization (db, migrate, login_manager)
├── models.py       # Database model definitions only
├── routes.py       # All route handlers and translation dictionaries
├── utils/          # Business logic modules
│   ├── engine.py       # Wait time calculation, slot availability checking
│   └── smart_engine.py # Queue optimization, reliability scoring algorithm
├── templates/      # Jinja2 HTML templates
├── static/         # CSS, images, client-side assets
└── migrations/     # Alembic migration scripts
```

### Smart Scheduling Engine
The `utils/smart_engine.py` implements:
- Patient reliability scoring (0-100 scale with penalties for no-shows, bonuses for punctuality)
- Shadow slot detection for overbooking protection on low-reliability patients
- Queue optimization with urgency weighting and delay penalties

### API Patterns
- Slot generation: `/api/doctors/<doctor_id>/slots` returns available time slots as JSON
- Queue status: `/api/queue_status/<doctor_id>` for real-time waiting room updates
- Doctor appointments: `/api/doctor/appointments` returns FullCalendar-compatible event data

## External Dependencies

### Database
- **PostgreSQL** (production via DATABASE_URL environment variable)
- **SQLite** (development fallback: `tbib.db`)

### Python Packages
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate
- Werkzeug (password hashing)
- Alembic (migrations, via Flask-Migrate)

### Frontend CDN Resources
- TailwindCSS (styling framework)
- Alpine.js (reactive UI)
- FullCalendar v6 (calendar component)
- Google Fonts: Inter, Cairo

### Environment Variables
- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: PostgreSQL connection string

### Brand Colors (Strict)
- Primary: `#3cc7a7` / `#14b999` (Mint Green)
- Background: `#FFFFFF` / `#F8F9FA`
- Text: `#333333`
- No violet, beige, or Bootstrap defaults