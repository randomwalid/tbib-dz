import pytest
import os
import sys

# Ensure TBIB directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models import User

@pytest.fixture
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['TESTING'] = 'True'
    os.environ['WTF_CSRF_ENABLED'] = 'False'

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
