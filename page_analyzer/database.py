import os
from logging import getLogger

import psycopg2
from dotenv import load_dotenv

logger = getLogger(__name__)
load_dotenv()


def get_conn():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        logger.info("Подключение к БД успешно")
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {str(e)}")
        raise


def add_url_check(url_id):
    """Добавляет проверку с базовыми полями (url_id и created_at)"""
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id;",
                (url_id,)
            )
            conn.commit()
            return cursor.fetchone()[0]


def get_url_checks(url_id):
    """Возвращает все проверки для конкретного URL"""
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, status_code, h1, title, description, created_at "
                "FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;",
                (url_id,)
            )
            return cursor.fetchall()