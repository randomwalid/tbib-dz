import random
from datetime import date, time
from extensions import db
from models import User, DoctorProfile, DoctorAvailability, Appointment

CITIES = ["Alger", "Oran", "Constantine", "Annaba", "Setif", "Bejaia", "Tlemcen", "Blida", "Tizi Ouzou", "Batna"]

SPECIALTIES = ["Médecin Généraliste", "Dentiste", "Cardiologue", "Pédiatre", "Dermatologue", "Gynécologue", "Ophtalmologue", "Psychologue"]

FIRST_NAMES = ["Mohamed", "Amine", "Walid", "Yacine", "Karim", "Sarah", "Fatima", "Meriem", "Yasmine", "Amel"]

LAST_NAMES = ["Benali", "Saidi", "Dahmani", "Moussaoui", "Belkacem", "Brahimi", "Mansouri", "Zerrouki"]

BIOS = [
    "Expert diplômé avec 10 ans d'expérience dans le domaine médical.",
    "Spécialiste reconnu avec une approche centrée sur le patient.",
    "Praticien dévoué offrant des soins de qualité depuis plus de 8 ans.",
    "Médecin expérimenté formé dans les meilleures universités algériennes.",
    "Professionnel passionné par la médecine et le bien-être des patients.",
]

def seed_test_accounts():
    if User.query.filter_by(email='doc@tbib.dz').first():
        return
    
    doctor_user = User(
        email='doc@tbib.dz',
        name='Ahmed Benali',
        phone='+213 555 123 456',
        role='doctor'
    )
    doctor_user.set_password('doc')
    db.session.add(doctor_user)
    db.session.flush()
    
    doctor_profile = DoctorProfile(
        user_id=doctor_user.id,
        specialty='Dentiste',
        city='Alger',
        address='123 Rue Didouche Mourad',
        bio='Dentiste expérimenté avec plus de 10 ans de pratique.',
        waiting_room_count=0
    )
    db.session.add(doctor_profile)
    db.session.flush()
    
    for day in range(0, 4):
        availability = DoctorAvailability(
            doctor_id=doctor_profile.id,
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(16, 0),
            is_available=True
        )
        db.session.add(availability)
    
    patient_user = User(
        email='pat@tbib.dz',
        name='Fatima Zahra',
        phone='+213 555 987 654',
        role='patient'
    )
    patient_user.set_password('pat')
    db.session.add(patient_user)
    db.session.flush()
    
    appointment = Appointment(
        patient_id=patient_user.id,
        doctor_id=doctor_profile.id,
        status='confirmed',
        queue_number=1,
        appointment_date=date.today()
    )
    db.session.add(appointment)
    db.session.commit()

def seed_50_doctors(reset=False):
    if reset:
        DoctorAvailability.query.delete()
        Appointment.query.delete()
        DoctorProfile.query.delete()
        User.query.filter(User.role == 'doctor').delete()
        db.session.commit()
    
    created_count = 0
    
    for i in range(50):
        email = f"doc{i}@tbib.dz"
        
        if User.query.filter_by(email=email).first():
            continue
        
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        user = User(
            email=email,
            name=full_name,
            phone=f"+2135550000{i:02d}",
            role='doctor'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        profile = DoctorProfile(
            user_id=user.id,
            specialty=random.choice(SPECIALTIES),
            city=random.choice(CITIES),
            address=f"{random.randint(1, 100)} Rue de la Santé",
            bio=random.choice(BIOS),
            waiting_room_count=random.randint(0, 5)
        )
        db.session.add(profile)
        db.session.flush()
        
        for day in range(0, 4):
            availability = DoctorAvailability(
                doctor_id=profile.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(16, 0),
                is_available=True
            )
            db.session.add(availability)
        
        created_count += 1
    
    db.session.commit()
    return created_count
