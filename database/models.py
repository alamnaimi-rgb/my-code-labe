from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    theme = db.Column(db.String(10), default='light')  # light or dark
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    questions = db.relationship('Question', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    code_files = db.relationship('CodeFile', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    trash_items = db.relationship('Trash', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Question(db.Model):
    """Question model"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), default='C')  # C, C++, Python, Java, JavaScript, SQL
    difficulty = db.Column(db.String(20), default='Easy')  # Easy, Medium, Hard
    topic = db.Column(db.String(100), index=True)
    tags = db.Column(db.String(500))  # Comma-separated tags
    expected_output = db.Column(db.Text)
    hints = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    code_files = db.relationship('CodeFile', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    test_cases = db.relationship('TestCase', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_tags(self):
        """Get tags as list"""
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    def set_tags(self, tags_list):
        """Set tags from list"""
        self.tags = ','.join(tags_list) if isinstance(tags_list, list) else tags_list
    
    def __repr__(self):
        return f'<Question {self.title}>'

class CodeFile(db.Model):
    """Code file model"""
    __tablename__ = 'code_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False, index=True)
    filepath = db.Column(db.String(500), nullable=False)
    content = db.Column(db.LongText, default='')
    language = db.Column(db.String(50), nullable=False)  # c, cpp, python, java, javascript, sql
    is_solution = db.Column(db.Boolean, default=False)  # Is this a solution to a question?
    is_starred = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_executed = db.Column(db.DateTime)
    execution_count = db.Column(db.Integer, default=0)
    
    # Relationships
    executions = db.relationship('Execution', backref='code_file', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CodeFile {self.filename}>'

class Folder(db.Model):
    """Folder model for organizing code files"""
    __tablename__ = 'folders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    code_files = db.relationship('CodeFile', backref='folder_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<Folder {self.name}>'

class Note(db.Model):
    """Note model"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    content = db.Column(db.LongText, nullable=False)
    note_type = db.Column(db.String(50), default='general')  # concept, important, mistake, solution, etc.
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.title}>'

class TestCase(db.Model):
    """Test case model"""
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    is_visible = db.Column(db.Boolean, default=True)  # Hidden or visible to user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TestCase for Q#{self.question_id}>'

class Execution(db.Model):
    """Code execution record"""
    __tablename__ = 'executions'
    
    id = db.Column(db.Integer, primary_key=True)
    code_file_id = db.Column(db.Integer, db.ForeignKey('code_files.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(50), default='pending')  # pending, running, success, error, timeout
    output = db.Column(db.LongText)
    error = db.Column(db.LongText)
    execution_time = db.Column(db.Float)  # in seconds
    memory_used = db.Column(db.Float)  # in MB
    stdin = db.Column(db.Text)  # Standard input
    test_cases_passed = db.Column(db.Integer, default=0)
    test_cases_total = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<Execution {self.id} - {self.status}>'

class Favorite(db.Model):
    """Favorite questions/files"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True, index=True)
    code_file_id = db.Column(db.Integer, db.ForeignKey('code_files.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    question = db.relationship('Question')
    code_file = db.relationship('CodeFile')
    
    def __repr__(self):
        return f'<Favorite {self.id}>'

class Trash(db.Model):
    """Trash/Recycle bin model"""
    __tablename__ = 'trash'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    item_type = db.Column(db.String(50), nullable=False)  # question, file, note, folder
    item_id = db.Column(db.Integer, nullable=False)
    item_data = db.Column(db.LongText)  # JSON backup of deleted item
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Trash {self.item_type}#{self.item_id}>'

class ActivityLog(db.Model):
    """Activity log for user tracking"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # created, updated, deleted, executed, etc.
    item_type = db.Column(db.String(50))  # question, code_file, note, etc.
    item_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    details = db.Column(db.Text)  # JSON details
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.action} on {self.item_type}>'
