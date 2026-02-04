"""
Главное приложение Ростелеком.
Подключается к базе данных через модуль database и маршрутизатор.
"""
from dotenv import load_dotenv
import os
load_dotenv()

from flask import Flask
from flask_login import LoginManager

from database.connection import init_db
from database.models import get_user_by_id

# Импорт роутеров (после создания app)
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'rostelekom-secret-key-2024'
    
    # Подключение к Supabase
    init_db(app)
    
    # Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Войдите для доступа к этой странице'
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)
    
    # Регистрация blueprint'ов (роутеров)
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app


app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 10000))
    app.run(host=host, port=port)
