from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, DoctorProfile, Appointment, HealthRecord, DoctorAvailability, ConsultationType, DoctorAbsence, Relative, Referral
from utils.engine import calculate_wait_time, shift_appointments, get_conflicting_appointments, cancel_appointments_in_range
from utils.smart_engine import QueueOptimizer
from datetime import date, datetime, timedelta, time

main_bp = Blueprint('main', __name__)

TRANSLATIONS = {
    'fr': {
        'brand': 'TBIB',
        'home': 'Accueil',
        'my_appointments': 'Mes Rendez-vous',
        'dashboard': 'Tableau de bord',
        'login': 'Se connecter',
        'register': "S'inscrire",
        'logout': 'Déconnexion',
        'patient': 'Patient',
        'doctor': 'Médecin',
        'search': 'Rechercher',
        'specialty': 'Spécialité',
        'city': 'Ville',
        'book': 'Prendre RDV',
        'your_turn': 'Votre Tour',
        'current': 'En cours',
        'next_patient': 'Patient Suivant',
        'no_show': 'Absent',
        'complete': 'Terminé',
        'cancel': 'Annuler',
        'email': 'Email',
        'password': 'Mot de passe',
        'name': 'Nom complet',
        'phone': 'Téléphone',
        'find_doctor': 'Trouvez votre médecin',
        'search_subtitle': 'Recherchez par spécialité et ville',
        'all_specialties': 'Toutes les spécialités',
        'all_cities': 'Toutes les villes',
        'available_doctors': 'Médecins disponibles',
        'today_appointments': "Aujourd'hui",
        'queue_status': 'En attente',
        'no_appointments': 'Aucun rendez-vous',
        'appointment_booked': 'Rendez-vous confirmé !',
        'login_required': 'Connectez-vous pour prendre rendez-vous',
        'welcome': 'Bienvenue',
        'address': 'Adresse',
        'bio': 'Biographie',
        'confirmed': 'Confirmé',
        'completed': 'Terminé',
        'cancelled': 'Annulé',
        'no_show_status': 'Absent',
        'waiting': 'En attente',
        'total': 'Total',
        'my_account': 'Mon Compte',
        'my_info': 'Mes informations',
        'health_record': 'Mon Carnet de Santé',
        'security': 'Sécurité',
        'relatives': 'Mes proches',
        'save': 'Enregistrer',
        'blood_type': 'Groupe sanguin',
        'weight': 'Poids (kg)',
        'height': 'Taille (cm)',
        'allergies': 'Allergies & Contre-indications',
        'vaccines': 'Vaccins',
        'dob': 'Date de naissance',
        'your_turn_message': 'Votre tour arrive',
        'estimated_wait_time': "Temps d'attente estimé",
        'confirm_presence': 'Je confirme ma présence',
    },
    'ar': {
        'brand': 'طبيب',
        'home': 'الرئيسية',
        'my_appointments': 'مواعيدي',
        'dashboard': 'لوحة التحكم',
        'login': 'تسجيل الدخول',
        'register': 'التسجيل',
        'logout': 'تسجيل الخروج',
        'patient': 'مريض',
        'doctor': 'طبيب',
        'search': 'بحث',
        'specialty': 'التخصص',
        'city': 'المدينة',
        'book': 'حجز موعد',
        'your_turn': 'دورك',
        'current': 'الحالي',
        'next_patient': 'المريض التالي',
        'no_show': 'غائب',
        'complete': 'مكتمل',
        'cancel': 'إلغاء',
        'email': 'البريد الإلكتروني',
        'password': 'كلمة المرور',
        'name': 'الاسم الكامل',
        'phone': 'الهاتف',
        'find_doctor': 'ابحث عن طبيبك',
        'search_subtitle': 'ابحث حسب التخصص والمدينة',
        'all_specialties': 'جميع التخصصات',
        'all_cities': 'جميع المدن',
        'available_doctors': 'الأطباء المتاحون',
        'today_appointments': 'اليوم',
        'queue_status': 'في الانتظار',
        'no_appointments': 'لا توجد مواعيد',
        'appointment_booked': 'تم تأكيد الموعد!',
        'login_required': 'سجل الدخول لحجز موعد',
        'welcome': 'مرحبا',
        'address': 'العنوان',
        'bio': 'السيرة الذاتية',
        'confirmed': 'مؤكد',
        'completed': 'مكتمل',
        'cancelled': 'ملغى',
        'no_show_status': 'غائب',
        'waiting': 'في الانتظار',
        'total': 'المجموع',
        'my_account': 'حسابي',
        'my_info': 'معلوماتي',
        'health_record': 'السجل الصحي',
        'security': 'الأمان',
        'relatives': 'أقاربي',
        'save': 'حفظ',
        'blood_type': 'فصيلة الدم',
        'weight': 'الوزن',
        'height': 'الطول',
        'allergies': 'الحساسية',
        'vaccines': 'اللقاحات',
        'dob': 'تاريخ الميلاد',
        'your_turn_message': 'دورك يقترب',
        'estimated_wait_time': 'وقت الانتظار المقدر',
        'confirm_presence': 'أؤكد حضوري',
    }
}

def get_t():
    lang = session.get('lang', 'fr')
    return TRANSLATIONS.get(lang, TRANSLATIONS['fr'])

def initialize_demo_data():
    import random

    cities = ["Alger", "Oran", "Constantine", "Annaba", "Setif", "Bejaia", "Tlemcen", "Blida"]
    specialties = ["Médecin Généraliste", "Dentiste", "Cardiologue", "Pédiatre", "Dermatologue", "Gynécologue", "Ophtalmologue"]
    first_names = ["Mohamed", "Amine", "Sarah", "Fatima", "Youssef", "Karim", "Nadia", "Amina", "Rachid", "Leila", "Yasmine", "Omar", "Lina", "Anis"]
    last_names = ["Benali", "Saidi", "Dahmani", "Boudiaf", "Hadj", "Mebarki", "Hamidi", "Cherif", "Bouzid", "Belkacem", "Rahmouni", "Meziane"]
    street_names = ['Didouche Mourad', 'Ben Mhidi', 'Abane Ramdane', 'Amirouche', 'Pasteur']

    for i in range(50):
        first = random.choice(first_names)
        last = random.choice(last_names)
        full_name = f"Dr. {first} {last}"
        city_choice = random.choice(cities)
        specialty = random.choice(specialties)

        user = User(
            email=f"doctor{i+1}@tbib.dz",
            role='doctor',
            name=full_name,
            phone=f"05{random.randint(10000000, 99999999)}",
            city=city_choice
        )
        user.set_password('doctor123')
        db.session.add(user)
        db.session.flush()

        doctor_profile = DoctorProfile(
            user_id=user.id,
            specialty=specialty,
            city=city_choice,
            address=f"{random.randint(1, 200)} Rue {random.choice(street_names)}",
            bio=f"Médecin expérimenté diplômé de l'Université d'Alger, spécialiste en {specialty.lower()} avec plus de 10 ans d'expérience.",
            waiting_room_count=0,
            languages="Français, Arabe",
            payment_methods="Espèces, Carte bancaire"
        )
        db.session.add(doctor_profile)
        db.session.flush()

        start_t = time(9, 0)
        end_t = time(17, 0)
        for day in range(5):
            availability = DoctorAvailability(
                doctor_id=doctor_profile.id,
                day_of_week=day,
                start_time=start_t,
                end_time=end_t,
                is_available=True
            )
            db.session.add(availability)

        consultation = ConsultationType(
            doctor_id=doctor_profile.id,
            name="Consultation",
            duration=30,
            price="2000 DA",
            color="#14b999",
            is_active=True
        )
        db.session.add(consultation)

        urgence = ConsultationType(
            doctor_id=doctor_profile.id,
            name="Urgence",
            duration=15,
            price="3000 DA",
            color="#ef4444",
            is_active=True
        )
        db.session.add(urgence)

    db.session.commit()
    print("✅ DATABASE INITIALIZED: 50 Doctors & Schedules Created!")


@main_bp.route('/legal/cgu')
def legal_cgu():
    return render_template('legal/cgu.html', t=get_t(), lang=session.get('lang', 'fr'))

@main_bp.route('/legal/privacy')
def legal_privacy():
    return render_template('legal/privacy.html', t=get_t(), lang=session.get('lang', 'fr'))

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Ici on pourrait envoyer un email ou sauvegarder le message
        flash('Votre message a bien été envoyé. Nous vous répondrons bientôt.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', t=get_t(), lang=session.get('lang', 'fr'))

