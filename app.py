import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

from config import config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('database', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/mycodlab.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('MyCodeLab startup')

# Import models
from database.models import User, Question, CodeFile, Folder, Note, TestCase, Favorite, Trash, ActivityLog

# Import blueprints
from auth.routes import auth_bp
from questions.routes import questions_bp
from editor.routes import editor_bp
from executor.routes import executor_bp
from search.routes import search_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(questions_bp, url_prefix='/questions')
app.register_blueprint(editor_bp, url_prefix='/editor')
app.register_blueprint(executor_bp, url_prefix='/executor')
app.register_blueprint(search_bp, url_prefix='/search')

# Login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processors
@app.context_processor
def inject_user():
    return {'current_user': current_user}

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Professional dashboard"""
    user = current_user
    
    # Get statistics
    total_questions = Question.query.filter_by(user_id=user.id).count()
    total_code_files = CodeFile.query.filter_by(user_id=user.id).count()
    total_languages = db.session.query(CodeFile.language).filter_by(
        user_id=user.id
    ).distinct().count()
    
    # Get recent activity
    recent_activity = ActivityLog.query.filter_by(user_id=user.id).order_by(
        ActivityLog.created_at.desc()
    ).limit(10).all()
    
    # Get recent questions
    recent_questions = Question.query.filter_by(user_id=user.id).order_by(
        Question.created_at.desc()
    ).limit(5).all()
    
    # Get recent code files
    recent_files = CodeFile.query.filter_by(user_id=user.id).order_by(
        CodeFile.created_at.desc()
    ).limit(5).all()
    
    # Calculate coding days (unique days with activity)
    coding_days = db.session.query(
        db.func.count(db.distinct(db.func.date(ActivityLog.created_at)))
    ).filter_by(user_id=user.id).scalar() or 0
    
    return render_template('index.html',
                         user=user,
                         total_questions=total_questions,
                         total_code_files=total_code_files,
                         total_languages=total_languages,
                         coding_days=coding_days,
                         recent_activity=recent_activity,
                         recent_questions=recent_questions,
                         recent_files=recent_files)

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = current_user
    return render_template('profile/profile.html', user=user)

@app.route('/profile/stats')
@login_required
def profile_stats():
    """Coding statistics"""
    user = current_user
    
    # Questions stats
    questions_solved = Question.query.filter_by(user_id=user.id).count()
    code_files = CodeFile.query.filter_by(user_id=user.id).count()
    languages = db.session.query(CodeFile.language).filter_by(
        user_id=user.id
    ).distinct().count()
    
    # Activity by day
    activity_by_day = db.session.query(
        db.func.date(ActivityLog.created_at).label('day'),
        db.func.count(ActivityLog.id).label('count')
    ).filter_by(user_id=user.id).group_by(
        db.func.date(ActivityLog.created_at)
    ).all()
    
    # Language distribution
    language_dist = db.session.query(
        CodeFile.language,
        db.func.count(CodeFile.id).label('count')
    ).filter_by(user_id=user.id).group_by(CodeFile.language).all()
    
    # Difficulty distribution
    difficulty_dist = db.session.query(
        Question.difficulty,
        db.func.count(Question.id).label('count')
    ).filter_by(user_id=user.id).group_by(Question.difficulty).all()
    
    return render_template('profile/stats.html',
                         user=user,
                         questions_solved=questions_solved,
                         code_files=code_files,
                         languages=languages,
                         activity_by_day=activity_by_day,
                         language_dist=language_dist,
                         difficulty_dist=difficulty_dist)

@app.route('/profile/settings')
@login_required
def profile_settings():
    """User settings page"""
    user = current_user
    return render_template('profile/settings.html', user=user)

@app.route('/profile/theme/<theme>', methods=['POST'])
@login_required
def change_theme(theme):
    """Change theme preference"""
    user = current_user
    if theme in ['light', 'dark']:
        user.theme = theme
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Theme changed to {theme}'})
    return jsonify({'status': 'error', 'message': 'Invalid theme'}), 400

@app.route('/favorites')
@login_required
def favorites():
    """Favorite questions and files"""
    user = current_user
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return render_template('profile/favorites.html', user=user, favorites=favorites)

@app.route('/trash')
@login_required
def trash():
    """Trash page - view deleted items"""
    user = current_user
    trash_items = Trash.query.filter_by(user_id=user.id).order_by(
        Trash.deleted_at.desc()
    ).all()
    return render_template('trash.html', user=user, trash_items=trash_items)

@app.route('/trash/restore/<int:trash_id>', methods=['POST'])
@login_required
def restore_from_trash(trash_id):
    """Restore item from trash"""
    trash_item = Trash.query.get_or_404(trash_id)
    
    if trash_item.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Restore logic based on item type
    if trash_item.item_type == 'question':
        question = Question.query.get(trash_item.item_id)
        if question:
            question.deleted = False
            db.session.commit()
    
    db.session.delete(trash_item)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Item restored'})

@app.route('/trash/permanent/<int:trash_id>', methods=['DELETE'])
@login_required
def permanent_delete(trash_id):
    """Permanently delete item"""
    trash_item = Trash.query.get_or_404(trash_id)
    
    if trash_item.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    db.session.delete(trash_item)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Item permanently deleted'})

# API endpoint for getting stats
@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics"""
    user = current_user
    
    stats = {
        'questions': Question.query.filter_by(user_id=user.id).count(),
        'code_files': CodeFile.query.filter_by(user_id=user.id).count(),
        'languages': db.session.query(CodeFile.language).filter_by(
            user_id=user.id
        ).distinct().count(),
        'notes': Note.query.filter_by(user_id=user.id).count(),
        'favorites': Favorite.query.filter_by(user_id=user.id).count(),
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', True), host='0.0.0.0', port=5000)
