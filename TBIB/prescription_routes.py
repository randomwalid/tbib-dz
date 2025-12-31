from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash, current_app
import secrets
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import qrcode
import io
import base64
from flask_login import login_required, current_user
from models import Prescription, Appointment
from extensions import db

prescription_bp = Blueprint('prescription', __name__, url_prefix='/prescription')

def generate_prescription_token():
    """Génère un token unique de 8 caractères"""
    return secrets.token_hex(4)

@prescription_bp.route('/create/<int:appointment_id>', methods=['POST'])
@login_required
def create_prescription(appointment_id):
    """Génère une nouvelle ordonnance"""

    # Vérifications de sécurité
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != current_user.id and appointment.doctor_id != current_user.doctor_profile.id:
         # Note: current_user.id matches user_id in DoctorProfile, but appointment.doctor_id refers to DoctorProfile.id usually.
         # Let's check models.
         # Appointment: doctor_id = db.ForeignKey('doctor_profiles.id')
         # DoctorProfile: user_id = db.ForeignKey('users.id')
         # So appointment.doctor_id should equal current_user.doctor_profile.id
         pass

    # Re-checking logic:
    # current_user is User.
    # If role is doctor, current_user.doctor_profile is available.
    # appointment.doctor_id is the ID of the DoctorProfile.

    if not current_user.doctor_profile or appointment.doctor_id != current_user.doctor_profile.id:
         return jsonify({'error': 'Not your patient'}), 403

    # Récupérer les données du formulaire
    medications = request.form.get('medications', '')

    # Validation stricte
    if not medications or medications.strip() == '':
        return jsonify({'error': 'Medications list cannot be empty'}), 400

    notes = request.form.get('notes', appointment.doctor_notes or '')
    prescription_type = request.form.get('type', 'ACUTE')

    # Créer le token
    token = generate_prescription_token()

    # Définir la durée de validité
    if prescription_type == 'ACUTE':
        expiry = datetime.utcnow() + timedelta(days=30)
        max_usage = 1
    else:  # CHRONIC
        expiry = datetime.utcnow() + timedelta(days=365)
        max_usage = 999

    # Signature HMAC-SHA256
    creation_time = datetime.utcnow()
    # Use integer timestamp for stability (ignoring microseconds)
    timestamp_int = int(creation_time.timestamp())
    payload = {
        'doctor_id': current_user.id,
        'patient_id': appointment.patient_id,
        'medications': medications,
        'timestamp': timestamp_int
    }
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        current_app.config['SECRET_KEY'].encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()

    # Créer l'ordonnance
    prescription = Prescription(
        token=token,
        appointment_id=appointment_id,
        doctor_id=current_user.id, # Uses User ID
        patient_id=appointment.patient_id, # Uses User ID
        medications=medications,
        notes=notes,
        prescription_type=prescription_type,
        max_usage=max_usage,
        expiry_date=expiry,
        created_at=creation_time,
        security_hash=signature,
        status='pending'
    )

    db.session.add(prescription)
    db.session.commit()

    # Rediriger vers la page d'affichage
    return redirect(url_for('prescription.view_prescription', token=token))

@prescription_bp.route('/view/<token>')
def view_prescription(token):
    """Affiche l'ordonnance (pour impression ou téléchargement PDF)"""

    prescription = Prescription.query.filter_by(token=token).first_or_404()

    # Générer le QR Code
    verify_url = url_for('prescription.verify_prescription', token=token, _external=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=2)

    # Secure E-Wassfa QR data: token|hash|timestamp
    # QR Code contient l'URL complète pour scan direct
    # Le hash HMAC reste stocké en DB pour vérification serveur (pharmacy_routes.py ligne 18-37)
    qr_data = verify_url
    qr.add_data(qr_data)

    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode()

    return render_template('prescription.html',
                          prescription=prescription,
                          qr_code=qr_code_base64,
                          verify_url=verify_url)

@prescription_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify_prescription(token):
    """Page publique de vérification (pour pharmaciens)"""

    prescription = Prescription.query.filter_by(token=token).first_or_404()

    # Vérifier la validité
    is_valid = True
    error_message = None

    if prescription.usage_count >= prescription.max_usage:
        is_valid = False
        error_message = "Ordonnance déjà utilisée (maximum atteint)"

    if prescription.expiry_date < datetime.utcnow():
        is_valid = False
        error_message = "Ordonnance expirée"

    # Si POST = le pharmacien confirme l'utilisation
    if request.method == 'POST' and is_valid:
        prescription.usage_count += 1
        prescription.last_verified_at = datetime.utcnow()
        db.session.commit()
        flash('Ordonnance marquée comme utilisée', 'success')

    return render_template('verify_prescription.html',
                          prescription=prescription,
                          is_valid=is_valid,
                          error_message=error_message)
