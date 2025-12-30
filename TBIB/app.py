import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, session, render_template, request, jsonify
from extensions import db, migrate, login_manager, babel, csrf
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

def get_locale():
    return session.get('lang', 'fr')

def configure_logging(app):
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler('logs/tbib.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('TBIB startup')

def create_app():
    app = Flask(__name__)

    # Configuration sécurisée via variables d'environnement
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tbib-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tbib.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

    # Gestion du mode DEBUG
    app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

    # Configuration sécurisée des cookies
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # SESSION_COOKIE_SECURE doit être True SEULEMENT si DEBUG est False (pour HTTPS en prod)
    app.config['SESSION_COOKIE_SECURE'] = not app.config['DEBUG']

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app) # Enable CSRF protection
    login_manager.login_view = 'main.login'

    configure_logging(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def set_language():
        if 'lang' not in session:
            session['lang'] = 'fr'

    @app.after_request
    def add_cache_control(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        from routes import get_t
        app.logger.error(f'Page not found: {request.url}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('404.html', t=get_t(), lang=session.get('lang', 'fr')), 404

    @app.errorhandler(500)
    def internal_error(error):
        from routes import get_t
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal Server Error'}), 500
        return render_template('500.html', t=get_t(), lang=session.get('lang', 'fr')), 500

    from routes import main_bp
    app.register_blueprint(main_bp)

    from prescription_routes import prescription_bp
    app.register_blueprint(prescription_bp)

    return app

if __name__ == '__main__':
    app = create_app()

    # ✅ CRÉATION AUTOMATIQUE DES TABLES MANQUANTES (FIX E-WASSFA)
    with app.app_context():
        from models import Prescription  # Force la détection du modèle
        db.create_all()
        print("✅ Tables vérifiées/créées (y compris prescriptions)")

    app.run(host='0.0.0.0', port=5000)
