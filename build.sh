#!/usr/bin/env bash

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Явная установка gunicorn
/opt/render/.local/bin/uv pip install gunicorn

# Установка зависимостей
/opt/render/.local/bin/uv pip install -e .