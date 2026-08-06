#!/usr/bin/env bash
# Run ruff linting and formatting checks on the backend code

set -e

cd "$(dirname "$0")/.."

echo "Running ruff check (with auto-fix)..."
cd backend
python -m ruff check --fix .

echo "Running ruff format..."
python -m ruff format .

echo "✓ Done!"