@main_bp.route('/')
def home():
        if current_user.is_authenticated and current_user.role == 'doctor':
            return redirect(url_for('main.doctor_dashboard'))

        try:
            doctor_count = DoctorProfile.query.count()
        except:
            db.create_all()
            doctor_count = 0

        if doctor_count == 0:
            print("⚠ DATABASE EMPTY. INITIALIZING DEMO DATA...")
            initialize_demo_data()
            return redirect(url_for('main.home'))

        specialty = request.args.get('specialty', '')
        city = request.args.get('city', '')
        search_mode = bool(specialty or city)
        doctors = []

        if search_mode:
            # ✅ FIX: Spécifie explicitement la condition de jointure
            query = DoctorProfile.query.join(User, DoctorProfile.user_id == User.id)
            if specialty:
                query = query.filter(DoctorProfile.specialty.ilike(f'%{specialty}%'))
            if city:
                query = query.filter(DoctorProfile.city.ilike(f'%{city}%'))
            doctors = query.all()

        specialties = db.session.query(DoctorProfile.specialty).distinct().all()
        cities = db.session.query(DoctorProfile.city).distinct().all()

        return render_template('home.html',
                               doctors=doctors,
                               search_mode=search_mode,
                               specialties=[s[0] for s in specialties],
                               cities=[c[0] for c in cities],
                               selected_specialty=specialty,
                               selected_city=city,
                               t=get_t(),
                               lang=session.get('lang', 'fr'))

@main_bp.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['fr', 'ar']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.home'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    next_url = request.args.get('next', '')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            if user.role == 'doctor':
                return redirect(url_for('main.doctor_dashboard'))
            if user.role == 'secretary':
                return redirect(url_for('main.secretary_dashboard'))
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.home'))
        flash('Email ou mot de passe incorrect', 'error')

    return render_template('login.html', next_url=next_url, t=get_t(), lang=session.get('lang', 'fr'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    role = request.args.get('role', 'patient')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        role = request.form.get('role', 'patient')

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'error')
            return render_template('register.html', role=role, t=get_t(), lang=session.get('lang', 'fr'))

        user = User(email=email, name=name, phone=phone, role=role)
        user.set_password(password)
        db.session.add(user)

        if role == 'doctor':
            specialty = request.form.get('specialty')
            city = request.form.get('city')
            address = request.form.get('address')
            bio = request.form.get('bio')

            db.session.flush()
            doctor_profile = DoctorProfile(
                user_id=user.id,
                specialty=specialty,
                city=city,
                address=address,
                bio=bio
            )
            db.session.add(doctor_profile)

        db.session.commit()
        login_user(user)

        if role == 'doctor':
            return redirect(url_for('main.doctor_dashboard'))
        return redirect(url_for('main.home'))

    return render_template('register.html', role=role, t=get_t(), lang=session.get('lang', 'fr'))

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main_bp.route('/book/<int:doctor_id>', methods=['POST'])
def book_appointment(doctor_id):
    from sqlalchemy.exc import IntegrityError

    if not current_user.is_authenticated:
        return redirect(url_for('main.login', next=url_for('main.doctor_profile', doctor_id=doctor_id)))

    if current_user.role != 'patient':
        return redirect(url_for('main.home'))

    doctor = DoctorProfile.query.get_or_404(doctor_id)

    appointment_date_str = request.form.get('appointment_date')
    appointment_time_str = request.form.get('appointment_time')
    consultation_reason = request.form.get('consultation_reason', 'Consultation')
    consultation_type_id = request.form.get('consultation_type_id')
    patient_name_override = request.form.get('patient_name_override', '').strip()

    if not consultation_type_id or str(consultation_type_id).strip() == "":
        consultation_type_id = None
    else:
        try:
            consultation_type_id = int(consultation_type_id)
        except (ValueError, TypeError):
            consultation_type_id = None

    if appointment_date_str and appointment_time_str:
        try:
            appt_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        except ValueError:
            flash('Date ou heure invalide', 'error')
            return redirect(url_for('main.doctor_profile', doctor_id=doctor_id))

        notes = f"Patient: {patient_name_override}" if patient_name_override else None

        # --- DÉBUT LOGIQUE SMARTFLOW ---

        # 1. On instancie l'objet (sans le sauvegarder tout de suite)
        new_appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status='confirmed',
            is_shadow_slot=False,
            booking_type='scheduled',
            consultation_reason=consultation_reason,
            consultation_type_id=consultation_type_id,
            queue_number=None,
            doctor_notes=notes
        )

        # 2. Vérification intelligente du créneau
        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=new_appointment.appointment_date,
            appointment_time=new_appointment.appointment_time,
            status='confirmed'
        ).first()

        if existing_appointment:
            # Le créneau est pris : on lance l'analyse SmartFlow
            patient_score = current_user.reliability_score if current_user.reliability_score is not None else 100

            # Est-ce qu'il y a déjà un "Ticket Shadow" (surbooking) sur ce créneau ?
            has_shadow = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=new_appointment.appointment_date,
                appointment_time=new_appointment.appointment_time,
                is_shadow_slot=True
            ).first() is not None

            # ALGO : Si patient "à risque" (<50) ET qu'il n'y a pas encore d'overbooking
            if patient_score < 50 and not has_shadow:
                new_appointment.is_shadow_slot = True
                db.session.add(new_appointment)
                db.session.commit()
                flash('Réservation confirmée (Priorité SmartFlow)', 'info')
                return redirect(url_for('main.my_appointments'))
            else:
                # Sinon, c'est un vrai blocage
                flash('Ce créneau n\'est plus disponible.', 'danger')
                return redirect(url_for('main.doctor_profile', doctor_id=doctor_id))
        else:
            # 3. Créneau libre : réservation standard
            db.session.add(new_appointment)
            db.session.commit()
            flash('Rendez-vous confirmé.', 'success')
            return redirect(url_for('main.my_appointments'))

        # --- FIN LOGIQUE SMARTFLOW ---
    else:
        today_count = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=date.today()
        ).count()

        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            status='confirmed',
            appointment_date=date.today(),
            booking_type='walk_in',
            queue_number=today_count + 1
        )
        db.session.add(appointment)
        db.session.commit()

    flash(get_t()['appointment_booked'], 'success')
    return redirect(url_for('main.my_appointments'))

@main_bp.route('/my-appointments')
@login_required
def my_appointments():
    if current_user.role != 'patient':
        return redirect(url_for('main.doctor_dashboard'))

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(Appointment.created_at.desc()).all()

    return render_template('my_appointments.html', 
                           appointments=appointments,
                           today=date.today(),
                           t=get_t(), 
                           lang=session.get('lang', 'fr'))

