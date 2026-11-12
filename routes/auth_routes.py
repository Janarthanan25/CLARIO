from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.models import User, Subscription
from services.audit_service import log_action
from services.notification_service import send_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_view'))
    if request.method == 'GET':
        return render_template('register.html')
    
    # Form submission or JSON
    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()

    if not email or not username or not password:
        if request.is_json:
            return jsonify({'success': False, 'error': 'All fields are required.'}), 400
        flash('All fields are required.', 'danger')
        return render_template('register.html')

    if len(password) < 6:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters.'}), 400
        flash('Password must be at least 6 characters.', 'danger')
        return render_template('register.html')

    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'success': False, 'error': 'An account with this email already exists.'}), 400
        flash('An account with this email already exists.', 'danger')
        return render_template('register.html')

    if User.query.filter_by(username=username).first():
        if request.is_json:
            return jsonify({'success': False, 'error': 'Username is already taken.'}), 400
        flash('Username is already taken.', 'danger')
        return render_template('register.html')

    # First user can be made admin, or if username is 'admin'
    role = 'admin' if (User.query.count() == 0 or username.lower() == 'admin') else 'user'

    new_user = User(
        email=email,
        username=username,
        full_name=full_name or username,
        role=role,
        plan='FREE',
        subscription_status='inactive'
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Create initial free subscription record
    free_sub = Subscription(user_id=new_user.id, plan_name='FREE', status='ACTIVE')
    db.session.add(free_sub)
    db.session.commit()

    # Welcome notification & Audit log
    send_notification(
        user_id=new_user.id,
        title="Welcome to CLARIO! 👋",
        message="Your intelligent AI Workspace is ready. Explore Document Intelligence, Smart Email Assistant, and Transaction Security AI.",
        category="system",
        link="/dashboard"
    )
    log_action(new_user.id, 'USER_REGISTERED', 'users', {'email': email, 'role': role})

    login_user(new_user)

    if request.is_json:
        return jsonify({'success': True, 'message': 'Account created successfully!', 'redirect': url_for('dashboard.dashboard_view')})
    flash('Account created successfully! Welcome to CLARIO.', 'success')
    return redirect(url_for('dashboard.dashboard_view'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_view'))
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json(silent=True) or request.form
    identifier = data.get('identifier', '').strip()  # email or username
    password = data.get('password', '').strip()
    remember = bool(data.get('remember', False))

    if not identifier or not password:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Please provide your email/username and password.'}), 400
        flash('Please provide your email/username and password.', 'danger')
        return render_template('login.html')

    user = User.query.filter((User.email == identifier.lower()) | (User.username == identifier)).first()

    if not user or not user.check_password(password):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials. Please verify your email and password.'}), 401
        flash('Invalid credentials. Please verify your email and password.', 'danger')
        return render_template('login.html')

    login_user(user, remember=remember)
    log_action(user.id, 'USER_LOGIN', 'users')

    next_page = request.args.get('next')
    redirect_target = next_page if (next_page and next_page.startswith('/')) else url_for('dashboard.dashboard_view')

    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged in successfully.', 'redirect': redirect_target})
    return redirect(redirect_target)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    uid = current_user.id
    log_action(uid, 'USER_LOGOUT', 'users')
    logout_user()
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out.'})
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))


# API Routes for Auth
@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    return register()

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    return login()

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    return logout()

@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })
