"""WSGI entry point for production servers (Gunicorn, Render, Railway)."""

from app import app

application = app
