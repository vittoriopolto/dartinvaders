#!/usr/bin/env bash
# Eseguito da Render a ogni deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Crea l'utente admin al primo deploy (la versione gratuita di Render non ha la Shell).
# Se l'utente esiste già il comando fallisce e lo ignoriamo.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --no-input || true
fi
