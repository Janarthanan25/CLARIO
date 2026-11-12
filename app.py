import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded from project root before anything else
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env', override=True)

from flask import Flask, render_template, jsonify
from flask_login import LoginManager, current_user
from config import Config
from models import db
from models.models import User, Notification
from extensions import csrf

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access your Clario workspace.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.workspace_routes import workspace_bp
    from routes.email_routes import email_bp
    from routes.security_routes import security_bp
    from routes.agent_routes import agent_bp
    from routes.payment_routes import payment_bp
    from routes.notification_routes import notification_bp
    from routes.settings_routes import settings_bp
    from routes.admin_routes import admin_bp
    from routes.report_routes import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(report_bp)

    # Global Context Processors for Jinja Templates
    @app.context_processor
    def inject_global_data():
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {
            'unread_notifications_count': unread_count,
            'app_name': 'CLARIO'
        }

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('base.html', error_title="403 Forbidden", error_message="You do not have administrative authorization to access this sector."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', error_title="404 Not Found", error_message="The requested workspace coordinate does not exist."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('base.html', error_title="500 Internal Error", error_message="The server encountered an unexpected situation. Security safeguards activated."), 500

    # Auto-initialize database and sample demo admin
    with app.app_context():
        db.create_all()
        # Seed initial admin user if not present
        if not User.query.filter_by(email='admin@clario.ai').first():
            admin_user = User(
                email='admin@clario.ai',
                username='admin',
                full_name='Clario Security Lead',
                role='admin',
                plan='PRO',
                subscription_status='active'
            )
            admin_user.set_password('Admin123!')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin account seeded: admin@clario.ai / Admin123!")

    # Safe startup verification for AI configuration
    gemini_key = app.config.get('GEMINI_API_KEY', '').strip()
    model_name = app.config.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    if gemini_key:
        masked = f"{gemini_key[:4]}...{gemini_key[-4:]}" if len(gemini_key) > 8 else "***"
        app.logger.info(f"[CLARIO STARTUP] Gemini AI Configuration: CONFIGURED (Key length: {len(gemini_key)}, Masked: {masked}, Model: {model_name})")
        print(f"[CLARIO STARTUP] Gemini AI Configuration: CONFIGURED (Masked: {masked}, Model: {model_name})")
    else:
        app.logger.warning("[CLARIO STARTUP] Gemini AI Configuration: NOT CONFIGURED (Running in Local Heuristic Mode)")
        print("[CLARIO STARTUP] Gemini AI Configuration: NOT CONFIGURED (Running in Local Heuristic Mode)")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
