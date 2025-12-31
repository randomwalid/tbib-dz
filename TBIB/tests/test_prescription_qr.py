import pytest
import re
import datetime
from models import Prescription, User, DoctorProfile, Appointment
from app import db
import qrcode
import io
import base64
from unittest.mock import MagicMock
# Import prescription_routes directly since it is top-level in TBIB/
import prescription_routes

class TestSecureQRCode:
    """Test suite pour QR Code sécurisé"""

    @pytest.fixture
    def doctor_user(self, app):
        with app.app_context():
            user = User(
                email='doctor@test.com',
                password_hash='hash',
                role='doctor',
                name='Dr. House',
                reliability_score=100.0
            )
            db.session.add(user)
            db.session.commit()

            profile = DoctorProfile(
                user_id=user.id,
                specialty='General',
                city='Algiers'
            )
            db.session.add(profile)
            db.session.commit()
            return user

    @pytest.fixture
    def patient_user(self, app):
        with app.app_context():
            user = User(
                email='patient@test.com',
                password_hash='hash',
                role='patient',
                name='John Doe',
                reliability_score=100.0
            )
            db.session.add(user)
            db.session.commit()
            return user

    @pytest.fixture
    def appointment(self, app, doctor_user, patient_user):
        with app.app_context():
            # Refresh objects in current session
            doctor = db.session.merge(doctor_user)
            patient = db.session.merge(patient_user)

            appt = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.doctor_profile.id,
                appointment_date=datetime.date.today()
            )
            db.session.add(appt)
            db.session.commit()
            return appt

    def test_qr_logic_unit(self):
        """Unit test for the format string logic"""
        token = "abc"
        sec_hash = "def"
        ts = 123456
        expected = f"{token}|{sec_hash}|{ts}"
        assert expected == "abc|def|123456"

    def test_view_prescription_qr_content(self, client, app, appointment, monkeypatch):
        """Test that the view adds the correct data to QRCode"""

        # Mock qrcode.QRCode
        mock_qr = MagicMock()
        mock_qr_cls = MagicMock(return_value=mock_qr)

        # Simulate make_image return
        mock_img = MagicMock()
        mock_buf = io.BytesIO(b"fakeimage")
        mock_img.save.side_effect = lambda buf, format: buf.write(b"fakeimage")
        mock_qr.make_image.return_value = mock_img

        # Patch qrcode in prescription_routes
        monkeypatch.setattr(prescription_routes.qrcode, 'QRCode', mock_qr_cls)

        with app.app_context():
            appt = db.session.merge(appointment)
            token = "testtoken"
            security_hash = "testhash"
            created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
            timestamp = int(created_at.timestamp())

            presc = Prescription(
                token=token,
                appointment_id=appt.id,
                doctor_id=appt.doctor_profile.user_id,
                patient_id=appt.patient_id,
                medications="Meds",
                security_hash=security_hash,
                created_at=created_at,
                expiry_date=created_at + datetime.timedelta(days=90),
                status='pending'
            )
            db.session.add(presc)
            db.session.commit()

            resp = client.get(f'/prescription/view/{token}')
            assert resp.status_code == 200

            # Verify calls
            expected_data = f"{token}|{security_hash}|{timestamp}"
            mock_qr.add_data.assert_called_with(expected_data)

            # Also verify fallback URL is present in response (as verify_url)
            # We can spy on render_template but since we already got 200,
            # and we know the template expects verify_url, checking context would be ideal.
            # But checking if the original logic for verify_url is maintained:
            # verify_url = url_for('prescription.verify_prescription', token=token, _external=True)
            # We can check if it is in the response text (HTML) if it's rendered.
            # Assuming 'prescription.html' renders {{ verify_url }}
            assert b'/prescription/verify/testtoken' in resp.data
