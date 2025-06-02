# Анализатор сайтов

[![Actions Status](https://github.com/darthlivesey/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/darthlivesey/python-project-83/actions)
[![SonarQube Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=darthlivesey_python-project-83&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=darthlivesey_python-project-83)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3-green)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15-purple)](https://www.postgresql.org/)

Профессиональный инструмент для SEO-анализа веб-страниц. Проверяет ключевые мета-теги и статус страниц.

## 🌟 Особенности

- Проверка HTTP-статуса страниц
- Анализ SEO-тегов (`h1`, `title`, `description`)
- История проверок с датировкой
- Простое API для интеграции

## 🛠 Технологии

| Компонент       | Технология         |
|----------------|--------------------|
| Бэкенд         | Python + Flask     |
| База данных    | PostgreSQL         |
| Парсинг        | BeautifulSoup4     |
| Фронтенд       | Bootstrap 5        |
| Деплой         | Gunicorn + Nginx   |

## 🚀 Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/darthlivesey/python-project-83.git
cd python-project-83

# Установка зависимостей
python -m pip install -r requirements.txt

# Настройка .env
echo "DATABASE_URL=postgresql://user:pass@localhost:5432/dbname" > .env

# Запуск
flask run