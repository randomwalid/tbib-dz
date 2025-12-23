from datetime import datetime, date, timedelta
from extensions import db
from models import Appointment

def calculate_wait_time(doctor_id):
    """
    Calculates the waiting time for a doctor based on the number of waiting patients.
    Each waiting patient adds 20 minutes.
    """
    # Count appointments with status 'WAITING' for the doctor on the current day
    waiting_count = Appointment.query.filter_by(
        doctor_id=doctor_id,
        status='WAITING',
        appointment_date=date.today()
    ).count()

    wait_time = waiting_count * 20
    return f"{wait_time} min"

def shift_appointments(doctor_id, urgency_duration):
    """
    Shifts all future appointments of the day for a doctor by a given duration (in minutes).
    Handles date exceptions if the shift pushes an appointment to the next day.
    """
    current_time = datetime.now().time()
    today = date.today()

    # Get future appointments for today
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == today,
        Appointment.appointment_time > current_time
    ).all()

    for appointment in appointments:
        if appointment.appointment_time:
            # Combine date and time to perform arithmetic
            appointment_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)

            # Add urgency duration
            new_dt = appointment_dt + timedelta(minutes=urgency_duration)

            # Update date and time
            appointment.appointment_date = new_dt.date()
            appointment.appointment_time = new_dt.time()

    db.session.commit()

def get_conflicting_appointments(doctor_id, start_date, end_date):
    """
    Returns a count of appointments that conflict with a given absence range.
    Only considers confirmed or waiting appointments.
    """
    # Convert datetime to date for comparison if necessary, but Appointment has date column
    # The absence dates are datetime, but typically absences cover whole days or specific periods.
    # Assuming start_date and end_date are datetime objects.

    # We check for appointments where appointment_date is within the range [start_date, end_date]
    # Note: start_date/end_date usually come with time 00:00:00 or 23:59:59 from the frontend

    count = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(['confirmed', 'waiting']),
        Appointment.appointment_date >= start_date.date(),
        Appointment.appointment_date <= end_date.date()
    ).count()

    return count

def cancel_appointments_in_range(doctor_id, start_date, end_date, reason):
    """
    Cancels all appointments in the given range for the doctor.
    """
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(['confirmed', 'waiting']),
        Appointment.appointment_date >= start_date.date(),
        Appointment.appointment_date <= end_date.date()
    ).all()

    for appt in appointments:
        appt.status = 'cancelled'
        if reason:
            existing_notes = appt.doctor_notes or ''
            appt.doctor_notes = f"ANNULÉ (Absence médecin: {reason})\n{existing_notes}".strip()
        else:
            existing_notes = appt.doctor_notes or ''
            appt.doctor_notes = f"ANNULÉ (Absence médecin)\n{existing_notes}".strip()

    db.session.commit()
    return len(appointments)
