import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .database import add_url_check, get_conn

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()

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
                            INSERT INTO urls (url)
                            VALUES (%s)
                            ON CONFLICT (url) DO NOTHING
                            RETURNING id
                        """, (url,))
                        if cur.fetchone():
                            flash('Сайт добавлен!', 'success')
                        else:
                            flash('Сайт уже существует', 'info')
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
                    uc.created_at AS last_check_date,
                    uc.status_code
                FROM urls u
                LEFT JOIN (
                    SELECT 
                        url_id,
                        created_at,
                        status_code,
                        ROW_NUMBER() OVER (PARTITION BY 
                           url_id ORDER BY created_at DESC) AS rn
                    FROM url_checks
                ) uc ON u.id = uc.url_id AND uc.rn = 1
                ORDER BY u.id DESC;
            """)
            urls = cursor.fetchall()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
            url = cursor.fetchone()
            
            cursor.execute("""
                SELECT * FROM url_checks 
                WHERE url_id = %s 
                ORDER BY created_at DESC;
            """, (id,))
            checks = cursor.fetchall()
    return render_template("url.html", url=url, checks=checks)
    

@app.post("/urls/<int:url_id>/checks")
def add_check(url_id):
    try:
        check_id = add_url_check(url_id)
        flash("Страница успешно проверена!", "success")
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "danger")
    return redirect(url_for("show_url", id=url_id))


if __name__ == '__main__':
    app.run(debug=True)