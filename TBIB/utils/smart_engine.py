"""
TBIB-SmartFlow : Moteur Décisionnel de Gestion de File d'Attente Intelligent

Ce module implémente l'algorithme SmartFlow pour:
- Optimiser automatiquement l'ordre de passage des patients
- Gérer les retards, absences et urgences de manière autonome
- Réduire la charge mentale du médecin à zéro

Auteur: TBIB Development Team
Version: 1.0.0
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from extensions import db
from models import Appointment, User, DoctorProfile


class QueueOptimizer:
    """
    Classe principale du moteur SmartFlow.
    
    Gère le tri intelligent de la file d'attente, le scoring de fiabilité
    des patients, et la détection des dérives temporelles.
    """
    
    # === CONSTANTES DE CONFIGURATION ===
    
    # Poids pour le calcul du score de priorité
    URGENCY_WEIGHT = 100          # Multiplicateur du niveau d'urgence
    DELAY_PENALTY_WEIGHT = 2      # Points perdus par minute de retard
    EARLY_ARRIVAL_BONUS = 10      # Bonus si arrivée <= 5 min avant
    LATE_PENALTY_PER_5MIN = 5     # Pénalité par tranche de 5 min de retard
    
    # Seuils pour la fiabilité
    SHADOW_SLOT_THRESHOLD = 50    # Score en dessous duquel on active le shadow slot
    NO_SHOW_PENALTY = 20          # Points perdus pour une absence
    LATE_PENALTY = 5              # Points perdus pour retard > 15 min
    PUNCTUAL_BONUS = 2            # Points gagnés pour ponctualité
    MAX_RELIABILITY_SCORE = 100   # Score maximum
    MIN_RELIABILITY_SCORE = 0     # Score minimum
    
    # Seuils temporels (en minutes)
    NO_SHOW_THRESHOLD_MINUTES = 15   # Délai avant de considérer un no-show
    DRIFT_ALERT_THRESHOLD = 30       # Retard global déclenchant une alerte
    COMPRESSION_REDUCTION = 5        # Minutes à réduire par RDV si drift
    LATE_THRESHOLD_MINUTES = 15      # Retard patient considéré comme "en retard"
    
    # ========================================
    # MÉTHODE PRINCIPALE: TRI DE LA FILE
    # ========================================
    
    def reorder_queue(self, doctor_id: int) -> List[Dict]:
        """
        Réordonne la file d'attente d'un médecin selon le score de priorité pondéré.
        
        Formule: Score = (UrgencyLevel * 100) - (RetardMinutes * 2) + BonusArrivée
        
        Args:
            doctor_id: ID du profil médecin
            
        Returns:
            Liste ordonnée des RDV avec leur score de priorité
        """
        today = date.today()
        
        # Récupérer tous les patients en attente pour aujourd'hui
        waiting_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status.in_(['waiting', 'checked_in'])
        ).all()
        
        # Calculer le score de priorité pour chaque RDV
        scored_appointments = []
        for appt in waiting_appointments:
            priority_score = self._calculate_priority_score(appt)
            scored_appointments.append({
                'appointment': appt,
                'appointment_id': appt.id,
                'patient_id': appt.patient_id,
                'patient_name': appt.patient.name if appt.patient else 'Inconnu',
                'priority_score': priority_score,
                'urgency_level': appt.urgency_level or 1,
                'is_shadow_slot': appt.is_shadow_slot,
                'scheduled_time': appt.appointment_time,
                'arrival_time': appt.arrival_time,
                'status': appt.status
            })
        
        # Trier par score décroissant (score le plus haut = priorité maximale)
        scored_appointments.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Mettre à jour les numéros de queue
        for idx, item in enumerate(scored_appointments, start=1):
            item['appointment'].queue_number = idx
        
        db.session.commit()
        
        return scored_appointments
    
    def _calculate_priority_score(self, appointment: Appointment) -> float:
        """
        Calcule le score de priorité d'un RDV.
        
        Formule: Score = (UrgencyLevel * 100) - (RetardMinutes * 2) + BonusArrivée
        
        Args:
            appointment: L'objet Appointment à scorer
            
        Returns:
            Score de priorité (float)
        """
        score = 0.0
        
        # 1. Composante Urgence (1-5, où 5 = Vitale)
        urgency = appointment.urgency_level or 1
        score += urgency * self.URGENCY_WEIGHT
        
        # 2. Pénalité de retard (si le patient est arrivé après son heure de RDV)
        if appointment.arrival_time and appointment.appointment_time:
            scheduled_dt = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time
            )
            arrival_dt = appointment.arrival_time
            
            delay_minutes = (arrival_dt - scheduled_dt).total_seconds() / 60
            
            if delay_minutes > 0:
                # Patient en retard: pénalité proportionnelle
                score -= delay_minutes * self.DELAY_PENALTY_WEIGHT
        
        # 3. Bonus/Malus d'arrivée
        arrival_bonus = self._get_arrival_bonus(
            appointment.arrival_time,
            appointment.appointment_time,
            appointment.appointment_date
        )
        score += arrival_bonus
        
        # 4. Léger bonus pour les patients avec un bon score de fiabilité
        if appointment.patient and hasattr(appointment.patient, 'reliability_score'):
            # Bonus de 0 à 10 basé sur le score de fiabilité
            reliability_bonus = (appointment.patient.reliability_score / 100) * 10
            score += reliability_bonus
        
        return round(score, 2)
    
    def _get_arrival_bonus(
        self,
        arrival_time: Optional[datetime],
        appointment_time,
        appointment_date
    ) -> int:
        """
        Calcule le bonus/malus basé sur l'heure d'arrivée.
        
        - Arrivée <= 5 min avant: +10 pts
        - Chaque tranche de 5 min de retard: -5 pts
        
        Args:
            arrival_time: Heure d'arrivée réelle (datetime)
            appointment_time: Heure du RDV (time)
            appointment_date: Date du RDV (date)
            
        Returns:
            Bonus en points (peut être négatif)
        """
        if not arrival_time or not appointment_time:
            return 0
        
        scheduled_dt = datetime.combine(appointment_date, appointment_time)
        diff_minutes = (arrival_time - scheduled_dt).total_seconds() / 60
        
        if diff_minutes <= 5:
            # Arrivée à l'heure ou en avance
            return self.EARLY_ARRIVAL_BONUS
        else:
            # Arrivée en retard: pénalité par tranche de 5 min
            late_tranches = int(diff_minutes // 5)
            return -late_tranches * self.LATE_PENALTY_PER_5MIN
    
    # ========================================
    # GESTION DU SCORE DE FIABILITÉ
    # ========================================
    
    def check_reliability(self, patient_id: int, event_type: str) -> float:
        """
        Met à jour le score de fiabilité d'un patient après un événement.
        
        Règles:
        - NO_SHOW: -20 pts (absence non excusée)
        - LATE: -5 pts (retard > 15 min)
        - PUNCTUAL: +2 pts (présence à l'heure, max 100)
        
        Args:
            patient_id: ID du patient
            event_type: Type d'événement ('NO_SHOW', 'LATE', 'PUNCTUAL')
            
        Returns:
            Nouveau score de fiabilité
        """
        patient = User.query.get(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} non trouvé")
        
        current_score = patient.reliability_score or 100.0
        
        if event_type == 'NO_SHOW':
            # Absence non excusée: forte pénalité
            new_score = max(
                self.MIN_RELIABILITY_SCORE,
                current_score - self.NO_SHOW_PENALTY
            )
            # Incrémenter aussi le compteur de no-shows
            patient.no_show_count = (patient.no_show_count or 0) + 1
            
        elif event_type == 'LATE':
            # Retard significatif (> 15 min)
            new_score = max(
                self.MIN_RELIABILITY_SCORE,
                current_score - self.LATE_PENALTY
            )
            
        elif event_type == 'PUNCTUAL':
            # Patient ponctuel: récompense (plafonné à 100)
            new_score = min(
                self.MAX_RELIABILITY_SCORE,
                current_score + self.PUNCTUAL_BONUS
            )
            
        else:
            raise ValueError(f"Type d'événement inconnu: {event_type}")
        
        patient.reliability_score = new_score
        db.session.commit()
        
        return new_score
    
    def should_use_shadow_slot(self, patient_id: int) -> bool:
        """
        Détermine si un patient doit être placé en shadow slot.
        
        Critère: Score de fiabilité < 50
        
        Args:
            patient_id: ID du patient
            
        Returns:
            True si le patient devrait être en shadow slot
        """
        patient = User.query.get(patient_id)
        if not patient:
            return False
        
        return (patient.reliability_score or 100) < self.SHADOW_SLOT_THRESHOLD
    
    # ========================================
    # GESTION DES SHADOW SLOTS
    # ========================================
    
    def handle_shadow_resolution(self, appointment_id: int) -> Dict:
        """
        Résout les conflits de shadow slot au moment du check-in.
        
        Logique:
        - Si les deux patients (normal + shadow) sont présents:
          → Le shadow est basculé en mode ticket prioritaire
        - Si un seul est présent:
          → Ce patient prend le créneau normalement
        
        Args:
            appointment_id: ID du RDV concerné
            
        Returns:
            Dict avec le résultat de la résolution
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {'status': 'error', 'message': 'RDV non trouvé'}
        
        # Trouver les RDV sur le même créneau
        same_slot_appointments = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == appointment.appointment_date,
            Appointment.appointment_time == appointment.appointment_time,
            Appointment.status.in_(['confirmed', 'waiting', 'checked_in']),
            Appointment.id != appointment_id
        ).all()
        
        if not same_slot_appointments:
            # Pas de conflit: check-in normal
            return {
                'status': 'ok',
                'message': 'Pas de conflit',
                'action': 'normal_checkin'
            }
        
        # Compter les patients présents (checked_in ou avec arrival_time)
        present_patients = [
            a for a in same_slot_appointments
            if a.status == 'checked_in' or a.arrival_time is not None
        ]
        
        # Vérifier si le RDV courant est un shadow
        if appointment.is_shadow_slot:
            if present_patients:
                # Le patient normal est déjà là: le shadow passe en mode ticket
                return {
                    'status': 'shadow_to_ticket',
                    'message': 'Patient normal déjà présent, shadow basculé en ticket',
                    'action': 'convert_to_ticket',
                    'original_appointment_id': present_patients[0].id
                }
            else:
                # Le shadow est arrivé en premier: il garde le créneau
                return {
                    'status': 'shadow_takes_slot',
                    'message': 'Shadow prend le créneau (patient normal absent)',
                    'action': 'normal_checkin'
                }
        else:
            # C'est le patient normal
            shadow_present = [a for a in present_patients if a.is_shadow_slot]
            if shadow_present:
                # Le shadow doit être basculé en ticket
                for shadow_appt in shadow_present:
                    shadow_appt.booking_type = 'ticket'
                    # Donner un numéro de queue au shadow
                    max_queue = db.session.query(db.func.max(Appointment.queue_number)).filter(
                        Appointment.doctor_id == appointment.doctor_id,
                        Appointment.appointment_date == appointment.appointment_date
                    ).scalar() or 0
                    shadow_appt.queue_number = max_queue + 1
                
                db.session.commit()
                
                return {
                    'status': 'normal_priority',
                    'message': 'Patient normal prioritaire, shadow(s) basculé(s) en ticket',
                    'action': 'resolve_shadow',
                    'shadows_converted': len(shadow_present)
                }
            
            return {
                'status': 'ok',
                'message': 'Check-in normal',
                'action': 'normal_checkin'
            }
    
    # ========================================
    # DÉTECTION DE DRIFT & COMPRESSION
    # ========================================
    
    def detect_drift(self, doctor_id: int) -> Dict:
        """
        Calcule le retard global du médecin et propose des actions correctives.
        
        Si retard > 30 min: Proposer une "Compression" (réduire durée des RDV suivants)
        
        Args:
            doctor_id: ID du profil médecin
            
        Returns:
            Dict avec l'analyse du drift et les recommandations
        """
        now = datetime.now()
        today = date.today()
        
        # Récupérer le dernier RDV terminé pour calculer le retard réel
        last_completed = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status == 'completed'
        ).order_by(Appointment.appointment_time.desc()).first()
        
        # Récupérer le prochain RDV prévu
        next_scheduled = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status.in_(['confirmed', 'waiting', 'checked_in']),
            Appointment.appointment_time != None
        ).order_by(Appointment.appointment_time.asc()).first()
        
        drift_info = {
            'drift_minutes': 0,
            'is_behind': False,
            'should_compress': False,
            'compression_suggestion': None,
            'next_appointment': None,
            'remaining_appointments': 0
        }
        
        if not next_scheduled:
            drift_info['message'] = 'Aucun RDV en attente'
            return drift_info
        
        # Calculer le drift: différence entre l'heure actuelle et l'heure prévue du prochain RDV
        scheduled_time = datetime.combine(today, next_scheduled.appointment_time)
        drift_minutes = (now - scheduled_time).total_seconds() / 60
        
        drift_info['drift_minutes'] = round(drift_minutes, 1)
        drift_info['is_behind'] = drift_minutes > 0
        drift_info['next_appointment'] = {
            'id': next_scheduled.id,
            'patient_name': next_scheduled.patient.name if next_scheduled.patient else 'Inconnu',
            'scheduled_time': next_scheduled.appointment_time.strftime('%H:%M') if next_scheduled.appointment_time else None
        }
        
        # Compter les RDV restants
        remaining = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status.in_(['confirmed', 'waiting', 'checked_in'])
        ).count()
        drift_info['remaining_appointments'] = remaining
        
        # Proposer une compression si retard > 30 min
        if drift_minutes > self.DRIFT_ALERT_THRESHOLD:
            drift_info['should_compress'] = True
            drift_info['compression_suggestion'] = {
                'action': 'reduce_duration',
                'reduction_minutes': self.COMPRESSION_REDUCTION,
                'message': f"Retard de {round(drift_minutes)} min détecté. "
                          f"Suggestion: réduire les {remaining} RDV suivants de {self.COMPRESSION_REDUCTION} min chacun.",
                'potential_recovery': remaining * self.COMPRESSION_REDUCTION
            }
        
        return drift_info
    
    def apply_compression(self, doctor_id: int, reduction_minutes: int = 5) -> Dict:
        """
        Applique une compression aux RDV restants de la journée.
        
        Args:
            doctor_id: ID du profil médecin
            reduction_minutes: Minutes à retirer par RDV (défaut: 5)
            
        Returns:
            Dict avec le résumé des modifications
        """
        today = date.today()
        now = datetime.now()
        
        # Récupérer les RDV futurs
        future_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status.in_(['confirmed', 'waiting']),
            Appointment.appointment_time != None
        ).order_by(Appointment.appointment_time.asc()).all()
        
        compressed_count = 0
        new_times = []
        
        # Décaler chaque RDV en fonction du cumul de compression
        cumulative_shift = timedelta(minutes=0)
        
        for appt in future_appointments:
            if appt.appointment_time:
                original_time = datetime.combine(today, appt.appointment_time)
                
                # Ne traiter que les RDV futurs
                if original_time > now:
                    # Décaler ce RDV
                    cumulative_shift += timedelta(minutes=reduction_minutes)
                    new_time = original_time - cumulative_shift
                    
                    # S'assurer qu'on ne met pas un RDV dans le passé
                    if new_time > now:
                        appt.appointment_time = new_time.time()
                        compressed_count += 1
                        new_times.append({
                            'appointment_id': appt.id,
                            'old_time': original_time.strftime('%H:%M'),
                            'new_time': new_time.strftime('%H:%M')
                        })
        
        db.session.commit()
        
        return {
            'status': 'ok',
            'compressed_count': compressed_count,
            'total_recovery_minutes': compressed_count * reduction_minutes,
            'modified_appointments': new_times
        }
    
    # ========================================
    # WATCHDOG: DÉTECTION DES NO-SHOWS
    # ========================================
    
    def detect_no_shows(self, doctor_id: int) -> List[Dict]:
        """
        Détecte les patients suspectés absents (> 15 min après leur RDV sans check-in).
        
        Met à jour le statut en 'suspected_missing' et retourne la liste.
        
        Args:
            doctor_id: ID du profil médecin
            
        Returns:
            Liste des RDV suspectés comme no-shows
        """
        now = datetime.now()
        today = date.today()
        threshold = now - timedelta(minutes=self.NO_SHOW_THRESHOLD_MINUTES)
        
        # Trouver les RDV confirmés sans check-in dont l'heure est dépassée de 15+ min
        overdue_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today,
            Appointment.status == 'confirmed',
            Appointment.appointment_time != None,
            Appointment.check_in_time == None  # Pas de check-in
        ).all()
        
        suspected_missing = []
        
        for appt in overdue_appointments:
            appointment_dt = datetime.combine(today, appt.appointment_time)
            
            # Si l'heure du RDV + 15 min est dépassée
            if appointment_dt + timedelta(minutes=self.NO_SHOW_THRESHOLD_MINUTES) < now:
                # Marquer comme suspected_missing
                appt.status = 'suspected_missing'
                
                suspected_missing.append({
                    'appointment_id': appt.id,
                    'patient_id': appt.patient_id,
                    'patient_name': appt.patient.name if appt.patient else 'Inconnu',
                    'patient_phone': appt.patient.phone if appt.patient else None,
                    'scheduled_time': appt.appointment_time.strftime('%H:%M'),
                    'minutes_overdue': round((now - appointment_dt).total_seconds() / 60),
                    'action_suggested': 'Appeler le patient ou passer au suivant'
                })
        
        if suspected_missing:
            db.session.commit()
        
        return suspected_missing
    
    def confirm_no_show(self, appointment_id: int) -> Dict:
        """
        Confirme un no-show et applique les pénalités au patient.
        
        Args:
            appointment_id: ID du RDV
            
        Returns:
            Dict avec le résultat de l'opération
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {'status': 'error', 'message': 'RDV non trouvé'}
        
        # Passer le statut à 'no_show'
        appointment.status = 'no_show'
        
        # Appliquer la pénalité de fiabilité
        if appointment.patient_id:
            new_score = self.check_reliability(appointment.patient_id, 'NO_SHOW')
        else:
            new_score = None
        
        db.session.commit()
        
        return {
            'status': 'ok',
            'appointment_id': appointment_id,
            'new_reliability_score': new_score,
            'message': 'No-show confirmé, pénalité appliquée'
        }
    
    # ========================================
    # ÉTAT GLOBAL DE LA FILE
    # ========================================
    
    def get_queue_status(self, doctor_id: int) -> Dict:
        """
        Retourne l'état complet de la file d'attente d'un médecin.
        
        Args:
            doctor_id: ID du profil médecin
            
        Returns:
            Dict avec toutes les métriques de la file
        """
        today = date.today()
        now = datetime.now()
        
        # Statistiques par statut
        status_counts = {}
        for status in ['confirmed', 'waiting', 'checked_in', 'in_progress', 
                       'completed', 'cancelled', 'no_show', 'suspected_missing']:
            count = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == today,
                Appointment.status == status
            ).count()
            status_counts[status] = count
        
        # File d'attente ordonnée
        ordered_queue = self.reorder_queue(doctor_id)
        
        # Détection de drift
        drift_info = self.detect_drift(doctor_id)
        
        # No-shows suspectés
        no_shows = self.detect_no_shows(doctor_id)
        
        # Temps d'attente estimé (20 min par patient en attente)
        waiting_count = status_counts.get('waiting', 0) + status_counts.get('checked_in', 0)
        estimated_wait = waiting_count * 20  # minutes
        
        return {
            'doctor_id': doctor_id,
            'timestamp': now.isoformat(),
            'statistics': {
                'total_today': sum(status_counts.values()),
                'by_status': status_counts,
                'waiting_count': waiting_count,
                'estimated_wait_minutes': estimated_wait
            },
            'ordered_queue': [
                {
                    'position': idx + 1,
                    'appointment_id': item['appointment_id'],
                    'patient_name': item['patient_name'],
                    'priority_score': item['priority_score'],
                    'urgency_level': item['urgency_level'],
                    'is_shadow': item['is_shadow_slot'],
                    'status': item['status']
                }
                for idx, item in enumerate(ordered_queue)
            ],
            'drift': drift_info,
            'suspected_no_shows': no_shows,
            'alerts': self._generate_alerts(drift_info, no_shows, status_counts)
        }
    
    def _generate_alerts(
        self,
        drift_info: Dict,
        no_shows: List[Dict],
        status_counts: Dict
    ) -> List[Dict]:
        """
        Génère des alertes basées sur l'état de la file.
        
        Returns:
            Liste d'alertes avec niveau et message
        """
        alerts = []
        
        # Alerte drift
        if drift_info.get('should_compress'):
            alerts.append({
                'level': 'warning',
                'type': 'drift',
                'message': f"Retard de {drift_info['drift_minutes']:.0f} min. "
                          f"Compression recommandée.",
                'action': 'compress'
            })
        
        # Alertes no-shows
        for ns in no_shows:
            alerts.append({
                'level': 'info',
                'type': 'no_show',
                'message': f"{ns['patient_name']} non présent(e) "
                          f"({ns['minutes_overdue']} min de retard)",
                'action': 'call_or_skip',
                'appointment_id': ns['appointment_id']
            })
        
        # Alerte file longue
        waiting = status_counts.get('waiting', 0) + status_counts.get('checked_in', 0)
        if waiting > 10:
            alerts.append({
                'level': 'warning',
                'type': 'queue_long',
                'message': f"{waiting} patients en attente",
                'action': 'none'
            })
        
        return alerts


# === FONCTIONS UTILITAIRES EXPORTÉES ===

def create_queue_optimizer() -> QueueOptimizer:
    """Factory function pour créer une instance de QueueOptimizer."""
    return QueueOptimizer()


def book_with_shadow_check(patient_id: int, doctor_id: int, **kwargs) -> Tuple[Appointment, bool]:
    """
    Crée un RDV en vérifiant si le patient doit être en shadow slot.
    
    Args:
        patient_id: ID du patient
        doctor_id: ID du médecin
        **kwargs: Autres champs du RDV
        
    Returns:
        Tuple (Appointment créé, is_shadow_slot)
    """
    optimizer = QueueOptimizer()
    is_shadow = optimizer.should_use_shadow_slot(patient_id)
    
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        is_shadow_slot=is_shadow,
        **kwargs
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return appointment, is_shadow


def process_checkin(appointment_id: int) -> Dict:
    """
    Traite le check-in d'un patient avec résolution des conflits shadow.
    
    Args:
        appointment_id: ID du RDV
        
    Returns:
        Dict avec le résultat du check-in
    """
    optimizer = QueueOptimizer()
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return {'status': 'error', 'message': 'RDV non trouvé'}
    
    now = datetime.now()
    
    # Enregistrer l'heure d'arrivée et de check-in
    if not appointment.arrival_time:
        appointment.arrival_time = now
    appointment.check_in_time = now
    appointment.status = 'checked_in'
    
    # Déterminer le type d'événement pour la fiabilité
    if appointment.appointment_time:
        scheduled_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
        delay_minutes = (now - scheduled_dt).total_seconds() / 60
        
        if delay_minutes > QueueOptimizer.LATE_THRESHOLD_MINUTES:
            event_type = 'LATE'
        else:
            event_type = 'PUNCTUAL'
        
        # Mettre à jour la fiabilité
        optimizer.check_reliability(appointment.patient_id, event_type)
    
    # Résoudre les conflits shadow si nécessaire
    shadow_resolution = optimizer.handle_shadow_resolution(appointment_id)
    
    db.session.commit()
    
    # Réordonner la file
    optimizer.reorder_queue(appointment.doctor_id)
    
    return {
        'status': 'ok',
        'check_in_time': now.isoformat(),
        'shadow_resolution': shadow_resolution
    }
