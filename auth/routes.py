from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, app
from database.models import User, ActivityLog
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Validate password strength"""
    return len(password) >= 6

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        
        if not email or not is_valid_email(email):
            errors.append('Invalid email address')
        
        if not password or not is_valid_password(password):
            errors.append('Password must be at least 6 characters')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('auth.register'))
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            theme='light'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action='registered',
            description=f'User {username} registered successfully'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is disabled', 'error')
                return redirect(url_for('auth.login'))
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=bool(remember_me))
            
            # Log activity
            activity = ActivityLog(
                user_id=user.id,
                action='login',
                description=f'User {user.username} logged in'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user = current_user
    username = user.username
    
    # Log activity
    activity = ActivityLog(
        user_id=user.id,
        action='logout',
        description=f'User {user.username} logged out'
    )
    db.session.add(activity)
    db.session.commit()
    
    logout_user()
    flash(f'Goodbye, {username}! See you soon.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password"""
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    user = current_user
    
    if not user.check_password(old_password):
        return jsonify({'status': 'error', 'message': 'Old password is incorrect'}), 400
    
    if not is_valid_password(new_password):
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400
    
    if new_password != confirm_password:
        return jsonify({'status': 'error', 'message': 'Passwords do not match'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    activity = ActivityLog(
        user_id=user.id,
        action='password_changed',
        description='User changed password'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Password changed successfully'})
