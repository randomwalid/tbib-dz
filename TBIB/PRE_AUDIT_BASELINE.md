# Pre-Audit Baseline

- **Date**: $(date)
- **Frameworks**: Flask, SQLAlchemy
- **Routes**:
  - Main Routes (routes.py)
  - Prescription Routes (prescription_routes.py)
- **Models**:
  - User
  - DoctorProfile
  - Appointment
  - Prescription
  - ... (and others)
- **Existing Tests**: 0 (New test suite created in `TBIB/tests/`)
- **Alembic**: Initialized.
- **Python Version**: 3.11+

## Prescription Model Baseline
- **Columns**:
  - id, token, appointment_id, doctor_id, patient_id
  - medications, notes, security_hash, prescription_type
  - usage_count, max_usage, expiry_date, created_at, last_verified_at

**Note**: `expiry_date` exists. `expired_at` will NOT be created. `status` will be added.
