"""
Script de réparation : Crée la table prescriptions si elle n'existe pas
À exécuter une seule fois sur Replit
"""
import os
from sqlalchemy import create_engine, text

# URL de ta base PostgreSQL (récupère depuis les variables d'environnement)
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tbib.db')

# Si c'est PostgreSQL, on adapte l'URL (Replit parfois utilise postgres:// au lieu de postgresql://)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# SQL de création de la table prescriptions
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    appointment_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    medications TEXT NOT NULL,
    notes TEXT,
    prescription_type VARCHAR(50) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    max_usage INTEGER NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (patient_id) REFERENCES users(id)
);
"""

try:
    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()
    print("✅ Table 'prescriptions' créée avec succès!")
    print("✅ Tu peux maintenant générer des ordonnances E-Wassfa")
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\n💡 Vérifie que :")
    print("   1. DATABASE_URL est bien configuré")
    print("   2. Les tables 'appointments' et 'users' existent")
