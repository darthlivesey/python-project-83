import os
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .database import get_conn


def normalize_url(url_string):
    parsed = urlparse(url_string)
    
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    if ':' in netloc:
        host, port = netloc.split(':', 1)
        if (scheme == 'http' and port == '80') or (
            scheme == 'https' and port == '443'):
            netloc = host
    
    path = parsed.path.rstrip('/') or '/'
    
    return f"{scheme}://{netloc}{path}"


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('URL обязателен', 'danger')
            return render_template('index.html'), 422

        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                flash('Некорректный URL', 'danger')
                return render_template('index.html'), 422
                
            normalized_url = normalize_url(url)
            
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO urls (url) VALUES (%s) ON CONFLICT "
                        "(url) DO NOTHING RETURNING id",
                        (normalized_url,)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        flash('Страница успешно добавлена', 'success')
                        return redirect(url_for('show_url', id=result[0]))
                    else:
                        cur.execute("SELECT id FROM urls WHERE url = %s", 
                                    (normalized_url,))
                        existing_id = cur.fetchone()[0]
                        flash('Страница уже существует', 'info')
                        return redirect(url_for('show_url', id=existing_id))
        except Exception as e:
            flash(f'Ошибка базы данных: {str(e)}', 'danger')
            return render_template('index.html'), 500
            
    return render_template('index.html')


@app.route("/urls", methods=["GET", "POST"])
def handle_urls():
    if request.method == "POST":
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('URL обязателен', 'danger')
            return redirect(url_for('index')), 422
            
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                flash('Некорректный URL', 'danger')
                return redirect(url_for('index')), 422
                
            normalized_url = normalize_url(url)
            
            with get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO urls (url) VALUES (%s) ON CONFLICT (url) " 
                        "DO NOTHING RETURNING id",
                        (normalized_url,)
                    )
                    result = cursor.fetchone()
                    conn.commit()

                    if result:
                        flash('Страница успешно добавлена', 'success')
                        return redirect(url_for('show_url', id=result[0]))
                    else:
                        cursor.execute("SELECT id FROM urls WHERE url = %s", 
                                       (normalized_url,))
                        existing_id = cursor.fetchone()[0]
                        flash('Страница уже существует', 'info')
                        return redirect(url_for('show_url', id=existing_id))
        except Exception as e:
            flash(f'Ошибка при обработке URL: {str(e)}', 'danger')
            return redirect(url_for('index')), 500

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
                GROUP BY u.id, u.url
                ORDER BY u.id DESC;
            """)
            urls = cursor.fetchall()

    return render_template("urls.html", url_list=urls)


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
                return redirect(url_for('handle_urls'))
            
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
    status_code = None
    h1 = None
    title = None
    description = None
    error = None
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT url FROM urls WHERE id = %s;", (url_id,))
                url_data = cursor.fetchone()
                if not url_data:
                    flash("Сайт не найден", "danger")
                    return redirect(url_for("show_url", id=url_id))

        response = requests.get(
            url_data[0],
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'},
            allow_redirects=True
        )
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.get_text().strip() if soup.h1 else None
        title = soup.title.string.strip() if soup.title else None
        
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                    soup.find('meta', attrs={'property': 'og:description'})
        description = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else None

    except requests.exceptions.RequestException as e:
        error = f"Произошла ошибка при проверке: {str(e)}"
    except Exception as e:
        error = f"Ошибка парсинга страницы: {str(e)}"

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
            """, (url_id, status_code, h1, title, description))
            conn.commit()

    if error:
        flash(error, "danger")
    else:
        flash("Страница успешно проверена!", "success")

    return redirect(url_for("show_url", id=url_id))


if __name__ == '__main__':
    app.run(debug=True)