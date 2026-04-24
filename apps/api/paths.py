"""Filesystem roots for the API layer."""

import os

_API_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_API_DIR, "..", ".."))
