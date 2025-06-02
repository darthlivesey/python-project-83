import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .database import get_conn

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('Некорректный URL', 'danger')
        elif len(url) > 255:
            flash('Некорректный URL', 'danger')
        elif not url.startswith(('http://', 'https://')):
            flash('Некорректный URL', 'danger')
        else:
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO urls (url) VALUES (%s)
                            ON CONFLICT (url) DO NOTHING
                            RETURNING id
                        """, (url,))
                        if cur.fetchone():
                            flash('Страница успешно добавлена!', 'success')
                        else:
                            flash('Страница уже существует', 'info')
            except Exception as e:
                flash(f'Ошибка базы данных: {str(e)}', 'danger')
    return render_template('index.html')


@app.route("/urls")
def list_urls():
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id, 
                    u.url, 
                    MAX(uc.created_at) as last_check,
                    (SELECT status_code FROM url_checks 
                     WHERE url_id = u.id 
                     ORDER BY created_at DESC LIMIT 1) as last_status
                FROM urls u
                LEFT JOIN url_checks uc ON u.id = uc.url_id
                GROUP BY u.id
                ORDER BY u.id DESC;
            """)
            urls = cursor.fetchall()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, url, created_at 
                FROM urls 
                WHERE id = %s;
            """, (id,))
            url = cursor.fetchone()
            
            if not url:
                flash('Сайт не найден', 'danger')
                return redirect(url_for('list_urls'))
            
            cursor.execute("""
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks 
                WHERE url_id = %s 
                ORDER BY created_at DESC;
            """, (id,))
            checks = cursor.fetchall()
         
    return render_template("url_detail.html", 
                         url={
                             'id': url[0],
                             'name': url[1],
                             'created_at': url[2]
                         }, 
                         checks=checks)


@app.post("/urls/<int:url_id>/checks")
def add_check(url_id):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT url FROM urls WHERE id = %s;", (url_id,))
            url_data = cursor.fetchone()
            if not url_data:
                flash("Сайт не найден", "danger")
                return redirect(url_for("show_url", id=url_id))
            url = url_data[0]

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.get_text().strip() if soup.h1 else None
        title = soup.title.get_text().strip() if soup.title else None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'].strip() if meta_desc else None

        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO url_checks (
                        url_id, 
                        status_code,
                        h1,
                        title,
                        description
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    url_id, 
                    response.status_code,
                    h1,
                    title,
                    description
                ))
                conn.commit()

        flash("Страница успешно проверена!", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Произошла ошибка при проверке: {str(e)}", "danger")
        app.logger.error(f"Ошибка проверки URL (id={url_id}): {str(e)}")
    except Exception as e:
        flash(f"Ошибка парсинга страницы: {str(e)}", "warning")
        app.logger.error(f"Ошибка парсинга (id={url_id}): {str(e)}")

    return redirect(url_for("show_url", id=url_id))


if __name__ == '__main__':
    app.run(debug=True)