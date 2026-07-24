"""
Shared pytest fixtures and environment setup.

The application reads SCRAPFLY_API_KEY, Z_AI_API_KEY, and SECRET_KEY from
the environment at import time (see app/config.py). Set safe test defaults
here so tests can import app.* without crashing on a real environment.
"""
import os

# Set test-safe defaults BEFORE any app import.
os.environ.setdefault("SCRAPFLY_API_KEY", "test-scrape-key")
os.environ.setdefault("Z_AI_API_KEY", "test-zai-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
