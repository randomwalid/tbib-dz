from flask import Blueprint, jsonify, request, current_app
import hmac
import hashlib
import json
import os
from datetime import datetime
from extensions import db
from models import Prescription

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')

@pharmacy_bp.route('/verify/<token>', methods=['GET'])
def verify_prescription(token):
    prescription = Prescription.query.filter_by(token=token).first()

    if not prescription:
        return jsonify({"valid": False, "reason": "Ordonnance introuvable"}), 404

    # Vérifier signature
    payload = {
        'doctor_id': prescription.doctor_id,
        'patient_id': prescription.patient_id,
        'medications': prescription.medications,
        # We need the original timestamp used for signing.
        # It was stored in created_at, but we need to convert to int timestamp.
        # Warning: ensure created_at in DB matches the one used for signing.
        # prescription.created_at is a DateTime.
        'timestamp': int(prescription.created_at.timestamp())
    }

    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        current_app.config['SECRET_KEY'].encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()

    if signature != prescription.security_hash:
        return jsonify({"valid": False, "status": "tampered", "reason": "Signature invalide / Ordonnance modifiée"}), 200 # Using 200 as per prompt logic inference, or maybe 400? Prompt said "Retourner un JSON clair".
        # Prompt examples used 400 for errors. I will use 200 with valid:False for tampering as it's a verification result.
        # Wait, prompt said: if dispensed -> 400. if expired -> 400.
        # So I'll default to 200 unless it's a "known bad state" that implies "Bad Request"?
        # Actually, tampering is critical. I'll return 200 with valid=False so the client app can display "INVALID".
        # 400 usually implies client error.

    # Vérifier statut
    if prescription.status == 'dispensed':
        return jsonify({"valid": False, "status": "dispensed", "reason": "Déjà servie"}), 400

    # Vérifier expiration
    if prescription.expiry_date and datetime.utcnow() > prescription.expiry_date:
        return jsonify({"valid": False, "status": "expired", "reason": "Ordonnance périmée"}), 400

    return jsonify({
        "valid": True,
        "status": "pending",
        "prescription_details": {
            "doctor": prescription.doctor.name if prescription.doctor else "Inconnu",
            "medications": prescription.medications,
            "expiry": prescription.expiry_date.isoformat()
        }
    }), 200

@pharmacy_bp.route('/dispense/<token>', methods=['POST'])
def dispense_prescription(token):
    # Vérifier API Key dans header
    api_key = request.headers.get('X-Pharmacy-Key')
    expected_key = os.environ.get('PHARMACY_API_KEY')

    if not expected_key:
        # Fallback for dev if not set (though instructions said verify strictly)
        # But if env var is missing, logic fails secure (deny all).
        # Unless I set a default in config.
        # Prompt Task 4: "if api_key != os.environ.get('PHARMACY_API_KEY'): return 401"
        pass

    if not api_key or api_key != expected_key:
        return jsonify({"error": "Non autorisé"}), 401

    prescription = Prescription.query.filter_by(token=token).first()

    if not prescription:
         return jsonify({"error": "Ordonnance introuvable"}), 404

    if prescription.status == 'dispensed':
        return jsonify({"error": "Déjà servie"}), 400

    prescription.status = 'dispensed'
    prescription.usage_count += 1
    prescription.last_verified_at = datetime.utcnow()
    db.session.commit()

    # Audit log (Task 4 says "Log l'action dans la table AuditLog (si elle existe)")
    # We checked models.py and AuditLog does not exist.
    # So we log to app logger.
    current_app.logger.info(f"Prescription {token} dispensed by pharmacy.")

    return jsonify({"success": True, "message": "Ordonnance marquée comme servie"}), 200
