import os
from dotenv import load_dotenv

# Load environment variables from .env file (does not override existing env)
load_dotenv()

class Config:
    # Provide sensible local defaults so the app can boot for development
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///./instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    EXPORT_DIR = os.getenv('EXPORT_DIR', 'instance/exports')
    # Optional bootstrap config for first-run initialization
    INIT_TOKEN = os.getenv('INIT_TOKEN', '')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