@main_bp.route('/patient/profile', methods=['GET', 'POST'])
@main_bp.route('/patient/profile/<section>', methods=['GET', 'POST'])
@login_required
def patient_profile(section='info'):
    if current_user.role != 'patient':
        return redirect(url_for('main.doctor_dashboard'))

    health_record = current_user.health_record
    if not health_record:
        health_record = HealthRecord(patient_id=current_user.id)
        db.session.add(health_record)
        db.session.commit()

    if request.method == 'POST':
        if section == 'info':
            current_user.name = request.form.get('name', current_user.name)
            current_user.phone = request.form.get('phone', current_user.phone)
            current_user.gender = request.form.get('gender', current_user.gender)
            current_user.address = request.form.get('address', current_user.address)
            current_user.city = request.form.get('city', current_user.city)
            birth_date_str = request.form.get('birth_date')
            if birth_date_str:
                try:
                    current_user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            db.session.commit()
            flash('Informations mises à jour', 'success')
        elif section == 'health':
            # Patient peut UNIQUEMENT modifier: poids, taille, contact urgence
            weight = request.form.get('weight')
            height = request.form.get('height')
            emergency_contact = request.form.get('emergency_contact')
            
            if weight:
                health_record.weight = float(weight)
            if height:
                health_record.height = float(height)
            health_record.emergency_contact = emergency_contact
            health_record.updated_by = 'patient'
            
            db.session.commit()
            flash('Constantes mises à jour', 'success')
        elif section == 'security':
            new_password = request.form.get('new_password')
            if new_password:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Mot de passe mis à jour', 'success')

        return redirect(url_for('main.patient_profile', section=section))

    return render_template('patient_profile.html',
                           section=section,
                           health_record=health_record,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/patient/health-record')
@login_required
def patient_health_record():
    """Page Carnet de Santé du Patient."""
    if current_user.role != 'patient':
        return redirect(url_for('main.home'))
    
    health_record = current_user.health_record
    if not health_record:
        health_record = HealthRecord(patient_id=current_user.id)
        db.session.add(health_record)
        db.session.commit()
    
    return render_template('patient_health_record.html',
                           health_record=health_record,
                           today=date.today(),
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/api/patient/health-record', methods=['POST'])
@login_required
def api_patient_health_record():
    """API pour que le patient mette à jour SES propres données (limitées)."""
    if current_user.role != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        health_record = current_user.health_record
        if not health_record:
            health_record = HealthRecord(patient_id=current_user.id)
            db.session.add(health_record)
        
        data = request.get_json()
        
        # Patient peut UNIQUEMENT modifier ces champs
        if 'weight' in data and data['weight']:
            health_record.weight = float(data['weight'])
        if 'height' in data and data['height']:
            health_record.height = float(data['height'])
        if 'emergency_contact' in data:
            health_record.emergency_contact = data['emergency_contact']
        
        health_record.updated_by = 'patient'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Données mises à jour'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating patient health record: {str(e)}")
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500


@main_bp.route('/patient/relatives/add', methods=['POST'])
@login_required
def add_relative():
    if current_user.role != 'patient':
        return redirect(url_for('main.home'))

    name = request.form.get('name')
    relation = request.form.get('relation')
    birth_date_str = request.form.get('birth_date')
    blood_type = request.form.get('blood_type')
    allergies = request.form.get('allergies')

    birth_date = None
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except:
            pass

    relative = Relative(
        patient_id=current_user.id,
        name=name,
        relation=relation,
        birth_date=birth_date,
        blood_type=blood_type,
        allergies=allergies
    )

    db.session.add(relative)
    db.session.commit()

    flash(f"Profil de {name} ajouté avec succès", "success")
    return redirect(url_for('main.patient_profile', section='relatives'))

@main_bp.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    try:
        current_app.logger.info(f"Dashboard access by Doctor {current_user.id}")
        doctor_profile = current_user.doctor_profile

        waiting_count = Appointment.query.filter(
            Appointment.doctor_id == doctor_profile.id,
            Appointment.appointment_date == date.today(),
            Appointment.queue_number.isnot(None),
            Appointment.status.in_(['confirmed', 'waiting'])
        ).count()
        
        # Calcul recette du jour
        today_revenue = db.session.query(db.func.sum(Appointment.price_paid)).filter(
            Appointment.doctor_id == doctor_profile.id,
            Appointment.appointment_date == date.today(),
            Appointment.status == 'completed',
            Appointment.price_paid.isnot(None)
        ).scalar() or 0

        return render_template('doctor_dashboard.html',
                            doctor_profile=doctor_profile,
                            waiting_count=waiting_count,
                            today_revenue=today_revenue,
                            t=get_t(),
                            lang=session.get('lang', 'fr'))
    except Exception as e:
        current_app.logger.error(f"Error accessing doctor dashboard for user {current_user.id}: {str(e)}", exc_info=True)
        flash("Une erreur est survenue lors du chargement du tableau de bord.", "error")
        return redirect(url_for('main.home'))


# ============================================================
# SECRÉTARIAT / ASSISTANTE
# ============================================================

@main_bp.route('/secretary/dashboard')
@login_required
def secretary_dashboard():
    """Dashboard simplifié pour la secrétaire."""
    if current_user.role != 'secretary':
        return redirect(url_for('main.home'))
    
    doctor = current_user.linked_doctor
    if not doctor:
        flash("Votre compte n'est pas lié à un médecin.", "error")
        return redirect(url_for('main.home'))
    
    return render_template('secretary_dashboard.html',
                           doctor=doctor,
                           today=date.today(),
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/api/secretary/appointments')
@login_required
def api_secretary_appointments():
    """API pour récupérer les RDV du jour pour la secrétaire."""
    if current_user.role != 'secretary':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = current_user.linked_doctor
    if not doctor:
        return jsonify({'error': 'No linked doctor'}), 400
    
    target_date = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == target_date
    ).order_by(Appointment.appointment_time).all()
    
    # Stats
    stats = {
        'waiting': sum(1 for a in appointments if a.status in ['confirmed', 'waiting']),
        'checked_in': sum(1 for a in appointments if a.status == 'checked_in'),
        'completed': sum(1 for a in appointments if a.status == 'completed'),
        'total': len(appointments)
    }
    
    # Waiting room
    waiting_room = []
    for a in appointments:
        if a.status == 'checked_in' and a.check_in_time:
            wait_mins = int((datetime.now() - a.check_in_time).total_seconds() / 60)
            waiting_room.append({
                'id': a.id,
                'name': a.patient.name if a.patient else 'Patient',
                'arrival_time': a.check_in_time.strftime('%H:%M'),
                'wait_time': wait_mins
            })
    
    return jsonify({
        'appointments': [{
            'id': a.id,
            'patient_name': a.patient.name if a.patient else 'Patient',
            'time': a.appointment_time.strftime('%H:%M') if a.appointment_time else '--:--',
            'status': a.status,
            'reason': a.consultation_reason
        } for a in appointments],
        'waiting_room': waiting_room,
        'stats': stats
    })


@main_bp.route('/api/secretary/checkin/<int:appointment_id>', methods=['POST'])
@login_required
def api_secretary_checkin(appointment_id):
    """Check-in d'un patient par la secrétaire."""
    if current_user.role != 'secretary':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = current_user.linked_doctor
    if not doctor:
        return jsonify({'error': 'No linked doctor'}), 400
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    appointment.status = 'checked_in'
    appointment.check_in_time = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Patient enregistré'})


@main_bp.route('/api/secretary/quick-appointment', methods=['POST'])
@login_required
def api_secretary_quick_appointment():
    """Création rapide d'un RDV par la secrétaire (appel téléphonique)."""
    if current_user.role != 'secretary':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = current_user.linked_doctor
    if not doctor:
        return jsonify({'error': 'No linked doctor'}), 400
    
    data = request.get_json()
    patient_name = data.get('patient_name', '').strip()
    phone = data.get('phone', '').strip()
    appt_date = data.get('date')
    appt_time = data.get('time')
    reason = data.get('reason', 'Consultation')
    
    if not patient_name or not phone:
        return jsonify({'error': 'Nom et téléphone requis'}), 400
    
    # Cherche ou crée le patient
    patient = User.query.filter_by(phone=phone).first()
    if not patient:
        patient = User(
            email=f"{phone}@tbib.temp",
            name=patient_name,
            phone=phone,
            role='patient'
        )
        patient.set_password(phone)  # Mot de passe temporaire
        db.session.add(patient)
        db.session.flush()
    
    # Parse date/time
    try:
        appt_date = datetime.strptime(appt_date, '%Y-%m-%d').date() if appt_date else date.today()
        appt_time = datetime.strptime(appt_time, '%H:%M').time() if appt_time else None
    except ValueError:
        appt_date = date.today()
        appt_time = None
    
    # Crée le RDV
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=appt_date,
        appointment_time=appt_time,
        consultation_reason=reason,
        status='confirmed'
    )
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({'success': True, 'appointment_id': appointment.id})



@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    wait_time = calculate_wait_time(doctor_profile.id)

    return render_template('doctor_dashboard.html',
                           doctor=doctor_profile,
                           wait_time=wait_time,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))

@main_bp.route('/ticket/<int:patient_id>')
def patient_ticket(patient_id):
    # Simulation: find the doctor for this patient today
    # We look for a confirmed or waiting appointment for today
    appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        appointment_date=date.today()
    ).first()

    wait_time = "--"
    if appointment:
        wait_time = calculate_wait_time(appointment.doctor_id)

    return render_template('patient_ticket.html',
                           wait_time=wait_time,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))

