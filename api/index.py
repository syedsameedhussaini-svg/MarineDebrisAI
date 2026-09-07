"""
MarineDebrisAI - Vercel Serverless Function Entry Point
Exposes the FastAPI application for Vercel Python runtime.
"""

import sys
from pathlib import Path

# Add project root to sys.path so modules and best.pt can be located
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the FastAPI app instance
from api_server import app
