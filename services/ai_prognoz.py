"""
Сервис получения ИИ-прогнозов на основе поступлений.
Поддерживает DeepSeek API и Groq API (бесплатный tier).
"""
import os
import json
import requests
from dotenv import load_dotenv

from database.connection import db
from database.models import Receipt, AIPrognoz

load_dotenv()

# Groq — бесплатный tier, Llama-модели
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# DeepSeek — требует пополнения баланса
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


def generate_ai_prognoz():
    """
    Получает поступления из БД, отправляет в ИИ-API (Groq или DeepSeek),
    сохраняет прогноз в AI_prognoz и возвращает его.
    """
    receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).limit(50).all()
    
    if not receipts:
        return None, "Нет данных о поступлениях для анализа"
    
    lines = []
    for r in receipts:
        date_str = r.receipt_date.strftime('%d.%m.%Y') if r.receipt_date else '—'
        lines.append(f"- {r.product_name}: {r.quantity} шт. (дата: {date_str}, поставщик: {r.supplier or '—'})")
    data_text = "\n".join(lines)
    
    user_input = (
        "Ты — аналитик логистики. На основе данных о поступлениях товаров на склад "
        "дай краткий прогноз: какие товары могут потребоваться в ближайшее время, "
        "рекомендации по закупкам и логистике. Отвечай на русском языке, структурированно.\n\n"
        f"Данные о поступлениях на склад:\n\n{data_text}\n\nСформируй прогноз."
    )
    
    # Приоритет: Groq (бесплатный) → DeepSeek
    groq_key = os.getenv("GROQ_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    prognoz_text = None
    deepseek_402 = False
    
    if groq_key:
        prognoz_text, _ = _call_api(GROQ_URL, groq_key, GROQ_MODEL, user_input)
    if prognoz_text is None and deepseek_key:
        prognoz_text, err = _call_api(DEEPSEEK_URL, deepseek_key, DEEPSEEK_MODEL, user_input)
        if prognoz_text is None and err and "402" in str(err):
            deepseek_402 = True
    if prognoz_text is None:
        prognoz_text = _demo_prognoz(receipts, data_text, payment_required=deepseek_402)
    
    prognoz = AIPrognoz(prognoz_text=prognoz_text)
    db.session.add(prognoz)
    db.session.commit()
    return prognoz, None


def _call_api(url, api_key, model, user_input):
    """Вызов ИИ-API. Возвращает (text, error) — text или None при ошибке."""
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": model,
            "messages": [{"role": "user", "content": user_input}],
            "max_tokens": 800
        }
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"] or "", None
    except requests.RequestException as e:
        return None, str(e)
    except json.JSONDecodeError:
        return None, "Неверный формат ответа"
    except (KeyError, IndexError):
        return None, "Ошибка формата ответа"


def _demo_prognoz(receipts, data_text, payment_required=False):
    """Демо-прогноз без API-ключа или при ошибке"""
    products = list(set(r.product_name for r in receipts))
    if payment_required:
        note = "DeepSeek требует пополнения баланса. Groq бесплатен — получите ключ на https://console.groq.com/keys и укажите GROQ_API_KEY в .env"
    else:
        note = "Задайте GROQ_API_KEY (бесплатно) или DEEPSEEK_API_KEY в .env для ИИ-прогноза."
    return (
        f"Прогноз на основе {len(receipts)} записей поступлений:\n\n"
        f"Анализ товаров: {', '.join(products[:5])}{'...' if len(products) > 5 else ''}\n\n"
        "Рекомендации: увеличьте объём закупок кабельной продукции и роутеров на 15–20% "
        "в связи с сезонным спросом. Обратите внимание на поставщика ООО Технопарк — "
        "оптимизируйте частоту поставок.\n\n"
        f"{note}"
    )
