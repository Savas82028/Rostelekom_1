"""
Модели базы данных
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import db


class User(UserMixin, db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Менеджер по продажам')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    ROLES = [
        'admin',
        'Начальник склада',
        'Логист',
        'Менеджер по продажам',
        'Приёмщик товара'
    ]
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.login}>'


class WarehouseMapCell(db.Model):
    """Ячейка карты склада с информацией о роботе"""
    __tablename__ = 'warehouse_map_cells'
    
    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer, nullable=False)
    col = db.Column(db.Integer, nullable=False)
    robot_id = db.Column(db.String(50), nullable=True)
    robot_info = db.Column(db.String(255), nullable=True)  # статус, заряд и т.д.
    cell_type = db.Column(db.String(50), default='empty')  # empty, robot, shelf, obstacle
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<MapCell {self.row},{self.col}>'


class Receipt(db.Model):
    """Поступление товара на склад"""
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    supplier = db.Column(db.String(200), nullable=True)
    receipt_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<Receipt {self.product_name} x{self.quantity}>'


class AIPrognoz(db.Model):
    """ИИ-прогнозы на основе поступлений"""
    __tablename__ = 'AI_prognoz'
    
    id = db.Column(db.Integer, primary_key=True)
    prognoz_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<AIPrognoz {self.id}>'
