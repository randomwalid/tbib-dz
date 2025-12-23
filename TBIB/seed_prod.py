from app import app
from extensions import db
from models import User, DoctorProfile, DoctorAvailability, ConsultationType
from datetime import time
import random
from werkzeug.security import generate_password_hash

CITIES = ["Alger", "Oran", "Constantine", "Annaba", "Setif", "Bejaia", "Tlemcen", "Blida"]
SPECIALTIES = ["Médecin Généraliste", "Dentiste", "Cardiologue", "Pédiatre", "Dermatologue", "Gynécologue", "Ophtalmologue"]
NAMES_M = ["Mohamed", "Amine", "Walid", "Karim", "Yacine", "Omar", "Youcef", "Bilal"]
NAMES_F = ["Sarah", "Fatima", "Meriem", "Yasmine", "Amel", "Leila", "Noura", "Imene"]
LAST_NAMES = ["Benali", "Saidi", "Dahmani", "Moussaoui", "Belkacem", "Larbi", "Chraiet", "Mekki"]
STREET_NAMES = ['Didouche Mourad', 'Ben Mhidi', 'Abane Ramdane', 'Amirouche', 'Pasteur']

def seed_database():
    with app.app_context():
        print("🚀 STARTING DATABASE SEEDING (PRODUCTION)...")
        
        db.create_all()
        print("✅ Tables verified.")

        if User.query.filter_by(role='doctor').first():
            print("⚠️ Database already contains doctors. Aborting to prevent duplicates.")
            return

        for i in range(1, 51):
            gender = random.choice(['M', 'F'])
            fname = random.choice(NAMES_M) if gender == 'M' else random.choice(NAMES_F)
            lname = random.choice(LAST_NAMES)
            full_name = f"Dr. {fname} {lname}"
            
            email = f"doc{i}@tbib.dz"
            city = random.choice(CITIES)
            spec = random.choice(SPECIALTIES)
            
            user = User(
                email=email,
                password_hash=generate_password_hash("123456"),
                role='doctor',
                name=full_name,
                phone=f"05{random.randint(10000000, 99999999)}",
                city=city
            )
            db.session.add(user)
            db.session.flush()

            profile = DoctorProfile(
                user_id=user.id,
                specialty=spec,
                city=city,
                address=f"{random.randint(1, 200)} Rue {random.choice(STREET_NAMES)}",
                bio=f"Spécialiste en {spec.lower()} à {city}. Expérience confirmée de plus de 10 ans.",
                waiting_room_count=0,
                languages="Français, Arabe",
                payment_methods="Espèces, Carte bancaire"
            )
            db.session.add(profile)
            db.session.flush()

            t1 = ConsultationType(
                doctor_id=profile.id,
                name="Consultation",
                duration=30,
                price="2000 DA",
                color="#14b999",
                is_active=True
            )
            t2 = ConsultationType(
                doctor_id=profile.id,
                name="Urgence",
                duration=15,
                price="3000 DA",
                color="#ef4444",
                is_emergency_only=True,
                is_active=True
            )
            db.session.add_all([t1, t2])

            start_t = time(9, 0)
            end_t = time(17, 0)
            for day in range(5):
                avail = DoctorAvailability(
                    doctor_id=profile.id,
                    day_of_week=day,
                    start_time=start_t,
                    end_time=end_t,
                    is_available=True
                )
                db.session.add(avail)

            if i % 10 == 0:
                print(f"   ... Created {i} doctors")

        db.session.commit()
        print("✅ SUCCESS: 50 Doctors injected with schedules!")

if __name__ == "__main__":
    seed_database()
