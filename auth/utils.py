from flask_mail import Mail, Message
from flask import current_app, url_for
import secrets
from datetime import datetime, timedelta

mail = Mail()

def send_reset_email(user):
    """Send password reset email"""
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    from app import db
    db.session.commit()
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message(
        subject='Password Reset Request',
        recipients=[user.email],
        body=f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
The link will expire in 1 hour.
'''
    )
    
    mail.send(msg)

def send_welcome_email(user):
    """Send welcome email to new user"""
    msg = Message(
        subject='Welcome to MyCodeLab!',
        recipients=[user.email],
        body=f'''Welcome to MyCodeLab, {user.full_name}!

Your account has been created successfully.
Start coding, save your progress, and practice programming!

Happy Coding!
MyCodeLab Team
'''
    )
    
    mail.send(msg)
