"""
Роутер главной страницы (dashboard) - шаблоны по ролям
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from database.connection import db
from database.models import User, WarehouseMapCell, Receipt, AIPrognoz
from services.ai_prognoz import generate_ai_prognoz

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def main():
    """Выбор шаблона по роли пользователя"""
    if current_user.is_admin:
        return render_template('dashboard/admin.html')
    elif current_user.role == 'Начальник склада':
        map_cells = WarehouseMapCell.query.order_by(WarehouseMapCell.row, WarehouseMapCell.col).all()
        rows = max((c.row for c in map_cells), default=0) + 1 if map_cells else 1
        cols = max((c.col for c in map_cells), default=0) + 1 if map_cells else 1
        receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).limit(50).all()
        return render_template('dashboard/warehouse.html', map_cells=map_cells, rows=rows, cols=cols, receipts=receipts)
    elif current_user.role in ('Логист', 'Менеджер по продажам'):
        receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).limit(50).all()
        prognozy = AIPrognoz.query.order_by(AIPrognoz.created_at.desc()).limit(20).all()
        return render_template('dashboard/logist.html', receipts=receipts, prognozy=prognozy)
    elif current_user.role == 'Приёмщик товара':
        map_cells = WarehouseMapCell.query.order_by(WarehouseMapCell.row, WarehouseMapCell.col).all()
        rows = max((c.row for c in map_cells), default=0) + 1 if map_cells else 1
        cols = max((c.col for c in map_cells), default=0) + 1 if map_cells else 1
        receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).limit(50).all()
        return render_template('dashboard/receiver.html', map_cells=map_cells, rows=rows, cols=cols, receipts=receipts)
    else:
        return render_template('dashboard/user.html')


@dashboard_bp.route('/generate-prognoz', methods=['POST'])
@login_required
def generate_prognoz():
    """Запрос к ИИ API и сохранение прогноза в AI_prognoz (Логист, Менеджер по продажам)"""
    if current_user.role not in ('Логист', 'Менеджер по продажам'):
        flash('Доступ запрещён', 'error')
        return redirect(url_for('dashboard.main'))
    
    prognoz, error = generate_ai_prognoz()
    if error:
        flash(f'Ошибка: {error}', 'error')
    else:
        flash('Прогноз успешно сформирован', 'success')
    return redirect(url_for('dashboard.main'))


@dashboard_bp.route('/users')
@login_required
def users_list():
    """Страница 3: Список учётных записей (только для админа)"""
    if not current_user.is_admin:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('dashboard.main'))
    
    users = User.query.filter(User.role != 'admin').order_by(User.login).all()
    return render_template('dashboard/users_list.html', users=users)


@dashboard_bp.route('/create-account', methods=['POST'])
@login_required
def create_account():
    """Создание аккаунта (только для админа)"""
    if not current_user.is_admin:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('dashboard.main'))
    
    login_input = request.form.get('new_login', '').strip()
    password = request.form.get('new_password', '')
    role = request.form.get('role', 'Менеджер по продажам')
    
    if not login_input or not password:
        flash('Заполните логин и пароль', 'error')
        return redirect(url_for('dashboard.main'))
    
    if User.query.filter_by(login=login_input).first():
        flash(f'Пользователь {login_input} уже существует', 'error')
        return redirect(url_for('dashboard.main'))
    
    if role not in User.ROLES or role == 'admin':
        flash('Выберите корректную роль', 'error')
        return redirect(url_for('dashboard.main'))
    
    user = User(login=login_input, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash(f'Аккаунт {login_input} успешно создан', 'success')
    return redirect(url_for('dashboard.main'))
