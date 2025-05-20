#!/usr/bin/env bash

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
make install

if ! command -v waitress-serve &> /dev/null; then
    echo "Waitress not found! Reinstalling..."
    uv pip install --force-reinstall waitress
fi