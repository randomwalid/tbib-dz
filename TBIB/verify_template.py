import sys
import os
from flask import Flask, render_template, session
from flask_login import AnonymousUserMixin

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from routes import get_t

app = create_app()

with app.app_context():
    with app.test_request_context('/'):
        # Mock session
        session['lang'] = 'fr'

        # Mock data
        specialties = ['Cardiologie', 'Dentiste']
        cities = ['Alger', 'Oran']
        search_mode = False
        doctors = []

        try:
            rendered = render_template('home.html',
                                     t=get_t(),
                                     lang='fr',
                                     specialties=specialties,
                                     cities=cities,
                                     search_mode=search_mode,
                                     doctors=doctors,
                                     selected_specialty='',
                                     selected_city='')
            print("TEMPLATE RENDER SUCCESS")
            if "Votre santé, simplifiée." in rendered:
                print("New content found.")
            else:
                print("New content NOT found.")

        except Exception as e:
            print(f"TEMPLATE RENDER FAILED: {e}")
            import traceback
            traceback.print_exc()
