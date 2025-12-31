import pytest
import json
import hashlib
import hmac
import datetime
from app import create_app, db
from models import Prescription, User, DoctorProfile, Appointment

class TestPharmacyEndpointsSecurity:
    """Tests de sécurité des endpoints pharmacien"""

    @pytest.fixture
    def app(self):
        # Setup specific app config for testing
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def valid_prescription(self, app):
        with app.app_context():
            # Create minimal graph
            doc_user = User(email='d@t.com', password_hash='x', role='doctor', name='Dr', reliability_score=100)
            pat_user = User(email='p@t.com', password_hash='x', role='patient', name='Pat', reliability_score=100)
            db.session.add_all([doc_user, pat_user])
            db.session.commit()

            profile = DoctorProfile(user_id=doc_user.id, specialty='X', city='Y')
            db.session.add(profile)
            db.session.commit()

            appt = Appointment(patient_id=pat_user.id, doctor_id=profile.id, appointment_date=datetime.date.today())
            db.session.add(appt)
            db.session.commit()

            # Create Prescription with valid hash
            ts = int(datetime.datetime.utcnow().timestamp())
            payload = {
                'doctor_id': doc_user.id,
                'patient_id': pat_user.id,
                'medications': 'Meds',
                'timestamp': ts
            }
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                b'test-secret',
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            presc = Prescription(
                token='validtoken',
                appointment_id=appt.id,
                doctor_id=doc_user.id,
                patient_id=pat_user.id,
                medications='Meds',
                security_hash=signature,
                created_at=datetime.datetime.fromtimestamp(ts),
                expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=30),
                status='pending',
                max_usage=1,
                usage_count=0
            )
            db.session.add(presc)
            db.session.commit()
            return presc

    def test_verify_rejects_invalid_token(self, client):
        """Reject un token inexistant"""
        response = client.get('/pharmacy/verify/FAKETOKEN123')
        assert response.status_code == 404
        assert b"introuvable" in response.data or b"Not Found" in response.data

    def test_verify_valid_prescription(self, client, valid_prescription):
        """Valid prescription returns 200 and details"""
        response = client.get('/pharmacy/verify/validtoken')
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is True
        assert data['status'] == 'pending'

    def test_verify_detects_tampered_prescription(self, client, app, valid_prescription):
        """Détecte une prescription modifiée (hash mismatch)"""
        with app.app_context():
            # Modify medication directly in DB without updating hash
            p = Prescription.query.filter_by(token='validtoken').first()
            p.medications = "Dangerous Drugs"
            db.session.commit()

        response = client.get('/pharmacy/verify/validtoken')
        assert response.status_code == 200 # It returns 200 but with valid=False usually? Or 400? Prompt said "Retourner un JSON clair".
        # The prompt for verify endpoint structure:
        # if not prescription: 404
        # if dispensed: 400
        # if expired: 400
        # But for signature mismatch? It wasn't explicitly defined in return codes,
        # but logic implies valid=False.
        # I'll expect valid=False in JSON.

        data = response.get_json()
        assert data['valid'] is False
        assert "ignature" in data['reason'] or "odifi" in data['reason'] # "Modifiée"

    def test_dispense_requires_api_key(self, client):
        """Dispense DOIT refuser sans API Key"""
        response = client.post('/pharmacy/dispense/validtoken')
        assert response.status_code == 401

    def test_dispense_rejects_wrong_api_key(self, client):
        """Dispense rejette une mauvaise clé"""
        response = client.post(
            '/pharmacy/dispense/validtoken',
            headers={'X-Pharmacy-Key': 'WRONG_KEY'}
        )
        assert response.status_code == 401

    def test_dispense_accepts_valid_key(self, client, valid_prescription, monkeypatch):
        """Dispense accepte la clé correcte"""
        monkeypatch.setenv('PHARMACY_API_KEY', 'TEST-KEY')

        response = client.post(
            '/pharmacy/dispense/validtoken',
            headers={'X-Pharmacy-Key': 'TEST-KEY'}
        )
        assert response.status_code == 200
        assert response.get_json()['success'] is True

        # Verify DB status change
        # Need new request or check DB
        verify = client.get('/pharmacy/verify/validtoken')
        assert verify.get_json()['status'] == 'dispensed'

    def test_cannot_dispense_twice(self, client, valid_prescription, monkeypatch):
        """Une prescription ne peut être servie 2 fois"""
        monkeypatch.setenv('PHARMACY_API_KEY', 'TEST-KEY')

        # First dispense
        client.post('/pharmacy/dispense/validtoken', headers={'X-Pharmacy-Key': 'TEST-KEY'})

        # Second dispense
        response = client.post('/pharmacy/dispense/validtoken', headers={'X-Pharmacy-Key': 'TEST-KEY'})
        assert response.status_code == 400
        # The response is JSON with unicode escaped chars for Déjà servie.
        # Check for status code is sufficient or check JSON content decoded
        assert "ervie" in response.get_json()['error'] or "dispensed" in response.get_json()['error']

    def test_expired_prescription_rejected(self, client, app, valid_prescription):
        """Une prescription périmée est refusée"""
        with app.app_context():
            p = Prescription.query.filter_by(token='validtoken').first()
            p.expiry_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            db.session.commit()

        response = client.get('/pharmacy/verify/validtoken')
        # Expect 400 per prompt instructions
        assert response.status_code == 400
        assert response.get_json()['status'] == 'expired'
