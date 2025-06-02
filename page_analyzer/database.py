import os
from logging import getLogger

import psycopg2
from dotenv import load_dotenv

logger = getLogger(__name__)
load_dotenv()


def get_conn():
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL'),
            connect_timeout=5
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise


def add_url_check(url_id, status_code=None):
    """Только обязательные поля + status_code"""
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO url_checks (url_id, status_code)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (url_id, status_code)
            )
            conn.commit()
            return cursor.fetchone()[0]


def get_url_checks(url_id):
    """Возвращает все проверки URL (статус-код теперь будет в списке)"""
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, status_code, h1, title, description, created_at 
                FROM url_checks 
                WHERE url_id = %s 
                ORDER BY created_at DESC;
                """,
                (url_id,)
            )
            return cursor.fetchall()


def get_last_check(url_id):
    """Возвращает последнюю проверку (опционально, если часто используется)"""
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT status_code 
                FROM url_checks 
                WHERE url_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1;
                """,
                (url_id,)
            )
            return cursor.fetchone()