@main_bp.route('/doctor/next-patient', methods=['POST'])
@login_required
def next_patient():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        doctor_profile = current_user.doctor_profile

        # 1. Terminer le patient précédent (si applicable)
        if doctor_profile.waiting_room_count > 0:
            previous_appointment = Appointment.query.filter_by(
                doctor_id=doctor_profile.id,
                appointment_date=date.today(),
                queue_number=doctor_profile.waiting_room_count
            ).first()

            if previous_appointment and previous_appointment.status == 'waiting':
                previous_appointment.status = 'completed'
                current_app.logger.info(f"Doctor {current_user.id} auto-completed appointment {previous_appointment.id}")

        # 2. Passer au suivant
        doctor_profile.waiting_room_count += 1
        new_count = doctor_profile.waiting_room_count

        # 3. Récupérer le nouveau patient
        next_appointment = Appointment.query.filter_by(
            doctor_id=doctor_profile.id,
            appointment_date=date.today(),
            queue_number=new_count
        ).first()

        next_patient_data = None
        if next_appointment:
            next_patient_data = {
                'id': next_appointment.id,
                'patient_name': next_appointment.patient.name,
                'patient_id': next_appointment.patient.id,
                'status': next_appointment.status,
                'queue_number': next_appointment.queue_number
            }
            # Optionnel: on pourrait passer le statut à 'waiting' si ce n'est pas fait,
            # mais généralement le patient check-in avant.

        db.session.commit()

        return jsonify({
            'success': True,
            'waiting_room_count': new_count,
            'next_patient': next_patient_data
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in next_patient for doctor {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@main_bp.route('/doctor/no-show/<int:appointment_id>', methods=['POST'])
@login_required
def mark_no_show(appointment_id):
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id == current_user.doctor_profile.id:
            appointment.status = 'no_show'
            db.session.commit()
            current_app.logger.info(f"Appointment {appointment_id} marked as no-show by doctor {current_user.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in mark_no_show for appointment {appointment_id}: {str(e)}", exc_info=True)
        flash("Impossible de marquer l'absence.", "error")

    return redirect(url_for('main.doctor_dashboard'))

@main_bp.route('/appointment/<int:appt_id>/present', methods=['POST'])
@login_required
def mark_patient_present(appt_id):
    """Marque le patient comme présent et met à jour son score de fiabilité."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        appointment = Appointment.query.get_or_404(appt_id)
        if appointment.doctor_id != current_user.doctor_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403

        appointment.status = 'completed'
        
        patient = appointment.patient
        if patient:
            current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
            patient.reliability_score = min(100.0, current_score + 2.0)
            patient.total_appointments = (patient.total_appointments or 0) + 1
        
        db.session.commit()
        current_app.logger.info(f"Appointment {appt_id} marked as present by doctor {current_user.id}")
        flash("Patient confirmé. Score de fiabilité augmenté (+2).", "success")
        
        return jsonify({
            'success': True,
            'message': 'Patient confirmé. Score de fiabilité augmenté.',
            'new_score': patient.reliability_score if patient else None
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking appointment {appt_id} as present: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@main_bp.route('/appointment/<int:appt_id>/noshow', methods=['POST'])
@login_required
def mark_patient_noshow(appt_id):
    """Marque le patient comme absent et met à jour son score de fiabilité."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        appointment = Appointment.query.get_or_404(appt_id)
        if appointment.doctor_id != current_user.doctor_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403

        appointment.status = 'no_show'
        
        patient = appointment.patient
        if patient:
            current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
            patient.reliability_score = max(0.0, current_score - 20.0)
            patient.no_show_count = (patient.no_show_count or 0) + 1
            patient.total_appointments = (patient.total_appointments or 0) + 1
        
        db.session.commit()
        current_app.logger.info(f"Appointment {appt_id} marked as no-show by doctor {current_user.id}")
        flash("Absence signalée. Score de fiabilité diminué (-20).", "warning")
        
        return jsonify({
            'success': True,
            'message': 'Absence signalée. Score de fiabilité diminué.',
            'new_score': patient.reliability_score if patient else None
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking appointment {appt_id} as no-show: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@main_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if current_user.role != 'patient':
        return redirect(url_for('main.home'))

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id == current_user.id:
        appointment.status = 'cancelled'
        db.session.commit()

    return redirect(url_for('main.my_appointments'))

@main_bp.route('/api/emergency/shift', methods=['POST'])
@login_required
def shift_appointments_api():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        urgency_duration = data.get('urgency_duration')

        if not urgency_duration:
            return jsonify({'error': 'Missing urgency_duration'}), 400

        try:
            urgency_duration = int(urgency_duration)
        except ValueError:
            return jsonify({'error': 'Invalid urgency_duration'}), 400

        current_app.logger.info(f"Doctor {current_user.id} shifting appointments by {urgency_duration} mins")
        shift_appointments(current_user.doctor_profile.id, urgency_duration)

        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error shifting appointments for doctor {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@main_bp.route('/api/queue_status/<int:doctor_id>')
def get_queue_status(doctor_id):
    """Retourne l'état de la file d'attente avec données SmartFlow."""
    doctor = DoctorProfile.query.get_or_404(doctor_id)

    # Comptage des patients en attente
    waiting_count = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date.today(),
        status='confirmed'
    ).count()

    checked_in_count = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date.today(),
        status='waiting'
    ).count()

    # Patient actuel
    current_patient = None
    current_appt = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date.today(),
        queue_number=doctor.waiting_room_count
    ).first()
    if current_appt:
        current_patient = current_appt.patient.name

    # === SmartFlow: Détection du Drift ===
    optimizer = QueueOptimizer()
    drift_info = optimizer.detect_drift(doctor_id)

    return jsonify({
        'current_serving': doctor.waiting_room_count,
        'waiting_count': waiting_count,
        'checked_in_count': checked_in_count,
        'current_patient': current_patient,
        # SmartFlow Drift Data
        'drift_minutes': drift_info.get('drift_minutes', 0),
        'is_behind': drift_info.get('is_behind', False),
        'compression_recommended': drift_info.get('should_compress', False),
        'compression_suggestion': drift_info.get('compression_suggestion'),
        'remaining_appointments': drift_info.get('remaining_appointments', 0)
    })

@main_bp.route('/api/check_in/<int:appointment_id>', methods=['POST'])
@login_required
def check_in_patient(appointment_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if appointment.queue_number is not None:
        return jsonify({'error': 'Patient already checked in'}), 400

    max_queue = db.session.query(db.func.max(Appointment.queue_number)).filter(
        Appointment.doctor_id == current_user.doctor_profile.id,
        Appointment.appointment_date == date.today()
    ).scalar() or 0

    appointment.queue_number = max_queue + 1
    appointment.status = 'waiting'
    db.session.commit()

    return jsonify({
        'success': True,
        'queue_number': appointment.queue_number,
        'patient_name': appointment.patient.name
    })

@main_bp.route('/api/doctors/<int:doctor_id>/slots')
def get_doctor_slots(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    start_date_str = request.args.get('start_date', date.today().isoformat())
    days = request.args.get('days', 3, type=int)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today()

    slots = {}

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()

        availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_available=True
        ).first()

        if availability:
            start_time = availability.start_time
            end_time = availability.end_time
        else:
            start_time = time(9, 0)
            end_time = time(17, 0)

        existing_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=current_date,
            status='confirmed'
        ).all()

        booked_times = set()
        for appt in existing_appointments:
            if appt.appointment_time:
                booked_times.add(appt.appointment_time.strftime('%H:%M'))

        day_slots = []
        current_time = datetime.combine(current_date, start_time)
        end_datetime = datetime.combine(current_date, end_time)

        now = datetime.now()

        while current_time < end_datetime:
            time_str = current_time.strftime('%H:%M')

            if current_date == date.today() and current_time <= now:
                current_time += timedelta(minutes=30)
                continue

            if time_str not in booked_times:
                day_slots.append(time_str)

            current_time += timedelta(minutes=30)

        slots[current_date.isoformat()] = day_slots

    return jsonify(slots)

@main_bp.route('/doctor/<int:doctor_id>')
def doctor_profile(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    return render_template('doctor_detail.html',
                           doctor=doctor,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))

@main_bp.route('/admin/seed_50_doctors')
def admin_seed_doctors():
    from seed_data import seed_50_doctors
    count = seed_50_doctors(reset=False)
    return f"<h1>{count} Doctors Created Successfully!</h1><p><a href='/'>Go to Home</a></p>"

@main_bp.route('/admin/reset_and_seed')
def admin_reset_and_seed():
    from seed_data import seed_50_doctors, seed_test_accounts
    seed_50_doctors(reset=True)
    seed_test_accounts()
    return "<h1>Database Reset & 50 Doctors Created!</h1><p><a href='/'>Go to Home</a></p>"


@main_bp.route('/api/doctor/appointments')
@login_required
def api_doctor_appointments():
    """
    Retourne les RDV d'un médecin avec les données SmartFlow.
    Inclut le priority_score calculé dynamiquement par le moteur.
    """
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    doctor_profile = current_user.doctor_profile
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    try:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date() if start_str else date.today() - timedelta(days=7)
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date() if end_str else date.today() + timedelta(days=30)
    except:
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() + timedelta(days=30)

    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date
    ).all()

    # Instancier le moteur SmartFlow pour calculer les scores de priorité
    optimizer = QueueOptimizer()

    events = []
    for appt in appointments:
        if appt.appointment_time:
            start_dt = datetime.combine(appt.appointment_date, appt.appointment_time)
            duration = appt.consultation_type.duration if appt.consultation_type else 30
            end_dt = start_dt + timedelta(minutes=duration)

            # Couleur basée sur le statut ou le type de consultation
            if appt.consultation_type and appt.consultation_type.color:
                color = appt.consultation_type.color
            elif appt.status == 'completed':
                color = '#3b82f6'
            elif appt.status == 'waiting':
                color = '#f59e0b'
            elif appt.status == 'no_show':
                color = '#9ca3af'
            elif appt.status == 'cancelled':
                color = '#ef4444'
            else:
                color = '#14b999'

            # Calcul dynamique du score de priorité SmartFlow
            try:
                priority_score = optimizer._calculate_priority_score(appt)
            except Exception:
                # Fallback si le calcul échoue (pas d'arrival_time, etc.)
                priority_score = (getattr(appt, 'urgency_level', 1) or 1) * 100

            # Calculate patient age if birth_date available
            patient_age = ''
            if hasattr(appt.patient, 'birth_date') and appt.patient.birth_date:
                from datetime import date as dt_date
                today = dt_date.today()
                birth = appt.patient.birth_date
                patient_age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

            # Get health record info if available
            health_record = getattr(appt.patient, 'health_record', None)
            blood_type = ''
            allergies = ''
            medical_history = ''
            if health_record:
                blood_type = getattr(health_record, 'blood_type', '') or ''
                allergies = getattr(health_record, 'allergies', '') or ''
                medical_history = getattr(health_record, 'medical_history', '') or ''

            events.append({
                'id': appt.id,
                'title': appt.patient.name,
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'color': color,
                'extendedProps': {
                    'patient_id': appt.patient_id,
                    'patient_name': appt.patient.name,
                    'patient_phone': appt.patient.phone or '',
                    'patient_email': appt.patient.email,
                    'patient_age': patient_age,
                    'blood_type': blood_type,
                    'allergies': allergies,
                    'medical_history': medical_history,
                    'status': appt.status,
                    'queue_number': appt.queue_number,
                    'consultation_reason': appt.consultation_reason or '',
                    'consultation_type': appt.consultation_type.name if appt.consultation_type else 'Consultation',
                    'booking_type': appt.booking_type,
                    'doctor_notes': appt.doctor_notes or '',
                    'no_show_count': appt.patient.no_show_count or 0,
                    # === SmartFlow Fields ===
                    'reliability_score': getattr(appt.patient, 'reliability_score', 100.0),
                    'is_shadow_slot': getattr(appt, 'is_shadow_slot', False),
                    'urgency_level': getattr(appt, 'urgency_level', 1),
                    'priority_score': priority_score
                }
            })

    return jsonify(events)


@main_bp.route('/api/doctor/appointments/<int:appointment_id>/status', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != current_user.doctor_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        new_status = data.get('status')
        diagnosis = data.get('diagnosis', '')

        if new_status not in ['confirmed', 'waiting', 'completed', 'no_show', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400

        old_status = appointment.status
        appointment.status = new_status

        if new_status == 'completed' and diagnosis:
            existing_notes = appointment.doctor_notes or ''
            appointment.doctor_notes = f"DIAGNOSTIC: {diagnosis}\n\n{existing_notes}".strip()

        if new_status == 'waiting' and appointment.queue_number is None:
            max_queue = db.session.query(db.func.max(Appointment.queue_number)).filter(
                Appointment.doctor_id == current_user.doctor_profile.id,
                Appointment.appointment_date == date.today()
            ).scalar() or 0
            appointment.queue_number = max_queue + 1

        if new_status == 'no_show':
            appointment.patient.no_show_count = (appointment.patient.no_show_count or 0) + 1
            if appointment.patient.no_show_count >= 3:
                appointment.patient.is_blocked = True

        db.session.commit()
        current_app.logger.info(f"Status update for appt {appointment_id}: {old_status} -> {new_status} by doctor {current_user.id}")

        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'new_status': new_status,
            'queue_number': appointment.queue_number
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating status for appointment {appointment_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@main_bp.route('/api/doctor/appointments/<int:appointment_id>/notes', methods=['POST'])
@login_required
def update_appointment_notes(appointment_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    appointment.doctor_notes = data.get('notes', '')
    db.session.commit()

    return jsonify({'success': True})


@main_bp.route('/doctor/patients')
@login_required
def doctor_patients():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    search_query = request.args.get('q', '').strip()

    patient_subquery = db.session.query(
        Appointment.patient_id,
        db.func.max(Appointment.appointment_date).label('last_visit'),
        db.func.count(Appointment.id).label('visit_count')
    ).filter(
        Appointment.doctor_id == doctor_profile.id
    ).group_by(Appointment.patient_id).subquery()

    query = db.session.query(
        User,
        patient_subquery.c.last_visit,
        patient_subquery.c.visit_count
    ).join(patient_subquery, User.id == patient_subquery.c.patient_id)

    if search_query:
        query = query.filter(User.name.ilike(f'%{search_query}%'))

    patients_data = query.order_by(patient_subquery.c.last_visit.desc()).all()

    patients = [{
        'user': p[0],
        'last_visit': p[1],
        'visit_count': p[2]
    } for p in patients_data]

    if request.headers.get('HX-Request'):
        return render_template('partials/patient_rows.html', patients=patients)

    return render_template('doctor_patients.html',
                           patients=patients,
                           search_query=search_query,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/api/doctor/patient/<int:patient_id>/history')
@login_required
def get_patient_history(patient_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    doctor_profile = current_user.doctor_profile

    # In a real app, verify relationship. For now, allow if doctor.
    # has_relationship = Appointment.query.filter(
    #     Appointment.doctor_id == doctor_profile.id,
    #     Appointment.patient_id == patient_id
    # ).first()

    # if not has_relationship:
    #     return jsonify({'error': 'Patient not found'}), 404

    patient = User.query.get_or_404(patient_id)
    health_record = patient.health_record

    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.patient_id == patient_id
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    history = [{
        'id': a.id,
        'date': a.appointment_date.strftime('%d/%m/%Y'),
        'time': a.appointment_time.strftime('%H:%M') if a.appointment_time else '--:--',
        'reason': a.consultation_reason or 'Consultation',
        'status': a.status,
        'notes': a.doctor_notes or ''
    } for a in appointments]

    age = None
    if patient.birth_date:
        today = date.today()
        age = today.year - patient.birth_date.year - ((today.month, today.day) < (patient.birth_date.month, patient.birth_date.day))

    return jsonify({
        'patient': {
            'id': patient.id,
            'name': patient.name,
            'email': patient.email,
            'phone': patient.phone or '',
            'age': age,
            'gender': patient.gender or '',
            'city': patient.city or '',
            'blood_type': health_record.blood_type if health_record else None,
            'allergies': health_record.allergies if health_record else None,
            'chronic_conditions': health_record.chronic_conditions if health_record else None
        },
        'history': history
    })


@main_bp.route('/api/doctor/patient/<int:patient_id>/health-record', methods=['POST'])
@login_required
def update_patient_health_record(patient_id):
    """API pour que le médecin mette à jour le dossier médical d'un patient."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        patient = User.query.get_or_404(patient_id)
        
        # Crée le HealthRecord si inexistant
        health_record = patient.health_record
        if not health_record:
            health_record = HealthRecord(patient_id=patient_id)
            db.session.add(health_record)
        
        data = request.get_json()
        
        # Champs modifiables par le médecin (données médicales)
        if 'blood_type' in data:
            health_record.blood_type = data['blood_type']
        if 'weight' in data and data['weight']:
            health_record.weight = float(data['weight'])
        if 'height' in data and data['height']:
            health_record.height = float(data['height'])
        if 'allergies' in data:
            health_record.allergies = data['allergies']
        if 'chronic_conditions' in data:
            health_record.chronic_conditions = data['chronic_conditions']
        if 'family_history' in data:
            health_record.family_history = data['family_history']
        if 'vaccines' in data:
            health_record.vaccines = data['vaccines']
        if 'current_treatments' in data:
            health_record.current_treatments = data['current_treatments']
        if 'prescriptions' in data:
            health_record.prescriptions = data['prescriptions']
        if 'notes' in data:
            health_record.notes = data['notes']
        
        health_record.updated_by = f'doctor:{current_user.id}'
        db.session.commit()
        current_app.logger.info(f"Doctor {current_user.id} updated health record for patient {patient_id}")
        
        return jsonify({
            'success': True,
            'message': 'Dossier médical mis à jour',
            'health_record': {
                'blood_type': health_record.blood_type,
                'weight': health_record.weight,
                'height': health_record.height,
                'allergies': health_record.allergies,
                'chronic_conditions': health_record.chronic_conditions,
                'family_history': health_record.family_history,
                'vaccines': health_record.vaccines,
                'current_treatments': health_record.current_treatments,
                'prescriptions': health_record.prescriptions
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating health record: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500


@main_bp.route('/api/doctor/appointments/<int:appointment_id>/complete', methods=['POST'])
@login_required
def complete_consultation(appointment_id):
    """Termine une consultation avec diagnostic optionnel et montant."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != current_user.doctor_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        diagnosis = data.get('diagnosis', '')
        amount = data.get('amount', '')
        payment_method = data.get('payment_method', 'Espèces')
        notes = data.get('notes', '')
        
        # Mise à jour du statut
        appointment.status = 'completed'
        
        # Enregistrer le paiement
        if amount:
            try:
                appointment.price_paid = float(amount)
            except (ValueError, TypeError):
                pass
        appointment.payment_method = payment_method
        
        # Construction des notes médicales
        medical_notes = []
        if diagnosis:
            medical_notes.append(f"DIAGNOSTIC: {diagnosis}")
        if amount:
            medical_notes.append(f"MONTANT: {amount} DA ({payment_method})")
        if notes:
            medical_notes.append(f"NOTES: {notes}")
        
        existing_notes = appointment.doctor_notes or ''
        if medical_notes:
            appointment.doctor_notes = '\n'.join(medical_notes) + '\n\n' + existing_notes
        
        # Mise à jour du score de fiabilité du patient
        patient = appointment.patient
        if patient:
            current_score = patient.reliability_score if patient.reliability_score is not None else 100.0
            patient.reliability_score = min(100.0, current_score + 2.0)
        
        db.session.commit()
        current_app.logger.info(f"Consultation {appointment_id} completed by doctor {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Consultation terminée avec succès',
            'appointment_id': appointment.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing consultation: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur lors de la finalisation'}), 500


@main_bp.route('/doctor/settings')
@login_required
def doctor_settings():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    consultation_types = ConsultationType.query.filter_by(doctor_id=doctor_profile.id, is_active=True).all()
    absences = DoctorAbsence.query.filter(
        DoctorAbsence.doctor_id == doctor_profile.id,
        DoctorAbsence.end_date >= datetime.now()
    ).order_by(DoctorAbsence.start_date).all()

    availability_slots = DoctorAvailability.query.filter_by(doctor_id=doctor_profile.id).all()
    availability = {}
    for slot in availability_slots:
        availability[slot.day_of_week] = {
            'is_available': slot.is_available,
            'start_time': slot.start_time.strftime('%H:%M') if slot.start_time else '08:00',
            'end_time': slot.end_time.strftime('%H:%M') if slot.end_time else '17:00'
        }
    
    # Charger les secrétaires liées à ce médecin
    secretaries = User.query.filter_by(role='secretary', linked_doctor_id=doctor_profile.id).all()

    return render_template('doctor_settings.html',
                           doctor=doctor_profile,
                           consultation_types=consultation_types,
                           absences=absences,
                           availability=availability,
                           secretaries=secretaries,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/doctor/settings/profile', methods=['POST'])
@login_required
def doctor_settings_profile():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor = current_user.doctor_profile

    current_user.name = request.form.get('name', current_user.name)
    doctor.specialty = request.form.get('specialty', doctor.specialty)
    doctor.city = request.form.get('city', doctor.city)
    doctor.address = request.form.get('address', '')
    doctor.bio = request.form.get('bio', '')
    doctor.profile_picture = request.form.get('profile_picture', '')
    doctor.languages = request.form.get('languages', '')
    doctor.payment_methods = request.form.get('payment_methods', '')
    doctor.expertises = request.form.get('expertises', '')
    doctor.diplomas = request.form.get('diplomas', '')

    db.session.commit()
    flash('Modifications enregistrées !', 'success')
    return redirect(url_for('main.doctor_settings'))


@main_bp.route('/doctor/settings/availability', methods=['POST'])
@login_required
def doctor_settings_availability():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_id = current_user.doctor_profile.id

    DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()

    for day in range(7):
        is_active = request.form.get(f'day_{day}_active') == '1'
        start_str = request.form.get(f'day_{day}_start', '08:00')
        end_str = request.form.get(f'day_{day}_end', '17:00')

        try:
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
        except:
            start_time = time(8, 0)
            end_time = time(17, 0)

        slot = DoctorAvailability(
            doctor_id=doctor_id,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
            is_available=is_active
        )
        db.session.add(slot)

    db.session.commit()
    flash('Horaires enregistrés !', 'success')
    return redirect(url_for('main.doctor_settings'))


@main_bp.route('/doctor/settings/consultation-type', methods=['POST'])
@login_required
def add_consultation_type():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    consultation_type = ConsultationType(
        doctor_id=current_user.doctor_profile.id,
        name=data.get('name', 'Consultation'),
        duration=int(data.get('duration', 30)),
        price=data.get('price', ''),
        color=data.get('color', '#14b999'),
        is_emergency_only=data.get('is_emergency_only', False),
        require_existing_patient=data.get('require_existing_patient', False)
    )

    db.session.add(consultation_type)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': consultation_type.id,
        'name': consultation_type.name
    })


@main_bp.route('/doctor/settings/consultation-type/<int:type_id>', methods=['DELETE'])
@login_required
def delete_consultation_type(type_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    ct = ConsultationType.query.get_or_404(type_id)
    if ct.doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403

    ct.is_active = False
    db.session.commit()

    return jsonify({'success': True})


@main_bp.route('/doctor/settings/absence', methods=['POST'])
@login_required
def add_absence():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    try:
        start_date = datetime.fromisoformat(data.get('start_date'))
        end_date = datetime.fromisoformat(data.get('end_date'))
    except:
        return jsonify({'error': 'Invalid dates'}), 400

    force = data.get('force', False)
    doctor_id = current_user.doctor_profile.id

    if not force:
        conflicts = get_conflicting_appointments(doctor_id, start_date, end_date)
        if conflicts > 0:
            return jsonify({
                'error': 'Conflict',
                'conflict_count': conflicts
            }), 409

    # Cancel appointments if they exist
    cancel_appointments_in_range(doctor_id, start_date, end_date, data.get('reason', ''))

    absence = DoctorAbsence(
        doctor_id=doctor_id,
        start_date=start_date,
        end_date=end_date,
        reason=data.get('reason', '')
    )

    db.session.add(absence)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': absence.id
    })


@main_bp.route('/doctor/settings/absence/<int:absence_id>', methods=['DELETE'])
@login_required
def delete_absence(absence_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403

    absence = DoctorAbsence.query.get_or_404(absence_id)
    if absence.doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(absence)
    db.session.commit()

    return jsonify({'success': True})


# ============================================================
# GESTION D'ÉQUIPE - SECRÉTAIRES
# ============================================================

@main_bp.route('/doctor/settings/secretary', methods=['POST'])
@login_required
def add_secretary():
    """Créer un compte secrétaire lié à ce médecin."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    can_view_medical = data.get('can_view_medical', False)
    
    if not name or not email or not password:
        return jsonify({'error': 'Tous les champs sont requis'}), 400
    
    # Vérifier si l'email existe déjà
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Cet email est déjà utilisé'}), 400
    
    secretary = User(
        email=email,
        name=name,
        role='secretary',
        linked_doctor_id=current_user.doctor_profile.id,
        can_view_medical_records=can_view_medical
    )
    secretary.set_password(password)
    
    db.session.add(secretary)
    db.session.commit()
    
    current_app.logger.info(f"Secretary {secretary.id} created by doctor {current_user.id}")
    return jsonify({'success': True, 'id': secretary.id})


@main_bp.route('/doctor/settings/secretary/<int:secretary_id>', methods=['DELETE'])
@login_required
def delete_secretary(secretary_id):
    """Supprimer un compte secrétaire."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    secretary = User.query.get_or_404(secretary_id)
    if secretary.linked_doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(secretary)
    db.session.commit()
    
    return jsonify({'success': True})


@main_bp.route('/doctor/settings/secretary/<int:secretary_id>/delegation', methods=['POST'])
@login_required
def toggle_secretary_delegation(secretary_id):
    """Activer/désactiver l'accès aux dossiers médicaux pour une secrétaire."""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    secretary = User.query.get_or_404(secretary_id)
    if secretary.linked_doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    secretary.can_view_medical_records = data.get('can_view_medical_records', False)
    db.session.commit()
    
    return jsonify({'success': True})

@main_bp.route('/api/doctors/<int:doctor_id>/consultation-types')
def get_consultation_types(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    types = ConsultationType.query.filter_by(doctor_id=doctor_id, is_active=True).all()

    if not types:
        return jsonify([{
            'id': None,
            'name': 'Consultation',
            'duration': 30,
            'price': '',
            'color': '#14b999',
            'is_emergency_only': False,
            'require_existing_patient': False
        }])

    return jsonify([{
        'id': ct.id,
        'name': ct.name,
        'duration': ct.duration,
        'price': ct.price,
        'color': ct.color,
        'is_emergency_only': ct.is_emergency_only,
        'require_existing_patient': ct.require_existing_patient
    } for ct in types])


@main_bp.route('/api/doctors/<int:doctor_id>/smart-slots')
def get_smart_slots(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    start_date_str = request.args.get('start_date', date.today().isoformat())
    days = request.args.get('days', 3, type=int)
    consultation_type_id = request.args.get('type_id', type=int)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today()

    duration = 30
    is_emergency_only = False
    require_existing_patient = False

    if consultation_type_id:
        ct = ConsultationType.query.get(consultation_type_id)
        if ct and ct.doctor_id == doctor_id:
            duration = ct.duration
            is_emergency_only = ct.is_emergency_only
            require_existing_patient = ct.require_existing_patient

    if is_emergency_only:
        max_date = date.today() + timedelta(days=1)
        if start_date > max_date:
            return jsonify({'error': 'Emergency slots only available for next 24h', 'slots': {}})

    if require_existing_patient and current_user.is_authenticated:
        past_appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.doctor_id == doctor_id,
            Appointment.status == 'completed'
        ).count()
        if past_appointments == 0:
            return jsonify({'error': 'This consultation type requires existing patients', 'slots': {}})

    if current_user.is_authenticated and (current_user.no_show_count or 0) >= 3:
        return jsonify({'error': 'Your account is blocked due to repeated no-shows', 'slots': {}})

    absences = DoctorAbsence.query.filter(
        DoctorAbsence.doctor_id == doctor_id,
        DoctorAbsence.end_date >= datetime.combine(start_date, time(0, 0))
    ).all()

    slots = {}

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()

        is_absent = False
        for absence in absences:
            if absence.start_date.date() <= current_date <= absence.end_date.date():
                is_absent = True
                break

        if is_absent:
            slots[current_date.isoformat()] = []
            continue

        availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_available=True
        ).first()

        if availability:
            slot_start_time = availability.start_time
            slot_end_time = availability.end_time
        else:
            slot_start_time = time(9, 0)
            slot_end_time = time(17, 0)

        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == current_date,
            Appointment.status.in_(['confirmed', 'waiting'])
        ).all()

        booked_ranges = []
        for appt in existing_appointments:
            if appt.appointment_time:
                appt_duration = appt.consultation_type.duration if appt.consultation_type else 30
                appt_start = datetime.combine(current_date, appt.appointment_time)
                appt_end = appt_start + timedelta(minutes=appt_duration)
                booked_ranges.append((appt_start, appt_end))

        day_slots = []
        current_time = datetime.combine(current_date, slot_start_time)
        end_datetime = datetime.combine(current_date, slot_end_time)

        now = datetime.now()

        while current_time + timedelta(minutes=duration) <= end_datetime:
            slot_end = current_time + timedelta(minutes=duration)

            if current_date == date.today() and current_time <= now:
                current_time += timedelta(minutes=15)
                continue

            conflict = False
            for booked_start, booked_end in booked_ranges:
                if not (slot_end <= booked_start or current_time >= booked_end):
                    conflict = True
                    break

            if not conflict:
                day_slots.append(current_time.strftime('%H:%M'))

            current_time += timedelta(minutes=15)

        slots[current_date.isoformat()] = day_slots

    return jsonify({'slots': slots})


@main_bp.route('/admin/initialize_db')
def initialize_database():
    secret_key = request.args.get('key')
    if secret_key != 'tbib_secret_key':
        return "Unauthorized", 403

    existing_doctor = DoctorProfile.query.first()
    if existing_doctor:
        return "Database already has data. No action taken."

    import random

    cities = ["Alger", "Oran", "Constantine", "Annaba", "Setif", "Bejaia", "Tlemcen", "Blida"]
    specialties = ["Médecin Généraliste", "Dentiste", "Cardiologue", "Pédiatre", "Dermatologue", "Gynécologue", "Ophtalmologue"]
    first_names = ["Mohamed", "Amine", "Sarah", "Fatima", "Youssef", "Karim", "Nadia", "Amina", "Rachid", "Leila"]
    last_names = ["Benali", "Saidi", "Dahmani", "Boudiaf", "Hadj", "Mebarki", "Hamidi", "Cherif", "Bouzid", "Belkacem"]

    doctors_created = 0

    for i in range(50):
        first = random.choice(first_names)
        last = random.choice(last_names)
        full_name = f"Dr. {first} {last}"
        city = random.choice(cities)
        specialty = random.choice(specialties)

        email = f"doctor{i+1}@tbib.dz"

        user = User(
            email=email,
            role='doctor',
            name=full_name,
            phone=f"05{random.randint(10000000, 99999999)}",
            city=city
        )
        user.set_password('doctor123')
        db.session.add(user)
        db.session.flush()

        street_names = ['Didouche Mourad', 'Ben Mhidi', 'Abane Ramdane', 'Amirouche', 'Pasteur']
        doctor_profile = DoctorProfile(
            user_id=user.id,
            specialty=specialty,
            city=city,
            address=f"{random.randint(1, 200)} Rue {random.choice(street_names)}",
            bio=f"Médecin spécialiste en {specialty.lower()} avec plusieurs années d'expérience.",
            waiting_room_count=0,
            languages="Français, Arabe",
            payment_methods="Espèces, Carte bancaire"
        )
        db.session.add(doctor_profile)
        db.session.flush()

        start_t = time(9, 0)
        end_t = time(17, 0)
        for day in range(5):
            availability = DoctorAvailability(
                doctor_id=doctor_profile.id,
                day_of_week=day,
                start_time=start_t,
                end_time=end_t,
                is_available=True
            )
            db.session.add(availability)

        default_consultation = ConsultationType(
            doctor_id=doctor_profile.id,
            name="Consultation standard",
            duration=30,
            price="2000 DA",
            color="#14b999",
            is_active=True
        )
        db.session.add(default_consultation)

        doctors_created += 1

    db.session.commit()

    return f"✅ SUCCESS: {doctors_created} Doctors & Schedules Created!"


@main_bp.route('/admin/seed_lite')
def seed_lite():
    import random

    doctor_count = DoctorProfile.query.count()
    if doctor_count > 5:
        return "⚠️ Database already has data. Aborted."

    cities = ["Alger", "Oran", "Constantine", "Setif", "Bejaia"]
    specialties = ["Médecin Généraliste", "Dentiste", "Pédiatre"]
    names = [
        ("Mohamed", "Benali"), ("Sarah", "Saidi"), ("Amine", "Dahmani"),
        ("Fatima", "Boudiaf"), ("Karim", "Hadj"), ("Yasmine", "Mebarki"),
        ("Omar", "Hamidi"), ("Leila", "Cherif"), ("Youcef", "Bouzid"), ("Amina", "Belkacem")
    ]

    for i, (first, last) in enumerate(names):
        user = User(
            email=f"medecin{i+1}@tbib.dz",
            role='doctor',
            name=f"Dr. {first} {last}",
            phone=f"05{random.randint(10000000, 99999999)}",
            city=cities[i % len(cities)]
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.flush()

        profile = DoctorProfile(
            user_id=user.id,
            specialty=specialties[i % len(specialties)],
            city=cities[i % len(cities)],
            address=f"{random.randint(1, 100)} Rue Centrale",
            bio=f"Médecin expérimenté à {cities[i % len(cities)]}.",
            waiting_room_count=0
        )
        db.session.add(profile)
        db.session.flush()

        for day in range(5):
            avail = DoctorAvailability(
                doctor_id=profile.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(16, 0),
                is_available=True
            )
            db.session.add(avail)

        consult = ConsultationType(
            doctor_id=profile.id,
            name="Consultation",
            duration=30,
            price="2000 DA",
            color="#14b999",
            is_active=True
        )
        db.session.add(consult)

    db.session.commit()
    return "✅ SUCCÈS : 10 Médecins ajoutés à la Production !"


@main_bp.route('/demo/force_login')
def demo_force_login():
    user = User.query.filter_by(email='medecin1@tbib.dz').first()

    if not user:
        user = User.query.filter_by(role='doctor').first()

    if user:
        login_user(user)
        flash("🔓 Mode Démo : Connexion Médecin forcée avec succès.", "success")
        return redirect(url_for('main.doctor_dashboard'))

    return "Erreur: Aucun médecin en base."


@main_bp.route('/admin/ministry')
def ministry_dashboard():
    # 1. Calcul des Chiffres Clés
    total_doctors = DoctorProfile.query.count()
    total_cities = db.session.query(DoctorProfile.city).distinct().count()

    # 2. Données pour l'équité (Carte/Liste)
    doctors_per_city = db.session.query(
        DoctorProfile.city,
        db.func.count(DoctorProfile.id).label('count')
    ).group_by(DoctorProfile.city).order_by(db.func.count(DoctorProfile.id).desc()).all()

    underserved_cities = [city for city, count in doctors_per_city if count < 2]

    # 3. Données de Veille Sanitaire (Anonymisées)
    health_trends = {
        'Grippe saisonnière': '+12%',
        'Diabète Type 2': 'Stable',
        'Hypertension': '+5%',
        'Allergies': '-3%',
        'Consultations préventives': '+8%'
    }

    # 4. Génération du Rapport Texte
    if underserved_cities:
        alert_msg = f"ALERTE: {len(underserved_cities)} ville(s) sous-couvertes médicalement."
    else:
        alert_msg = "Couverture médicale satisfaisante sur l'ensemble du territoire."

    report = f"RAPPORT SANTÉ PUBLIQUE: {total_doctors} médecins actifs couvrant {total_cities} villes. {alert_msg}"

    # 5. Rendu de la page (AVEC les traductions 't' et 'lang')
    return render_template('admin/ministry.html',
                           total_doctors=total_doctors,
                           total_cities=total_cities,
                           doctors_per_city=doctors_per_city,
                           underserved_cities=underserved_cities,
                           health_trends=health_trends,
                           report=report,
                           t=get_t(),
                           lang=session.get('lang', 'fr')
                           )


@main_bp.route('/doctor/agenda')
@login_required
def doctor_agenda():
    """Full calendar view for doctors."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    return render_template('doctor_agenda.html',
                           doctor_profile=doctor_profile,
                           doctor=doctor_profile,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/doctor/public-profile')
@login_required
def doctor_public_profile():
    """Shows what the public sees for this doctor."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    consultation_types = ConsultationType.query.filter_by(doctor_id=doctor_profile.id, is_active=True).all()

    return render_template('doctor_public_view.html',
                           doctor=doctor_profile,
                           doctor_profile=doctor_profile,
                           consultation_types=consultation_types,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))


@main_bp.route('/doctor/walkin', methods=['POST'])
@login_required
def add_walkin():
    """Add a walk-in or emergency patient."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    import uuid
    import secrets
    from werkzeug.security import generate_password_hash
    from sqlalchemy.exc import IntegrityError

    max_retries = 3
    for retry in range(max_retries):
        try:
            doctor_profile = current_user.doctor_profile
            patient_name = request.form.get('patient_name', 'Walk-in Patient')
            phone = request.form.get('phone', '')
            urgency_level = int(request.form.get('urgency_level', 1))

            existing_patient = User.query.filter_by(phone=phone).first() if phone else None

            if not existing_patient:
                temp_email = f"walkin_{uuid.uuid4().hex}@temp.tbib.dz"
                secure_random_password = secrets.token_urlsafe(32)
                existing_patient = User(
                    name=patient_name,
                    email=temp_email,
                    phone=phone if phone else None,
                    role='patient',
                    password_hash=generate_password_hash(secure_random_password),
                    reliability_score=100.0
                )
                db.session.add(existing_patient)
                db.session.flush()

            queue_number = Appointment.query.filter_by(
                doctor_id=doctor_profile.id,
                appointment_date=date.today()
            ).count() + 1

            appointment = Appointment(
                patient_id=existing_patient.id,
                doctor_id=doctor_profile.id,
                appointment_date=date.today(),
                appointment_time=datetime.now().time(),
                status='waiting',
                queue_number=queue_number,
                urgency_level=urgency_level,
                consultation_reason='Walk-in / Urgence'
            )
            db.session.add(appointment)
            db.session.commit()

            flash(f"Patient {patient_name} ajouté en urgence (Ticket #{queue_number}).", "success")
            break

        except IntegrityError:
            db.session.rollback()
            if retry == max_retries - 1:
                current_app.logger.error("Failed to create walk-in patient after retries")
                flash("Erreur lors de l'ajout du patient. Veuillez réessayer.", "error")
            continue
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding walk-in: {str(e)}", exc_info=True)
            flash("Erreur lors de l'ajout du patient.", "error")
            break

    return redirect(url_for('main.doctor_dashboard'))
from itsdangerous import URLSafeSerializer

def get_serializer(secret_key=None):
    if secret_key is None:
        secret_key = current_app.secret_key
    return URLSafeSerializer(secret_key)

@main_bp.route('/patient/live/<token>')
def patient_live_ticket(token):
    s = get_serializer()
    try:
        appointment_id = s.loads(token)
    except:
        return render_template('404.html', t=get_t(), lang=session.get('lang', 'fr'))

    appointment = Appointment.query.get_or_404(appointment_id)
    today = date.today()

    query = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == today,
        Appointment.status == 'waiting'
    )

    if appointment.queue_number:
        query = query.filter(Appointment.queue_number < appointment.queue_number)

    waiting_ahead = query.count()
    estimated_wait = waiting_ahead * 15

    return render_template('live_ticket.html',
                           appointment=appointment,
                           waiting_ahead=waiting_ahead,
                           estimated_wait=estimated_wait,
                           t=get_t(),
                           token=token,
                           lang=session.get('lang', 'fr'))

@main_bp.route('/patient/live/status/<token>')
def patient_live_status(token):
    s = get_serializer()
    try:
        appointment_id = s.loads(token)
    except:
        return jsonify({'error': 'Invalid token'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)
    today = date.today()

    query = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == today,
        Appointment.status == 'waiting'
    )

    if appointment.queue_number:
        query = query.filter(Appointment.queue_number < appointment.queue_number)

    waiting_ahead = query.count()
    estimated_wait = waiting_ahead * 15

    return jsonify({
        'success': True,
        'status': appointment.status,
        'waiting_ahead': waiting_ahead,
        'estimated_wait': estimated_wait,
        'queue_number': appointment.queue_number,
        'patient_name': appointment.patient.name if appointment.patient else ""
    })

@main_bp.route('/patient/live/confirm/<token>', methods=['POST'])
def patient_live_confirm(token):
    s = get_serializer()
    try:
        appointment_id = s.loads(token)
    except:
        return jsonify({'error': 'Invalid token'}), 403

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.status == 'waiting' and appointment.queue_number:
         return jsonify({'success': True, 'message': 'Already checked in'})

    max_queue = db.session.query(db.func.max(Appointment.queue_number)).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == date.today()
    ).scalar() or 0

    appointment.queue_number = max_queue + 1
    appointment.status = 'waiting'
    try:
        appointment.check_in_time = datetime.now()
    except:
        pass

    db.session.commit()
    return jsonify({'success': True})
