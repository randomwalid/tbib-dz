import pytest
import sys
import os
from datetime import time

# Add TBIB to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db as _db
from models import User, DoctorProfile, DoctorAvailability, ConsultationType

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    return app

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def seed(db_session):
    # Doctor 1
    doc1 = User(email='doctor1@tbib.dz', role='doctor', name='Dr. Chaos', phone='0555555555')
    doc1.set_password('password')
    db_session.add(doc1)
    db_session.flush()

    prof1 = DoctorProfile(user_id=doc1.id, specialty='General', city='Algiers', waiting_room_count=0)
    db_session.add(prof1)
    db_session.flush()

    # Availability for Doc 1
    for d in range(7):
        db_session.add(DoctorAvailability(doctor_id=prof1.id, day_of_week=d, start_time=time(8,0), end_time=time(18,0)))

    ctype1 = ConsultationType(doctor_id=prof1.id, name='Consultation', duration=30, price='2000', is_active=True)
    db_session.add(ctype1)

    # Doctor 2
    doc2 = User(email='doctor2@tbib.dz', role='doctor', name='Dr. Order', phone='0555555556')
    doc2.set_password('password')
    db_session.add(doc2)
    db_session.flush()

    prof2 = DoctorProfile(user_id=doc2.id, specialty='Cardio', city='Oran', waiting_room_count=0)
    db_session.add(prof2)
    db_session.flush()

    # Patient 1
    pat1 = User(email='patient1@tbib.dz', role='patient', name='Patient Zero', phone='0666666666')
    pat1.set_password('password')
    db_session.add(pat1)

    # Patient 2
    pat2 = User(email='patient2@tbib.dz', role='patient', name='Patient Two', phone='0666666667')
    pat2.set_password('password')
    db_session.add(pat2)

    # Secretary for Doc 1
    sec1 = User(email='sec1@tbib.dz', role='secretary', name='Secretary One', linked_doctor_id=prof1.id)
    sec1.set_password('password')
    db_session.add(sec1)

    db_session.commit()

    return {
        'doc1': doc1, 'prof1': prof1, 'ctype1': ctype1,
        'doc2': doc2, 'prof2': prof2,
        'pat1': pat1, 'pat2': pat2,
        'sec1': sec1
    }
