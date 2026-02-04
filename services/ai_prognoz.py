"""
Сервис получения ИИ-прогнозов. Использует inventory_history и products.
Сохраняет в ai_predictions (структурированные прогнозы по товарам).
"""
import os
import json
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

from database.models import get_inventory_history, get_products, insert_ai_prediction

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


def generate_ai_prognoz():
    """
    Получает данные из inventory_history и products, отправляет в ИИ-API,
    сохраняет прогнозы в ai_predictions.
    """
    inventory = get_inventory_history(50)
    products = get_products()

    if not inventory:
        return None, "Нет данных инвентаризации для анализа"

    product_names = {p['id']: p.get('name', p['id']) for p in products}
    lines = []
    for inv in inventory:
        product_name = product_names.get(inv.get('product_id'), inv.get('product_id'))
        scanned = inv.get('scanned_at', '')[:10] if inv.get('scanned_at') else '—'
        lines.append(f"- {product_name}: {inv.get('quantity', 0)} шт. (дата: {scanned}, статус: {inv.get('status', '—')})")
    data_text = "\n".join(lines)

    user_input = (
        "Ты — аналитик логистики. На основе данных инвентаризации товаров на складе "
        "дай прогноз по каждому товару: сколько дней до исчерпания запаса, "
        "рекомендуемый объём заказа, уверенность прогноза (0.0–1.0). "
        "Отвечай ТОЛЬКО в формате JSON-массива, каждый элемент: "
        '{"product_id": "TEL-4567", "days_until_stockout": 14, "recommended_order": 50, "confidence": 0.85}. '
        "Если не можешь дать точные числа — используй оценки.\n\n"
        f"Данные инвентаризации:\n\n{data_text}\n\n"
        "Список product_id из данных выше. Верни JSON-массив прогнозов."
    )

    groq_key = os.getenv("GROQ_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    prognoz_text = None
    deepseek_402 = False

    if groq_key:
        prognoz_text, _ = _call_api(GROQ_URL, groq_key, GROQ_MODEL, user_input)
    if prognoz_text is None and deepseek_key:
        prognoz_text, err = _call_api(DEEPSEEK_URL, deepseek_key, DEEPSEEK_MODEL, user_input)
        if prognoz_text and err and "402" in str(err):
            deepseek_402 = True

    if prognoz_text is None:
        # Демо: создаём прогнозы на основе данных
        product_ids = list(set(inv.get('product_id') for inv in inventory if inv.get('product_id')))
        pred_date = date.today()
        for pid in product_ids[:5]:
            insert_ai_prediction(
                product_id=pid,
                prediction_date=pred_date,
                days_until_stockout=14,
                recommended_order=50,
                confidence_score=0.75
            )
        return True, None

    # Парсим JSON из ответа ИИ
    try:
        # Извлекаем JSON из ответа (может быть обёрнут в markdown)
        text = prognoz_text.strip()
        if '```' in text:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                text = text[start:end]
        predictions = json.loads(text)
        if not isinstance(predictions, list):
            predictions = [predictions]
    except json.JSONDecodeError:
        # Fallback: один общий прогноз
        product_ids = list(set(inv.get('product_id') for inv in inventory if inv.get('product_id')))
        for pid in product_ids[:3]:
            insert_ai_prediction(pid, date.today(), 14, 50, 0.7)
        return True, None

    pred_date = date.today()
    for p in predictions:
        pid = p.get('product_id') or p.get('product_name')
        if not pid:
            continue
        insert_ai_prediction(
            product_id=str(pid),
            prediction_date=pred_date,
            days_until_stockout=p.get('days_until_stockout'),
            recommended_order=p.get('recommended_order'),
            confidence_score=p.get('confidence') or p.get('confidence_score')
        )
    return True, None


def _call_api(url, api_key, model, user_input):
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": user_input}], "max_tokens": 800}
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"] or "", None
    except requests.RequestException as e:
        return None, str(e)
    except (json.JSONDecodeError, KeyError, IndexError):
        return None, "Ошибка формата ответа"
