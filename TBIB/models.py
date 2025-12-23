import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time

from extensions import db

class AppointmentMode(enum.Enum):
    TICKET_QUEUE = 'TICKET_QUEUE'
    SMART_RDV = 'SMART_RDV'

class KYCStatus(enum.Enum):
    PENDING = 'PENDING'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    no_show_count = db.Column(db.Integer, default=0)
    is_blocked = db.Column(db.Boolean, default=False)
    
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(500), nullable=True)
    languages = db.Column(db.String(255), nullable=True)
    payment_methods = db.Column(db.String(255), nullable=True)
    expertises = db.Column(db.String(500), nullable=True)
    diplomas = db.Column(db.Text, nullable=True)
    waiting_room_count = db.Column(db.Integer, default=0)
    
    appointment_mode = db.Column(db.Enum(AppointmentMode), default=AppointmentMode.TICKET_QUEUE)
    kyc_status = db.Column(db.Enum(KYCStatus), default=KYCStatus.PENDING)
    documents_encrypted_path = db.Column(db.String(500), nullable=True)

    appointments = db.relationship('Appointment', backref='doctor_profile', foreign_keys='Appointment.doctor_id', lazy='dynamic')

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    doctor_profile = db.relationship('DoctorProfile', backref='availability_slots')

class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    blood_type = db.Column(db.String(10))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    vaccines = db.Column(db.Text)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = db.relationship('User', backref=db.backref('health_record', uselist=False))

class Appointment(db.Model):
    __tablename__ = 'appointments'
    __table_args__ = (
        db.Index('ix_unique_scheduled_slot', 'doctor_id', 'appointment_date', 'appointment_time',
                 unique=True, postgresql_where=db.text("status = 'confirmed' AND appointment_time IS NOT NULL")),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    queue_number = db.Column(db.Integer, nullable=True)
    is_urgent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointment_date = db.Column(db.Date, default=date.today)
    appointment_time = db.Column(db.Time, nullable=True)
    booking_type = db.Column(db.String(20), default='scheduled')
    consultation_reason = db.Column(db.String(100))
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    consultation_type_id = db.Column(db.Integer, db.ForeignKey('consultation_types.id'), nullable=True)
    consultation_type = db.relationship('ConsultationType', backref='appointments')

    emergency_type_id = db.Column(db.Integer, db.ForeignKey('emergency_types.id'), nullable=True)
    emergency_type = db.relationship('EmergencyType', backref='appointments')

    relative_id = db.Column(db.Integer, db.ForeignKey('relatives.id'), nullable=True)
    relative = db.relationship('Relative', backref='appointments')

    doctor_notes = db.Column(db.Text)


class ConsultationType(db.Model):
    __tablename__ = 'consultation_types'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False, default=30)
    price = db.Column(db.String(20))
    color = db.Column(db.String(10), default='#14b999')
    is_emergency_only = db.Column(db.Boolean, default=False)
    require_existing_patient = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    doctor_profile = db.relationship('DoctorProfile', backref='consultation_types')


class DoctorAbsence(db.Model):
    __tablename__ = 'doctor_absences'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))
    
    doctor_profile = db.relationship('DoctorProfile', backref='absences')


class EmergencyType(db.Model):
    __tablename__ = 'emergency_types'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    priority_level = db.Column(db.Integer, default=1) # 1 (Low) to 5 (Critical)
    color = db.Column(db.String(10), default='#ff0000')

    doctor_profile = db.relationship('DoctorProfile', backref='emergency_types')


class UserRelationship(db.Model):
    __tablename__ = 'user_relationships'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False) # e.g., PARENT, SPOUSE, CHILD
    status = db.Column(db.String(20), default='PENDING') # PENDING, ACCEPTED, REJECTED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requester = db.relationship('User', foreign_keys=[requester_id], backref='relationships_requested')
    target = db.relationship('User', foreign_keys=[target_id], backref='relationships_received')


class Relative(db.Model):
    __tablename__ = 'relatives'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50))
    birth_date = db.Column(db.Date)
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    
    patient = db.relationship('User', backref=db.backref('relatives', lazy=True))


class EpidemiologyData(db.Model):
    __tablename__ = 'epidemiology_data'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    wilaya = db.Column(db.String(100), nullable=False)
    pathology_tag = db.Column(db.String(100), nullable=False)
    age_group = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
