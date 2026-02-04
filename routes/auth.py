"""
Роутер авторизации - страница входа
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from database.models import get_user_by_name

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    if request.method == 'POST':
        name_input = request.form.get('login', '').strip()  # поле "логин" = name в БД
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        user = get_user_by_name(name_input)
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('dashboard.main'))
        else:
            flash('Неверное имя или пароль', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
