"""
Подключение к Supabase через URL и API key.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://vcpmhxenvlvtiexfnrlu.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "sb_publishable_yUGmf-IJm411Pp3aT-_cng_agoXT3Pw"
)

_supabase: Client | None = None


def get_supabase() -> Client:
    """Возвращает клиент Supabase (singleton)."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def init_db(app):
    """
    Инициализация подключения к Supabase.
    Таблицы создаются через SQL-скрипт supabase_init.sql в дашборде Supabase.
    """
    try:
        from database.models import get_user_by_name, create_user
        admin = get_user_by_name('admin')
        if not admin:
            create_user('admin', '15801580', 'admin')
    except Exception:
        pass  # Таблицы могут ещё не существовать — выполните supabase_init.sql в Supabase SQL Editor
