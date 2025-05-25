from flask import Flask, request, flash, redirect, url_for, render_template
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def get_conn():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        app.logger.info("Подключение к БД успешно")
        return conn
    except Exception as e:
        app.logger.error(f"Ошибка подключения к БД: {str(e)}")
        raise

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        # Валидация
        if not url:
            flash('URL не может быть пустым', 'danger')
        elif len(url) > 255:
            flash('URL превышает 255 символов', 'danger')
        elif not url.startswith(('http://', 'https://')):
            flash('URL должен начинаться с http:// или https://', 'danger')
        else:
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO urls (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO NOTHING
                            RETURNING id
                        """, (url,))
                        if cur.fetchone():
                            flash('Сайт добавлен!', 'success')
                        else:
                            flash('Сайт уже существует', 'info')
            except Exception as e:
                flash(f'Ошибка базы данных: {str(e)}', 'danger')
    return render_template('index.html')

@app.route('/urls')
def url_list():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
                urls = cur.fetchall()
        return render_template('urls.html', urls=urls)
    except Exception as e:
        flash(f'Ошибка при загрузке списка: {str(e)}', 'danger')
        return render_template('urls.html', urls=[])

if __name__ == '__main__':
    app.run(debug=True)