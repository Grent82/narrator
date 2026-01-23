import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:17000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "17080"))
FRONTEND_LOG_FILE = os.getenv("FRONTEND_LOG_FILE", "logs/frontend.log")
