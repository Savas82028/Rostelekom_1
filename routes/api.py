"""
API для приёма данных от роботов склада. Сохраняет в robots и inventory_history.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from database.models import upsert_robot, insert_inventory_record

api_bp = Blueprint('api', __name__)


@api_bp.route('/robots/data', methods=['POST'])
def robots_data():
    """
    Принимает данные от эмулятора робота.
    Обновляет robots, добавляет записи в inventory_history.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON required'}), 400

    robot_id = data.get('robot_id')
    timestamp = data.get('timestamp')
    location = data.get('location', {})
    scan_results = data.get('scan_results', [])
    battery_level = data.get('battery_level')
    next_checkpoint = data.get('next_checkpoint')

    if not robot_id or not timestamp:
        return jsonify({'error': 'robot_id and timestamp required'}), 400

    zone = location.get('zone', 'A')
    row = location.get('row', 1)
    shelf = location.get('shelf', 1)

    try:
        # Обновляем робота
        upsert_robot(
            robot_id=robot_id,
            status='active',
            battery_level=battery_level,
            current_zone=str(zone),
            current_row=int(row),
            current_shelf=int(shelf)
        )

        # Добавляем записи инвентаризации
        scanned_at = timestamp
        for scan in scan_results:
            product_id = scan.get('product_id', scan.get('product_name', 'UNKNOWN'))
            quantity = scan.get('quantity', 0)
            status = scan.get('status', 'OK')
            insert_inventory_record(
                robot_id=robot_id,
                product_id=product_id,
                quantity=quantity,
                zone=str(zone),
                row_number=int(row),
                shelf_number=int(shelf),
                status=status,
                scanned_at=scanned_at
            )

        return jsonify({'status': 'ok', 'robot_id': robot_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
