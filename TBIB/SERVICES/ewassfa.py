"""
E-Wassfa Service - Ordonnances électroniques sécurisées.

Fonctionnalités :
- Génération de tokens uniques (8 caractères)
- Signature HMAC-SHA256 (anti-falsification)
- Génération de QR Codes pour pharmaciens
- Validation d'ordonnances (expiry, usage)

Conformité : Loi 18-07 (Souveraineté des données médicales)
"""

import secrets
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import qrcode
import io
import base64
from flask import current_app
from models import Prescription


class EWassfaService:
    """Service centralisant la logique E-Wassfa."""

    # ========================================================================
    # TOKEN GENERATION (IDENTIFIANT UNIQUE)
    # ========================================================================

    @staticmethod
    def generate_token():
        """Génère un token unique de 8 caractères hexadécimaux."""
        return secrets.token_hex(4)

    # ========================================================================
    # EXPIRY & MAX USAGE CALCULATION
    # ========================================================================

    @staticmethod
    def calculate_expiry_and_usage(prescription_type):
        """Calcule la date d'expiration et le nombre max d'utilisations."""
        if prescription_type == 'ACUTE':
            expiry = datetime.utcnow() + timedelta(days=30)
            max_usage = 1
        else:  # CHRONIC
            expiry = datetime.utcnow() + timedelta(days=365)
            max_usage = 999

        return expiry, max_usage

    # ========================================================================
    # HMAC SIGNATURE (ANTI-FALSIFICATION)
    # ========================================================================

    @staticmethod
    def create_hmac_signature(doctor_id, patient_id, medications, timestamp):
        """
        Crée une signature HMAC-SHA256 pour l'ordonnance.

        ⚠️  SÉCURITÉ CRITIQUE : Ne JAMAIS modifier cette fonction sans audit.
        """
        payload = {
            'doctor_id': doctor_id,
            'patient_id': patient_id,
            'medications': medications,
            'timestamp': timestamp
        }
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            current_app.config['SECRET_KEY'].encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    # ========================================================================
    # QR CODE GENERATION (SCAN PHARMACIEN)
    # ========================================================================

    @staticmethod
    def generate_qr_code(verify_url):
        """Génère un QR Code encodé en base64."""
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(verify_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode()

        return qr_code_base64

    # ========================================================================
    # VALIDATION (EXPIRY + USAGE)
    # ========================================================================
    
    @staticmethod
    def validate_prescription(prescription):
        """Vérifie si une ordonnance est encore valide."""
        is_valid = True
        error_message = None

        if prescription.usage_count >= prescription.max_usage:
            is_valid = False
            error_message = "Ordonnance déjà utilisée (maximum atteint)"

        if prescription.expiry_date < datetime.utcnow():
            is_valid = False
            error_message = "Ordonnance expirée"

        return {
            'is_valid': is_valid,
            'error_message': error_message
        }
