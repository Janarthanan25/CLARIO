import os
import re
from werkzeug.utils import secure_filename
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def allowed_file(filename, allowed_extensions):
    """Check if file has an authorized extension"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def sanitize_safe_filename(original_filename):
    """Sanitize filename to prevent directory traversal or script injection"""
    clean_name = secure_filename(original_filename)
    if not clean_name:
        clean_name = f"upload_{int(os.times()[4])}"
    return clean_name

def admin_required(f):
    """Decorator to enforce admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
