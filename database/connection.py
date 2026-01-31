"""
Отдельное приложение для подключения к базе данных.
Используется через роутер в основном приложении.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Инициализация подключения к БД"""
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, 'instance', 'rostelekom.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        from database.models import User, WarehouseMapCell, Receipt, AIPrognoz
        db.create_all()
        if not User.query.filter_by(login='admin').first():
            admin = User(login='admin', role='admin')
            admin.set_password('15801580')
            db.session.add(admin)
            db.session.commit()
        # Начальные данные карты склада и поступлений
        if WarehouseMapCell.query.count() == 0:
            for r in range(6):
                for c in range(8):
                    cell_type = 'empty'
                    robot_id = None
                    robot_info = None
                    if (r, c) in [(1, 2), (3, 5), (4, 1)]:
                        cell_type = 'robot'
                        robot_id = f'R{r*10+c}'
                        robot_info = 'Заряд 87%' if (r,c)==(1,2) else ('В работе' if (r,c)==(3,5) else 'Свободен')
                    elif (r, c) in [(2, 3), (2, 4), (4, 4)]:
                        cell_type = 'shelf'
                        robot_info = 'Стеллаж A'
                    elif (r, c) == (0, 7):
                        cell_type = 'obstacle'
                        robot_info = 'Стена'
                    db.session.add(WarehouseMapCell(row=r, col=c, robot_id=robot_id, robot_info=robot_info, cell_type=cell_type))
            db.session.commit()
        if Receipt.query.count() == 0:
            from datetime import datetime, timedelta
            for i, (name, qty, sup) in enumerate([
                ('Роутер Wi-Fi', 25, 'ООО Технопарк'),
                ('Кабель UTP 5e', 500, 'Кабельная компания'),
                ('Маршрутизатор', 15, 'ООО Сеть'),
                ('Патч-панель 24п', 10, 'ООО Технопарк'),
                ('Кросс-панель', 8, 'Кабельная компания'),
            ]):
                db.session.add(Receipt(product_name=name, quantity=qty, supplier=sup, receipt_date=datetime.now() - timedelta(days=i)))
            db.session.commit()
