from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, DoctorProfile, Appointment, HealthRecord, DoctorAvailability, ConsultationType, DoctorAbsence, Relative
from utils.engine import calculate_wait_time, shift_appointments
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
        print("⚠️ DATABASE EMPTY. INITIALIZING DEMO DATA...")
        initialize_demo_data()
        return redirect(url_for('main.home'))
    
    specialty = request.args.get('specialty', '')
    city = request.args.get('city', '')
    
    search_mode = bool(specialty or city)
    doctors = []
    
    if search_mode:
        query = DoctorProfile.query.join(User)
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

@main_bp.route('/set-language/<lang>')
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
        
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            status='confirmed',
            appointment_date=appt_date,
            appointment_time=appt_time,
            booking_type='scheduled',
            consultation_reason=consultation_reason,
            consultation_type_id=consultation_type_id,
            queue_number=None,
            doctor_notes=notes
        )
        
        try:
            db.session.add(appointment)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Ce créneau n\'est plus disponible', 'error')
            return redirect(url_for('main.doctor_profile', doctor_id=doctor_id))
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
            health_record.blood_type = request.form.get('blood_type')
            health_record.weight = request.form.get('weight', type=float)
            health_record.height = request.form.get('height', type=float)
            health_record.allergies = request.form.get('allergies')
            health_record.vaccines = request.form.get('vaccines')
            health_record.chronic_conditions = request.form.get('chronic_conditions')
            db.session.commit()
            flash('Carnet de santé mis à jour', 'success')
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
    
    doctor_profile = current_user.doctor_profile
    
    waiting_count = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == date.today(),
        Appointment.queue_number.isnot(None),
        Appointment.status.in_(['confirmed', 'waiting'])
    ).count()
    
    return render_template('doctor_cockpit.html',
                           doctor_profile=doctor_profile,
                           waiting_count=waiting_count,
                           t=get_t(),
                           lang=session.get('lang', 'fr'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))

    doctor_profile = current_user.doctor_profile
    wait_time = calculate_wait_time(doctor_profile.id)

    # Fetch appointments for the dashboard list
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == date.today()
    ).all()

    # Custom sort
    # We want 'in_progress' first.
    # Then 'waiting'/'confirmed'.
    # Then 'completed'/'no_show' at the bottom.

    def status_rank(appt):
        if appt.status == 'in_progress': return 0
        if appt.status in ['waiting', 'confirmed']: return 1
        return 2

    appointments.sort(key=lambda x: (status_rank(x), x.queue_number or 9999, x.appointment_time or time(23, 59)))

    return render_template('doctor_dashboard.html',
                           doctor=doctor_profile,
                           wait_time=wait_time,
                           appointments=appointments,
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

@main_bp.route('/api/doctor/next_patient', methods=['POST'])
@login_required
def next_patient_api():
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor_profile = current_user.doctor_profile
    today = date.today()
    
    # 1. Mark current IN_PROGRESS as COMPLETED
    current_in_progress = Appointment.query.filter_by(
        doctor_id=doctor_profile.id,
        appointment_date=today,
        status='in_progress'
    ).first()

    if current_in_progress:
        current_in_progress.status = 'completed'

    # 2. Find next WAITING or CONFIRMED appointment
    # Priority: Queue Number (if exists), then Time
    next_appt = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == today,
        Appointment.status.in_(['waiting', 'confirmed'])
    ).order_by(
        Appointment.queue_number.asc().nulls_last(),
        Appointment.appointment_time.asc()
    ).first()
    
    if next_appt:
        next_appt.status = 'in_progress'

        # Ensure it has a queue number if it didn't have one
        if next_appt.queue_number is None:
             max_queue = db.session.query(db.func.max(Appointment.queue_number)).filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.appointment_date == today
            ).scalar() or 0
             next_appt.queue_number = max_queue + 1

        doctor_profile.waiting_room_count = next_appt.queue_number
    
    db.session.commit()

    return jsonify({
        'success': True,
        'completed_id': current_in_progress.id if current_in_progress else None,
        'next_patient': {
            'id': next_appt.id,
            'name': next_appt.patient.name,
            'queue_number': next_appt.queue_number
        } if next_appt else None
    })

@main_bp.route('/doctor/no-show/<int:appointment_id>', methods=['POST'])
@login_required
def mark_no_show(appointment_id):
    if current_user.role != 'doctor':
        return redirect(url_for('main.home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id == current_user.doctor_profile.id:
        appointment.status = 'no_show'
        db.session.commit()
    
    return redirect(url_for('main.doctor_dashboard'))

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

    data = request.get_json()
    urgency_duration = data.get('urgency_duration')

    if not urgency_duration:
        return jsonify({'error': 'Missing urgency_duration'}), 400

    try:
        urgency_duration = int(urgency_duration)
    except ValueError:
         return jsonify({'error': 'Invalid urgency_duration'}), 400

    shift_appointments(current_user.doctor_profile.id, urgency_duration)

    return jsonify({'success': True})

@main_bp.route('/api/queue_status/<int:doctor_id>')
def get_queue_status(doctor_id):
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    waiting_count = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date.today(),
        status='confirmed'
    ).count()
    
    current_patient = None
    current_appt = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date.today(),
        queue_number=doctor.waiting_room_count
    ).first()
    if current_appt:
        current_patient = current_appt.patient.name
    
    return jsonify({
        'current_serving': doctor.waiting_room_count,
        'waiting_count': waiting_count,
        'current_patient': current_patient
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
    
    events = []
    for appt in appointments:
        if appt.appointment_time:
            start_dt = datetime.combine(appt.appointment_date, appt.appointment_time)
            duration = appt.consultation_type.duration if appt.consultation_type else 30
            end_dt = start_dt + timedelta(minutes=duration)
            
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
                    'status': appt.status,
                    'queue_number': appt.queue_number,
                    'consultation_reason': appt.consultation_reason or '',
                    'consultation_type': appt.consultation_type.name if appt.consultation_type else 'Consultation',
                    'booking_type': appt.booking_type,
                    'doctor_notes': appt.doctor_notes or '',
                    'no_show_count': appt.patient.no_show_count or 0
                }
            })
    
    return jsonify(events)


@main_bp.route('/api/doctor/appointments/<int:appointment_id>/status', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    if current_user.role != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.doctor_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    diagnosis = data.get('diagnosis', '')
    
    if new_status not in ['confirmed', 'waiting', 'in_progress', 'completed', 'no_show', 'cancelled']:
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
    
    return jsonify({
        'success': True,
        'appointment_id': appointment.id,
        'new_status': new_status,
        'queue_number': appointment.queue_number
    })


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
    
    has_relationship = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.patient_id == patient_id
    ).first()
    
    if not has_relationship:
        return jsonify({'error': 'Patient not found'}), 404
    
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
    
    return render_template('doctor_settings.html',
                           doctor=doctor_profile,
                           consultation_types=consultation_types,
                           absences=absences,
                           availability=availability,
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
    
    absence = DoctorAbsence(
        doctor_id=current_user.doctor_profile.id,
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
                           t=get_t(),                      # <--- C'est ça qui manquait !
                           lang=session.get('lang', 'fr')  # <--- Et ça !
                           )