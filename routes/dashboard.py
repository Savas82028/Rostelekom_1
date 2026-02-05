"""
Роутер главной страницы (dashboard) - шаблоны по ролям.
Роли: admin, Начальник склада, Менеджер по продажам, Приёмщик товаров, Логист
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from database.models import (
    User,
    get_robots, get_inventory_history, get_ai_predictions, get_products,
    get_users_except_admin, create_user, user_exists, recompute_products_quantities_and_status,
)
from services.ai_prognoz import generate_ai_prognoz

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def main():
    """Выбор шаблона по роли"""
    if current_user.is_admin:
        return render_template('dashboard/admin.html')
    elif current_user.role == 'Начальник склада':
        return render_template('dashboard/user.html', apps=['robots', 'inventory'])
    elif current_user.role == 'Приёмщик товаров':
        return render_template('dashboard/user.html', apps=['inventory'])
    elif current_user.role in ('Менеджер по продажам', 'Логист'):
        return render_template('dashboard/user.html', apps=['inventory', 'products', 'ai'])
    else:
        return render_template('dashboard/user.html', apps=['inventory'])


@dashboard_bp.route('/generate-prognoz', methods=['POST'])
@login_required
def generate_prognoz():
    """Запрос к ИИ API и сохранение прогноза в ai_predictions (Менеджер по продажам, Логист)"""
    if current_user.role not in ('Менеджер по продажам', 'Логист'):
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
    
    users = get_users_except_admin()
    return render_template('dashboard/users_list.html', users=users)


@dashboard_bp.route('/create-account', methods=['POST'])
@login_required
def create_account():
    """Создание аккаунта (только для админа)"""
    if not current_user.is_admin:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('dashboard.main'))
    
    name_input = request.form.get('new_login', '').strip()
    password = request.form.get('new_password', '')
    role = request.form.get('role', 'Логист')
    
    if not name_input or not password:
        flash('Заполните имя и пароль', 'error')
        return redirect(url_for('dashboard.main'))
    
    if user_exists(name_input):
        flash(f'Пользователь {name_input} уже существует', 'error')
        return redirect(url_for('dashboard.main'))
    
    if role not in User.ROLES or role == 'admin':
        flash('Выберите корректную роль', 'error')
        return redirect(url_for('dashboard.main'))
    
    create_user(name_input, password, role)
    
    flash(f'Аккаунт {name_input} успешно создан', 'success')
    return redirect(url_for('dashboard.main'))


@dashboard_bp.route('/data/warehouse')
@login_required
def data_warehouse():
    try:
        recompute_products_quantities_and_status()
    except Exception:
        pass
    robots = get_robots()
    inventory = get_inventory_history(50)
    products = {p['id']: p.get('name', p['id']) for p in get_products()}
    for inv in inventory:
        inv['product_name'] = products.get(inv.get('product_id'), inv.get('product_id'))
    return jsonify({'robots': robots, 'inventory': inventory})


@dashboard_bp.route('/data/logist')
@login_required
def data_logist():
    try:
        recompute_products_quantities_and_status()
    except Exception:
        pass
    inventory = get_inventory_history(50)
    predictions = get_ai_predictions(20)
    products_list = get_products()
    products = {p['id']: p.get('name', p['id']) for p in products_list}
    for inv in inventory:
        inv['product_name'] = products.get(inv.get('product_id'), inv.get('product_id'))
    for p in predictions:
        p['product_name'] = products.get(p.get('product_id'), p.get('product_id'))
    return jsonify({'inventory': inventory, 'predictions': predictions, 'products': products_list})


@dashboard_bp.route('/apps/<app_name>')
@login_required
def app_page(app_name):
    app_name = (app_name or '').lower()
    if current_user.is_admin:
        return redirect(url_for('dashboard.main'))
    if current_user.role == 'Начальник склада':
        if app_name not in ('robots', 'inventory'):
            flash('Доступ запрещён', 'error')
            return redirect(url_for('dashboard.main'))
        robots = get_robots()
        inventory = get_inventory_history(50)
        products_map = {p['id']: p.get('name', p['id']) for p in get_products()}
        for inv in inventory:
            inv['product_name'] = products_map.get(inv.get('product_id'), inv.get('product_id'))
        return render_template('dashboard/warehouse.html', robots=robots, inventory=inventory, view=app_name)
    if current_user.role == 'Приёмщик товаров':
        if app_name != 'inventory':
            flash('Доступ запрещён', 'error')
            return redirect(url_for('dashboard.main'))
        inventory = get_inventory_history(50)
        products_map = {p['id']: p.get('name', p['id']) for p in get_products()}
        for inv in inventory:
            inv['product_name'] = products_map.get(inv.get('product_id'), inv.get('product_id'))
        return render_template('dashboard/receiver.html', inventory=inventory, view=app_name)
    if current_user.role in ('Менеджер по продажам', 'Логист'):
        if app_name not in ('inventory', 'products', 'ai'):
            flash('Доступ запрещён', 'error')
            return redirect(url_for('dashboard.main'))
        inventory = get_inventory_history(50)
        predictions = get_ai_predictions(20)
        products_list = get_products()
        products = {p['id']: p.get('name', p['id']) for p in products_list}
        for inv in inventory:
            inv['product_name'] = products.get(inv.get('product_id'), inv.get('product_id'))
        for p in predictions:
            p['product_name'] = products.get(p.get('product_id'), p.get('product_id'))
        return render_template('dashboard/logist.html', inventory=inventory, predictions=predictions, products_list=products_list, view=app_name)
    return render_template('dashboard/user.html')
