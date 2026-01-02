"""
SmartFlow Service - Logique métier pour la gestion intelligente des RDV.

Fonctionnalités :
- Calcul Patient Reliability Score (PRS)
- Gestion Shadow Slots (Surbooking intelligent)
- Détection de drift (Retard accumulé)
- Optimisation de la file d'attente
"""

from models import Appointment, User
from extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import func
from utils.smart_engine import QueueOptimizer


class SmartFlowService:
    """Service centralisant la logique SmartFlow."""

    # ========================================================================
    # PATIENT RELIABILITY SCORE (PRS)
    # ========================================================================

    @staticmethod
    def update_prs_on_present(patient_id):
        """Augmente le PRS de +2 quand un patient se présente."""
        patient = User.query.get(patient_id)
        if not patient:
            return None

        current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
        patient.reliability_score = min(100.0, current_score + 2.0)

        # Pas de commit ici (fait par la route)
        return patient.reliability_score

    @staticmethod
    def update_prs_on_noshow(patient_id):
        """Diminue le PRS de -20 quand un patient est absent."""
        patient = User.query.get(patient_id)
        if not patient:
            return None

        current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
        patient.reliability_score = max(0.0, current_score - 20.0)
        patient.no_show_count = (patient.no_show_count or 0) + 1

        return patient.reliability_score

    @staticmethod
    def restore_prs_after_error(patient_id, reason='error'):
        """
        Restaure le PRS après une erreur ou un retard.

        Args:
            patient_id: UUID du patient
            reason: 'error' (restore +20) ou 'late' (restore +20 puis -5)

        Returns:
            dict: {'new_score': float, 'action': str}
        """
        patient = User.query.get(patient_id)
        if not patient:
            return None

        # Restaurer les points (annule le -20)
        current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
        restored_score = min(100.0, current_score + 20.0)
        patient.reliability_score = restored_score

        # Décrémenter no_show_count
        if patient.no_show_count and patient.no_show_count > 0:
            patient.no_show_count -= 1

        # Pénalité retard si applicable
        if reason == 'late':
            patient.reliability_score = max(0.0, patient.reliability_score - 5.0)
            action = 'Retard : -5 pts appliqués'
        else:
            action = 'Erreur corrigée : +20 pts restaurés'

        return {
            'new_score': patient.reliability_score,
            'action': action
        }

    # ========================================================================
    # SHADOW SLOTS (SURBOOKING INTELLIGENT)
    # ========================================================================

    @staticmethod
    def should_create_shadow_slot(patient_id, doctor_id, appointment_date, appointment_time):
        """
        Décide si un Shadow Slot doit être créé pour un patient à risque.

        Règle : Si PRS < 50 (RED TIER) ET pas déjà de shadow slot sur ce créneau.

        Args:
            patient_id: UUID du patient
            doctor_id: ID du docteur
            appointment_date: Date du RDV
            appointment_time: Heure du RDV

        Returns:
            bool: True si Shadow Slot nécessaire
        """
        # Récupérer le patient
        patient = User.query.get(patient_id)
        if not patient:
            return False

        # Calculer le score
        patient_score = patient.reliability_score if patient.reliability_score is not None else 100

        # Vérifier s'il y a déjà un shadow slot
        has_shadow = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            is_shadow_slot=True
        ).first() is not None

        # Décision : RED TIER + Pas de shadow existant
        return patient_score < 50 and not has_shadow

    # ========================================================================
    # DRIFT DETECTION (RETARD ACCUMULÉ)
    # ========================================================================

    @staticmethod
    def get_drift_info(doctor_id):
        """
        Wrapper pour QueueOptimizer.detect_drift().

        Args:
            doctor_id: ID du docteur

        Returns:
            dict: {'drift_minutes': int, 'is_behind': bool, ...}
        """
        optimizer = QueueOptimizer()
        return optimizer.detect_drift(doctor_id)

    # ========================================================================
    # QUEUE MANAGEMENT
    # ========================================================================
    
    @staticmethod
    def assign_queue_number(doctor_id, appointment_date):
        """
        Génère le prochain numéro de file d'attente pour un médecin/date.

        Args:
            doctor_id: ID du docteur
            appointment_date: Date du RDV

        Returns:
            int: Prochain numéro (ex: 5)
        """
        max_queue = db.session.query(func.max(Appointment.queue_number)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date
        ).scalar() or 0

        return max_queue + 1
