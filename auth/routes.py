from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import re

from app import db
from database.models import User, ActivityLog
from auth.utils import send_reset_email

auth_bp = Blueprint('auth', __name__)

# Email validation regex
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_email(email):
    """Validate email format"""
    return re.match(EMAIL_REGEX, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        elif len(username) > 20:
            errors.append('Username must be at most 20 characters long')
        elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append('Username can only contain letters, numbers, underscores, and hyphens')
        
        if not email:
            errors.append('Email is required')
        elif not validate_email(email):
            errors.append('Invalid email address')
        
        if not password:
            errors.append('Password is required')
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if not full_name:
            errors.append('Full name is required')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action='registered',
            item_type='user',
            description=f'User {username} registered successfully'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username_or_email or not password:
            flash('Username/Email and password are required', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            
            # Log activity
            activity = ActivityLog(
                user_id=user.id,
                action='logged_in',
                item_type='user',
                description=f'User {user.username} logged in'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or url_has_allowed_host_and_scheme(next_page):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    user_id = current_user.id
    
    logout_user()
    
    # Log activity
    activity = ActivityLog(
        user_id=user_id,
        action='logged_out',
        item_type='user',
        description=f'User {username} logged out'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email is required', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            send_reset_email(user)
            flash('Check your email for a link to reset your password', 'success')
        else:
            # Don't reveal if email exists
            flash('Check your email for a link to reset your password', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        if not current_user.check_password(current_password):
            errors.append('Current password is incorrect')
        
        if not new_password:
            errors.append('New password is required')
        else:
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                errors.append(msg)
        
        if new_password != confirm_password:
            errors.append('New passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/change_password.html')

# API endpoint for checking username availability
@auth_bp.route('/api/check-username/<username>')
def check_username(username):
    """Check if username is available"""
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username too short'})
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return jsonify({'available': False, 'message': 'Invalid username format'})
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        return jsonify({'available': False, 'message': 'Username already taken'})
    else:
        return jsonify({'available': True, 'message': 'Username available'})

# API endpoint for checking email availability
@auth_bp.route('/api/check-email/<email>')
def check_email(email):
    """Check if email is available"""
    if not validate_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    user = User.query.filter_by(email=email.lower()).first()
    
    if user:
        return jsonify({'available': False, 'message': 'Email already registered'})
    else:
        return jsonify({'available': True, 'message': 'Email available'})

def url_has_allowed_host_and_scheme(url, allowed_hosts=None):
    """Security check for redirects"""
    if allowed_hosts is None:
        allowed_hosts = {}
    
    if not url:
        return False
    
    if url.startswith('//'):
        return False
    
    return True
