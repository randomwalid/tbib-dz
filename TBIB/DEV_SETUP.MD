Fichier : /TBIB/DEV_SETUP.md

text
# TBIB - Guide d'Installation & Développement

## Prérequis

- Python 3.11+
- PostgreSQL 16 (ou SQLite pour dev local)
- UV (gestionnaire de paquets Python)

## Installation Rapide

```bash
# 1. Cloner le repo
git clone [ton-repo-url]
cd TBIB

# 2. Installer les dépendances
uv sync

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec tes valeurs

# 4. Initialiser la base de données
cd TBIB
uv run python seed_data.py
Lancement du Serveur
Port fixe : 5001 (ne jamais changer)

bash
cd TBIB
uv run python main.py --port 5001
L'application est accessible sur : http://localhost:5001

Comptes de Test
Rôle	Email	Password
Docteur	doctor1@tbib.dz	doctor123
Patient	patient1@tbib.dz	patient123
Secrétaire	secretary1@tbib.dz	secretary123
Admin	admin@tbib.dz	admin123
Tests
bash
# Tous les tests
uv run pytest tests/ -v

# Tests unitaires uniquement
uv run pytest tests/unit/ -v

# Tests contract (vérifie respect architecture)
uv run pytest tests/contract/ -v

# Tests chaos (destructifs)
uv run pytest tests/chaos/ -v
Structure du Projet
text
/TBIB
  ├── ARCHITECTURE.md        # Vision stratégique
  ├── AGENT_PROTOCOL.md      # Règles de code
  ├── DEV_SETUP.md          # Ce fichier
  ├── main.py               # Point d'entrée
  ├── seed_data.py          # Init DB
  └── /app
      ├── /blueprints       # Routes HTTP
      ├── /services         # Logique métier
      ├── /models           # SQLAlchemy
      └── /templates        # Jinja2
Troubleshooting
Erreur "Database already exists"
bash
rm TBIB/instance/tbib.db
rm tbib.db  # Si à la racine
uv run python seed_data.py
Port 5001 déjà utilisé
bash
lsof -ti:5001 | xargs kill -9
Erreur CSRF 400
Vérifier que :

Le formulaire a {{ csrf_token() }}

Les fetch utilisent TBIB.post() avec header X-CSRFToken

Workflow Git
bash
# Avant de coder
git checkout -b feature/nom-feature

# Avant de commit
uv run pytest tests/contract/ -v  # Vérifier le contrat

# Commit
git add .
git commit -m "feat: description"

# Push
git push origin feature/nom-feature
Contact
En cas de problème : [ton-email-ou-contact]

text

***

## ✅ CHECKLIST DE CE SOIR

Avant de dormir, tu dois avoir dans `/TBIB` :

- ✅ `ARCHITECTURE.md` (modifié avec sections 5-10)
- ✅ `AGENT_PROTOCOL.md` (créé, 600 lignes)
- ✅ `DEV_SETUP.md` (à créer maintenant, 5 min)

**Ces 3 fichiers = ta fondation documentaire complète.**

***

## 📅 DEMAIN MATIN (Avec terminal)

### 1. Commit des 3 fichiers (5 min)

```bash
cd TBIB
git add ARCHITECTURE.md AGENT_PROTOCOL.md DEV_SETUP.md
git commit -m "docs: Architecture Agent-Friendly complète (Protocole Omega)"
git push
2. Quick Win : Créer /services (5 min)
bash
cd TBIB/app
mkdir -p services
touch services/__init__.py
touch services/smartflow.py
touch services/ewassfa.py
touch services/billing.py
3. Audit CSRF rapide (10 min)
bash
# Lister tous les formulaires POST
grep -rn "<form method=\"POST\"" TBIB/templates/

# Note mentalement lesquels manquent csrf_token
# (Ne pas corriger maintenant, Jules le fera)