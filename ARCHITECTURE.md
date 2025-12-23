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
