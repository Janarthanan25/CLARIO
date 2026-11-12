import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env', override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clario-dev-secret-key-change-in-production-2026')
    
    # Database
    db_dir = basedir / 'instance'
    db_dir.mkdir(exist_ok=True)
    default_db_path = (db_dir / 'clario.db').as_posix()
    
    env_db = os.environ.get('DATABASE_URL')
    if env_db and not env_db.startswith('sqlite:///instance'):
        SQLALCHEMY_DATABASE_URI = env_db
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{default_db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = basedir / 'uploads'
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'csv'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    
    # AI Engine (Google Gemini)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    GEMINI_FALLBACK_MODELS = ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-flash-lite-latest', 'gemini-3.1-flash-lite']
    
    # PayPal Sandbox
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '').strip()
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '').strip()
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox').lower()
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID', '').strip()
    PAYPAL_API_BASE = 'https://api-m.sandbox.paypal.com' if PAYPAL_MODE == 'sandbox' else 'https://api-m.paypal.com'
    
    # Subscription Tiers
    SUBSCRIPTION_PLANS = {
        'FREE': {
            'name': 'Free Starter',
            'price': 0.00,
            'currency': 'USD',
            'interval': 'forever',
            'ai_requests_limit': 25,
            'document_upload_limit': 5,
            'features': [
                'Basic Document Intelligence',
                'Standard Email Assistant',
                'Basic Transaction Anomaly Scan',
                '25 AI Requests / Day',
                'Community Support'
            ]
        },
        'PRO': {
            'name': 'Clario Professional',
            'price': 29.00,
            'currency': 'USD',
            'interval': 'monthly',
            'ai_requests_limit': 500,
            'document_upload_limit': 100,
            'features': [
                'Multi-Agent Orchestration Engine',
                'Unlimited Document Processing',
                'Isolation Forest Financial Fraud Scan',
                'Custom Email Tone Generation',
                'Executive PDF/CSV Reports',
                'Priority Gemini Processing',
                'Dedicated 24/7 Support'
            ]
        }
    }

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
