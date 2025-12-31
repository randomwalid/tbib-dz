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

class PaymentMethod(enum.Enum):
    ESPECES = 'Espèces'
    CHIFA = 'Chifa'
    CIB = 'CIB'
    GRATUITE = 'Gratuité'

class ReferralStatus(enum.Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    COMPLETED = 'completed'
    DECLINED = 'declined'

class User(UserMixin, db.Model):
    """
    Roles: 'patient', 'doctor', 'secretary'
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # patient, doctor, secretary
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    no_show_count = db.Column(db.Integer, default=0)
    is_blocked = db.Column(db.Boolean, default=False)

    # SmartFlow: Score de fiabilité du patient (0-100)
    reliability_score = db.Column(db.Float, default=100.0, nullable=False)
    
    # === Secrétaire/Assistante ===
    # Lien vers le médecin (pour rôle secretary)
    linked_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=True)
    # Délégation: permet à la secrétaire de voir les dossiers médicaux
    can_view_medical_records = db.Column(db.Boolean, default=False)

    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, 
                                      foreign_keys='DoctorProfile.user_id', cascade='all, delete-orphan')
    linked_doctor = db.relationship('DoctorProfile', foreign_keys=[linked_doctor_id], backref='secretaries')

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
    """Carnet de Santé Numérique - Digital Medical Record (DMR)"""
    __tablename__ = 'health_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # === Données Vitales (Patient peut modifier) ===
    weight = db.Column(db.Float)                          # Poids en kg
    height = db.Column(db.Float)                          # Taille en cm
    emergency_contact = db.Column(db.String(200))         # Nom + Téléphone urgence
    
    # === Données Médicales (Médecin uniquement) ===
    blood_type = db.Column(db.String(10))                 # A+, O-, AB+, etc.
    allergies = db.Column(db.Text)                        # Médicaments, aliments, latex...
    chronic_conditions = db.Column(db.Text)               # Diabète, HTA, Asthme...
    family_history = db.Column(db.Text)                   # Antécédents familiaux (Père/Mère)
    vaccines = db.Column(db.Text)                         # Suivi vaccinal (dates + types)
    current_treatments = db.Column(db.Text)               # Traitements en cours
    prescriptions = db.Column(db.Text)                    # Ordonnances / Documents
    notes = db.Column(db.Text)                            # Notes privées médecin
    
    # === Métadonnées ===
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(50))                 # 'patient' ou 'doctor:<id>'

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

    # === SmartFlow Fields ===
    # Shadow Slot: Surbooking sécurisé pour patients peu fiables (score < 50)
    is_shadow_slot = db.Column(db.Boolean, default=False)
    # Niveau d'urgence: 1 (Normal) à 5 (Vitale)
    urgency_level = db.Column(db.Integer, default=1)
    # Heure d'arrivée réelle du patient
    arrival_time = db.Column(db.DateTime, nullable=True)
    # Heure de check-in confirmé
    check_in_time = db.Column(db.DateTime, nullable=True)
    
    # === Caisse & Honoraires ===
    price_paid = db.Column(db.Float, nullable=True)        # Montant perçu
    payment_method = db.Column(db.String(20), nullable=True)  # Espèces, Chifa, CIB, Gratuité

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


class Referral(db.Model):
    """Réseau d'Adressage - Orienter un patient vers un confrère."""
    __tablename__ = 'referrals'

    id = db.Column(db.Integer, primary_key=True)
    from_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    to_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text)                           # Motif de l'orientation
    notes = db.Column(db.Text)                            # Notes pour le confrère
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    from_doctor = db.relationship('DoctorProfile', foreign_keys=[from_doctor_id], backref='referrals_sent')
    to_doctor = db.relationship('DoctorProfile', foreign_keys=[to_doctor_id], backref='referrals_received')
    patient = db.relationship('User', backref='referrals')


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Relations
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Contenu médical (chiffré plus tard)
    medications = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Sécurité
    status = db.Column(db.String(20), default='pending', nullable=False, server_default='pending')
    security_hash = db.Column(db.String(64), nullable=True)
    prescription_type = db.Column(db.String(20), default='ACUTE')  # ACUTE ou CHRONIC
    usage_count = db.Column(db.Integer, default=0)
    max_usage = db.Column(db.Integer, default=1)
    expiry_date = db.Column(db.DateTime, nullable=False)

    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_verified_at = db.Column(db.DateTime, nullable=True)

    # Relations ORM
    appointment = db.relationship('Appointment', backref='prescription', lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='issued_prescriptions')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='received_prescriptions')

    def __repr__(self):
        return f'<Prescription {self.token}>'
