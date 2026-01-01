# TBIB - CONSTITUTION TECHNIQUE & FONCTIONNELLE

## 1. IDENTITÉ VISUELLE (STRICTE)
* **Couleur Primaire (Action, Branding) :** `#3cc7a7` (Vert Menthe).
    * *Usage :* Boutons principaux, barres de progression, headers actifs, icônes de validation.
* **Couleur Secondaire (Fond) :** `#FFFFFF` (Blanc Pur) ou `#F8F9FA` (Gris très clair pour les zones de contenu).
* **Couleur Texte :** `#333333` (Gris Foncé pour la lisibilité).
* **Interdiction :** Ne jamais utiliser de violet, de beige ou de couleurs par défaut de Bootstrap.

## 2. RÈGLES DE SOUVERAINETÉ (ALGÉRIE)
* **Hébergement :** Local (Simulé pour le moment).
* **Privacy by Design :**
    * Les données épidémiologiques (Table `EpidemiologyData`) ne doivent JAMAIS avoir de clé étrangère vers la table `User`.
    * L'anonymat doit être irréversible (Agrégation par ville/âge).
* **Sécurité KYC :**
    * Un médecin ne peut accéder aux dossiers patients que si `kyc_status == 'VERIFIED'`.

## 3. ARCHITECTURE TECHNIQUE (SILOS)
* **Backend :** Python (Flask) + SQLAlchemy + PostgreSQL.
* **Frontend :** HTML5 + TailwindCSS (Pas de React/Vue pour l'instant).
* **Organisation des Fichiers :**
    * `models.py` : Uniquement la structure de la BDD.
    * `routes.py` : Uniquement les points d'entrée API/Web.
    * `utils/` : Toute la logique mathématique (Algos de file d'attente, chiffrement).
    * `templates/` : L'interface visuelle.

## 4. FONCTIONNALITÉS CLÉS
* **Mode Hybride :** Le médecin choisit entre 'TICKET_QUEUE' (File d'attente) et 'SMART_RDV' (Agenda dynamique).
* **Smart Shift :** Capacité de décaler tous les RDV d'une journée en cas d'urgence.

## 5. COMPORTEMENT DES ROUTES (HTTP CONTRACT)

### Accès & Redirections
* **`/` (non connecté)** → 302 vers `/login`
* **`/` (patient)** → 302 vers `/patient/dashboard`
* **`/` (doctor)** → 302 vers `/doctor/dashboard`

### Login
* **GET `/login`** → 200 + formulaire
* **POST `/login` (succès)** → 302 vers dashboard
* **POST `/login` (échec)** → 200 + message erreur (jamais 500)

### Protection des Routes
* **Ordre strict des décorateurs** :
  ```python
  @route('/doctor/dashboard')
  @login_required          # 1. Authentification
  @role_required('doctor') # 2. Autorisation
  def dashboard(): ...
Pages d'Erreur
404 → Statut 404 + texte "Page introuvable"

403 → "Accès interdit" (mauvais rôle)

500 → Page erreur + log Sentry automatique

6. SÉCURITÉ CSRF (RÈGLES ABSOLUES)
Formulaires HTML
Obligatoire après chaque <form method="POST"> :

xml
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
Requêtes AJAX (fetch)
Obligatoire dans les headers :

javascript
headers: {
  'Content-Type': 'application/json',
  'X-CSRFToken': '{{ csrf_token() }}'
}
Wrapper JS Imposé
Les agents et développeurs doivent utiliser :

javascript
await TBIB.post('/api/walkin', data)  // ✅ BON
fetch('/api/walkin', ...)             // ❌ INTERDIT
Exemptions CSRF
Liste exhaustive (avec justification) :

/pharmacy/verify/* : Scan QR code public

/webhook/payment : Callback externe CIB

7. ORGANISATION DU CODE (ARCHITECTURE INTERNE)
Structure Obligatoire
text
/TBIB
  /app
    /blueprints       # HTTP uniquement (parse, validate, redirect)
      /auth
      /doctor
      /patient
      /api
    /services         # 🧠 LOGIQUE MÉTIER PURE
      smartflow.py    # Algorithmes créneaux/retard
      ewassfa.py      # Crypto ordonnances
      billing.py      # Calculs CA
      predictor.py    # ML (futur)
    /models           # SQLAlchemy
    /schemas          # Validation Pydantic (futur)
    /static
      /js
        api_client.js # Wrapper TBIB.post
    /templates
      /components     # Partials réutilisables
RÈGLE D'OR
Aucune logique métier dans routes.py.
Les routes appellent TOUJOURS une fonction de /services.

Exemple :

python
# ❌ MAUVAIS (logique dans route)
@doctor_bp.route('/walkin', methods=['POST'])
def walkin():
    patient = Patient(...)
    db.session.add(patient)
    appointment = Appointment(...)
    # ... 50 lignes de logique

# ✅ BON (appel service)
@doctor_bp.route('/walkin', methods=['POST'])
def walkin():
    data = request.get_json()
    result = WalkinService.create_walkin(data)
    return jsonify(result)
8. RÈGLES POUR AGENTS IA (JULES/CURSOR)
Interdictions Strictes
❌ Pas de CSS inline (style="...")

❌ Pas de logique dans templates Jinja

❌ Pas de fetch sans wrapper TBIB.post

❌ Pas de librairie externe sans validation souveraineté

Scope de Modification
Par défaut, un agent ne peut modifier QUE :

Les fichiers listés dans sa mission

Les templates spécifiques

Interdiction absolue de toucher :

models.py (structure DB)

app.py (config globale)

Sauf accord explicite de l'architecte (toi).

Patterns à Suivre
Avant de coder, l'agent DOIT consulter :

templates/components/secure_form.html (formulaire type)

blueprints/doctor/routes.py (route protégée type)

static/js/api_client.js (fetch type)

9. ENVIRONNEMENT DE DÉVELOPPEMENT
Port Fixe
5001 (jamais changer)

Comptes de Test (Seed Data)
Rôle	Email	Password
Docteur	doctor1@tbib.dz	doctor123
Patient	patient1@tbib.dz	patient123
Secrétaire	secretary1@tbib.dz	secretary123
Commandes Standard
bash
# Installation
uv sync

# Seed DB
cd TBIB && uv run python seed_data.py

# Lancer serveur
cd TBIB && uv run python main.py --port 5001

# Tests
uv run pytest tests/ -v
Troubleshooting
DB dupliquée :

bash
rm TBIB/instance/tbib.db
rm tbib.db  # Si à la racine
uv run python seed_data.py
Port occupé :

bash
lsof -ti:5001 | xargs kill -9
10. TESTS & QUALITÉ
Types de Tests
Unitaires (tests/unit/) : Services purs

Intégration (tests/integration/) : Routes + DB

Contract (tests/contract/) : Vérifie respect de ce document

Chaos (tests/chaos/) : Monkeys destructeurs

Tests Contract Obligatoires
✅ Tous les forms POST ont CSRF

✅ Tous les fetch POST ont X-CSRFToken

✅ Routes protégées renvoient 403 si mauvais rôle

✅ / redirige correctement selon authentification

CI/CD
GitHub Actions doit vérifier :

Tests contract passent

Tests unitaires passent

Aucune exemption CSRF non documentée

