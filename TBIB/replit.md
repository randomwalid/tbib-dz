# TBIB Medical Booking Platform

## Overview
TBIB is a bilingual (French/Arabic) medical appointment booking platform built with Flask. It features a public search-first homepage, role-based access for patients and doctors, a queue-based appointment system, FullCalendar-powered doctor cockpit, and RTL support for Arabic.

## Current State
- Search-first public homepage (no login required to browse)
- Clean minimalist UI with Mint (#14b999) brand color
- FullCalendar "Cockpit" dashboard for doctors
- Smart slot generation with variable durations
- Real-time queue status updates
- Bilingual support (FR/AR) with RTL toggle

## Test Credentials
- **Doctor**: doc@tbib.dz / doc
- **Patient**: pat@tbib.dz / pat

## Project Architecture

### Backend
- **Framework**: Flask 3.x with SQLAlchemy ORM
- **Database**: PostgreSQL (via DATABASE_URL)
- **Authentication**: Flask-Login with booking gate for guests
- **Structure**:
  - `app.py` - Application factory and configuration
  - `extensions.py` - Flask extensions (db, migrate, login_manager)
  - `models.py` - Database models (User, DoctorProfile, Appointment, ConsultationType, DoctorAbsence)
  - `routes.py` - All routes and translations

### Frontend
- **Styling**: TailwindCSS via CDN
- **Calendar**: FullCalendar v6 (week/day views, 15-min slots)
- **Fonts**: Inter (French), Cairo (Arabic)
- **Templates**: Jinja2 with base layout (white navbar, no footer)

### Data Models
1. **User**: id, email, password_hash, role, name, phone, birth_date, gender, address, city, no_show_count, is_blocked
2. **DoctorProfile**: id, user_id, specialty, city, address, bio, profile_picture, languages, payment_methods, expertises, diplomas, waiting_room_count
3. **DoctorAvailability**: id, doctor_id, day_of_week, start_time, end_time, is_available
4. **ConsultationType**: id, doctor_id, name, duration, price, color, is_emergency_only, require_existing_patient
5. **DoctorAbsence**: id, doctor_id, start_date, end_date, reason
6. **Appointment**: id, patient_id, doctor_id, status, queue_number, appointment_date, appointment_time, booking_type, consultation_reason, consultation_type_id, doctor_notes
7. **HealthRecord**: id, patient_id, blood_type, weight, height, allergies, chronic_conditions, vaccines
8. **Relative**: id, patient_id, name, relation, birth_date, blood_type, allergies

## Key Features
1. **Public Search**: Anyone can browse doctors without logging in
2. **Booking Gate**: Guests redirected to login when trying to book
3. **Smart Calendar Booking**: Dynamic slot generation based on consultation type duration
4. **Consultation Types**: Configurable types with duration, price, and color
5. **Doctor Cockpit**: FullCalendar with week/day views, right panel for appointment details
6. **AJAX Status Workflow**: Update appointment status without page reload
7. **No-Show Tracking**: Patients blocked after 3 no-shows
8. **Doctor Absences**: Configure vacation periods that block slots
9. **Real-Time Updates**: Queue status polling every 5-10 seconds
10. **Bilingual**: FR/AR toggle with RTL support

## Brand Colors
- Mint Turquoise: #14b999 (primary)
- White backgrounds with subtle shadows

## API Endpoints
- `/api/queue_status/<doctor_id>` - Returns current_serving, waiting_count, current_patient
- `/api/doctors/<doctor_id>/slots` - Returns available 30-min time slots (legacy)
- `/api/doctors/<doctor_id>/smart-slots` - Smart slots with duration awareness
- `/api/doctors/<doctor_id>/consultation-types` - List of consultation types
- `/api/doctor/appointments` - FullCalendar JSON events (doctor only)
- `/api/doctor/appointments/<id>/status` (POST) - Update appointment status
- `/api/doctor/appointments/<id>/notes` (POST) - Save doctor notes
- `/api/doctor/patient/<id>/history` - Patient history with security check
- `/api/check_in/<appointment_id>` (POST) - Assign queue number

## Routes
- `/` - Public homepage with doctor search
- `/doctor/<id>` - Doctor profile with booking wizard
- `/book/<id>` (POST) - Book appointment (scheduled or walk-in)
- `/my-appointments` - Patient's appointment list with real-time ticket view
- `/patient/profile` - Patient profile and health records
- `/doctor/dashboard` - FullCalendar Cockpit with sidebar navigation
- `/doctor/patients` - Patient management with searchable list and history modal
- `/doctor/settings` - Manage consultation types and absences

## Doctor Cockpit Layout
- **Left Sidebar**: Dark green gradient, collapsible, navigation to Agenda/Patients/Settings
- **Center**: FullCalendar with week/day views, 15-min slots, color-coded events
- **Right Panel**: Patient info, status buttons (Arrivé/En cours/Terminé/Absent), notes

## Status Workflow (AJAX)
1. Doctor clicks appointment in calendar
2. Right panel shows patient details and status buttons
3. "Arrivé" → status=waiting, assigns queue number, event turns amber
4. "Terminé" → status=completed, event turns blue
5. "Absent" → status=no_show, increments no_show_count, event turns gray with strikethrough

## Doctor Settings Hub (/doctor/settings)
Tabbed interface with 3 sections:
- **Tab 1 - Informations publiques**: Profile photo URL, name, specialty, city, address, bio, diplomas, languages, payment methods, expertises
- **Tab 2 - Types de consultation**: CRUD for consultation types with duration/price/color
- **Tab 3 - Horaires & Absences**: Weekly availability grid (Mon-Sun with start/end times) + absence management

## Patient Profile
Enhanced with additional fields: birth_date, gender, address, city (persisted on save)

## Patient Management (/doctor/patients)
- Searchable list of all patients the doctor has seen
- Table with patient name, contact info, last visit date, visit count
- "Voir Dossier" button opens modal with full patient history
- Modal shows patient demographics, health info, and appointment history
- Security: Only returns data for patients with existing doctor relationship

## Ministry Dashboard (/admin/ministry)
Public health observatory with RGPD-compliant aggregated statistics:
- **Equity Panel**: Doctor distribution by city, specialty counts
- **Epidemiological Watch**: Top diagnoses, consultation trends
- **Compliance Badge**: RGPD/CNI certification displayed

## Proxy Booking
Patients can book appointments for relatives using "Book for Someone Else" checkbox in booking flow.

## Recent Changes
- December 22, 2024: Family & Relatives Management - "Mes Proches" section with add modal
- December 22, 2024: Bug fixes - Diagnosis prompt only on "Terminé", proxy booking uses plain JS
- December 22, 2024: Ministry Dashboard - Aggregated health statistics with RGPD compliance
- December 22, 2024: Doctor Diagnosis capture on appointment completion
- December 22, 2024: Proxy booking - "Book for Someone Else" feature
- December 22, 2024: Patient Management module - searchable patient list with history modal
- December 22, 2024: Doctor Settings Hub V2 - Tabbed interface for profile, consultations, and availability
- December 22, 2024: Extended User model with birth_date, gender, address, city fields
- December 22, 2024: Extended DoctorProfile with profile_picture, languages, payment_methods, expertises, diplomas
- December 22, 2024: Weekly availability management with checkboxes and time inputs
- December 21, 2024: Doctolib Pro transformation - FullCalendar Cockpit, Smart Slot V2, Consultation Types
- December 21, 2024: Added doctor settings page for consultation types and absences
- December 21, 2024: AJAX status workflow with no-show tracking and blocking
- December 21, 2024: Check-in feature connecting scheduled appointments to live queue
