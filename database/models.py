"""
Модели и репозитории для Supabase.
Таблицы: users, robots, products, inventory_history, ai_predictions
"""
from datetime import datetime, date
from flask_login import UserMixin

from database.connection import get_supabase


# --- User ---

class User(UserMixin):
    """Модель пользователя. Роли, которые может выдавать админ."""
    ROLES = ['Начальник склада', 'Менеджер по продажам', 'Приёмщик товаров', 'Логист']

    def __init__(self, id, name, password, role, created_at=None):
        self.id = int(id) if id else None
        self.name = name
        self.login = name  # для совместимости с шаблонами (current_user.login)
        self.password = password
        self.role = role
        self.created_at = created_at

    def check_password(self, password):
        return self.password == password

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.name}>'


def _user_from_row(row):
    if not row:
        return None
    return User(
        id=row.get('id'),
        name=row.get('name', ''),
        password=row.get('password', ''),
        role=row.get('role', 'Логист'),
        created_at=row.get('created_at')
    )


def get_user_by_id(user_id):
    try:
        supabase = get_supabase()
        r = supabase.table('users').select('*').eq('id', int(user_id)).limit(1).execute()
        return _user_from_row(r.data[0]) if r.data and len(r.data) > 0 else None
    except Exception as e:
        if '204' in str(e) or 'Missing response' in str(e):
            return None
        raise


def get_user_by_name(name):
    """Загрузка пользователя по имени (для входа)."""
    try:
        supabase = get_supabase()
        r = supabase.table('users').select('*').eq('name', name).limit(1).execute()
        return _user_from_row(r.data[0]) if r.data and len(r.data) > 0 else None
    except Exception as e:
        if '204' in str(e) or 'Missing response' in str(e):
            return None
        raise


def create_user(name, password, role):
    supabase = get_supabase()
    data = {'name': name, 'password': password, 'role': role}
    r = supabase.table('users').insert(data).execute()
    return _user_from_row(r.data[0]) if r.data and len(r.data) > 0 else None


def get_users_except_admin():
    supabase = get_supabase()
    r = supabase.table('users').select('*').neq('role', 'admin').order('name').execute()
    return [_user_from_row(row) for row in (r.data or [])]


def user_exists(name):
    return get_user_by_name(name) is not None


# --- Robot ---

def get_robots():
    supabase = get_supabase()
    r = supabase.table('robots').select('*').execute()
    return r.data or []


def upsert_robot(robot_id, status='active', battery_level=None, current_zone=None, current_row=None, current_shelf=None):
    supabase = get_supabase()
    data = {
        'id': robot_id,
        'status': status,
        'battery_level': int(battery_level) if battery_level is not None else None,
        'last_update': datetime.utcnow().isoformat() + 'Z',
        'current_zone': current_zone,
        'current_row': current_row,
        'current_shelf': current_shelf
    }
    supabase.table('robots').upsert(data, on_conflict='id').execute()


# --- Inventory history ---

def insert_inventory_record(robot_id, product_id, quantity, zone, row_number, shelf_number, status, scanned_at):
    supabase = get_supabase()
    data = {
        'robot_id': robot_id,
        'product_id': product_id,
        'quantity': quantity,
        'zone': zone,
        'row_number': row_number,
        'shelf_number': shelf_number,
        'status': status,
        'scanned_at': scanned_at
    }
    r = supabase.table('inventory_history').insert(data).execute()
    return r.data[0] if r.data and len(r.data) > 0 else None


def get_inventory_history(limit=50):
    supabase = get_supabase()
    r = supabase.table('inventory_history').select('*').order('scanned_at', desc=True).limit(limit).execute()
    return r.data or []


# --- Products ---

def get_products():
    supabase = get_supabase()
    r = supabase.table('products').select('*').execute()
    return r.data or []


# --- AI Predictions ---

def get_ai_predictions(limit=20):
    supabase = get_supabase()
    r = supabase.table('ai_predictions').select('*').order('created_at', desc=True).limit(limit).execute()
    return r.data or []


def insert_ai_prediction(product_id, prediction_date, days_until_stockout=None, recommended_order=None, confidence_score=None):
    supabase = get_supabase()
    pred_date = prediction_date.isoformat() if isinstance(prediction_date, date) else str(prediction_date)
    data = {
        'product_id': product_id,
        'prediction_date': pred_date,
        'days_until_stockout': days_until_stockout,
        'recommended_order': recommended_order,
        'confidence_score': float(confidence_score) if confidence_score is not None else None
    }
    r = supabase.table('ai_predictions').insert(data).execute()
    return r.data[0] if r.data and len(r.data) > 0 else None
