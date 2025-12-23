from datetime import datetime, date, timedelta, time
from extensions import db
from models import Appointment, DoctorAvailability, DoctorAbsence, ConsultationType

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

def is_slot_free(doctor_id, start_dt, duration_minutes, exclude_appointment_id=None):
    """
    Checks if a slot is free for a doctor.
    Considers:
    1. Working hours (DoctorAvailability)
    2. Absences (DoctorAbsence)
    3. Existing Appointments
    """
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    day_of_week = start_dt.weekday()
    current_date = start_dt.date()

    # 1. Check Working Hours
    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day_of_week,
        is_available=True
    ).first()

    if not availability:
        # If no availability defined for this day, assume strictly 9-17 or unavailable?
        # Based on app logic, fallback seems to be 9-17.
        start_work = time(9, 0)
        end_work = time(17, 0)
    else:
        start_work = availability.start_time
        end_work = availability.end_time

    # Check if slot fits in working hours
    # Create comparable datetimes for the day
    work_start_dt = datetime.combine(current_date, start_work)
    work_end_dt = datetime.combine(current_date, end_work)

    if start_dt < work_start_dt or end_dt > work_end_dt:
        return False

    # 2. Check Absences
    # If the slot overlaps with any absence
    absence = DoctorAbsence.query.filter(
        DoctorAbsence.doctor_id == doctor_id,
        DoctorAbsence.start_date < end_dt,
        DoctorAbsence.end_date > start_dt
    ).first()

    if absence:
        return False

    # 3. Check Existing Appointments
    # We check for overlaps.
    # Overlap logic: (StartA < EndB) and (EndA > StartB)
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == current_date,
        Appointment.status.in_(['confirmed', 'waiting'])
    )

    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)

    # Fetch relevant appointments for the day
    existing_appointments = query.all()

    for appt in existing_appointments:
        if not appt.appointment_time:
            continue

        appt_start = datetime.combine(appt.appointment_date, appt.appointment_time)
        # Determine duration
        appt_duration = 30
        if appt.consultation_type:
            appt_duration = appt.consultation_type.duration

        appt_end = appt_start + timedelta(minutes=appt_duration)

        if start_dt < appt_end and end_dt > appt_start:
            return False

    return True

def find_next_free_slot(doctor_id, start_dt, duration_minutes, max_days=30, exclude_appointment_id=None):
    """
    Finds the next available slot starting from start_dt.
    """
    current_search_dt = start_dt

    # Safety limit: check up to X days ahead
    max_search_date = start_dt.date() + timedelta(days=max_days)

    # Loop limit to prevent infinite loops (e.g., if everything is booked or bug)
    max_iterations = 5000
    iterations = 0

    while current_search_dt.date() <= max_search_date:
        if iterations > max_iterations:
            raise Exception("Could not find a free slot within reasonable limits.")
        iterations += 1

        if is_slot_free(doctor_id, current_search_dt, duration_minutes, exclude_appointment_id):
            return current_search_dt

        # Increment search time
        # We can increment by small steps (e.g. 15 mins)
        current_search_dt += timedelta(minutes=15)

        # Optimization: If we passed end of working day, jump to next day start
        # Retrieve working hours for current day to see if we passed them
        day_of_week = current_search_dt.weekday()
        availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_available=True
        ).first()

        if availability:
            end_work = availability.end_time
        else:
            end_work = time(17, 0) # Default fallback

        work_end_dt = datetime.combine(current_search_dt.date(), end_work)

        if current_search_dt >= work_end_dt:
            # Jump to next day 08:00 (since we don't know start time easily without querying again, 08:00 is safe bet to start checking)
            next_day = current_search_dt.date() + timedelta(days=1)
            current_search_dt = datetime.combine(next_day, time(8, 0))

    return None

def shift_appointments(doctor_id, urgency_duration):
    """
    Shifts all future appointments of the day for a doctor by a given duration (in minutes).
    Uses a smart algorithm to find the next available slot if the shift causes overlap or pushes outside working hours.

    If shifting forward (delay), processes appointments in reverse chronological order to avoid cascading collisions.
    If shifting backward (earlier), processes in chronological order.
    """
    current_time = datetime.now().time()
    today = date.today()

    # Get future appointments for today, sorted by time
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == today,
        Appointment.appointment_time > current_time
    ).order_by(Appointment.appointment_time).all()

    # If delay (positive duration), reverse the list to shift latest appointments first.
    # This clears the way for earlier appointments to move into slots that might have been occupied.
    if urgency_duration > 0:
        appointments.reverse()

    for appointment in appointments:
        if appointment.appointment_time:
            # Determine duration of this appointment
            duration = 30
            if appointment.consultation_type:
                duration = appointment.consultation_type.duration

            appointment_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)

            # Calculate tentative new start time
            tentative_start = appointment_dt + timedelta(minutes=urgency_duration)

            # Find actual free slot starting from tentative_start
            # We exclude current appointment ID from collision check (it's moving)
            real_start_dt = find_next_free_slot(
                doctor_id,
                tentative_start,
                duration,
                exclude_appointment_id=appointment.id
            )

            if real_start_dt:
                appointment.appointment_date = real_start_dt.date()
                appointment.appointment_time = real_start_dt.time()

                # Flush to ensure subsequent checks see this slot as taken/freed
                db.session.add(appointment)
                db.session.flush()
            else:
                raise Exception(f"Cannot reschedule appointment {appointment.id}: No slots available.")

    db.session.commit()
