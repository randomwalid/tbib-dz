from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

def reset_password():
    app = create_app()
    # On ouvre l'accès à la base de données
    ctx = app.app_context()
    ctx.push()

    # C'EST ICI QU'ON CHANGE LA CIBLE
    # D'après ta capture d'écran, cet email existe vraiment :
    target_email = "doc1@tbib.dz" 
    new_pass = "123456"

    print(f"🔍 Recherche de l'utilisateur réel : {target_email}...")

    try:
        # On cherche l'utilisateur dans la base
        user = User.query.filter_by(email=target_email).first()

        if user:
            # S'il est trouvé, on écrase son mot de passe
            user.password_hash = generate_password_hash(new_pass)
            db.session.commit()
            print(f"✅ SUCCÈS CONFIRMÉ : Le mot de passe de {target_email} est maintenant '{new_pass}'")
            print("👉 Tu peux aller te connecter sur le site !")
        else:
            # Si ça échoue encore (très improbable), on affiche pourquoi
            print(f"❌ ERREUR : Impossible de trouver {target_email}. C'est anormal.")

    except Exception as e:
        print(f"❌ ERREUR CRITIQUE : {e}")
    finally:
        ctx.pop()

if __name__ == "__main__":
    reset_password()
