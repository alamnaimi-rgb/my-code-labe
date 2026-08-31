#!/usr/bin/env python
"""Initialize the database"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from database.models import User, Question, CodeFile, Folder, Note, TestCase, Favorite, Trash, ActivityLog, Execution

def init_db():
    """Initialize database with all tables"""
    with app.app_context():
        print('Creating database tables...')
        db.create_all()
        print('✅ Database initialized successfully!')
        print('Tables created:')
        print('  - users')
        print('  - questions')
        print('  - code_files')
        print('  - folders')
        print('  - notes')
        print('  - test_cases')
        print('  - executions')
        print('  - favorites')
        print('  - trash')
        print('  - activity_logs')

if __name__ == '__main__':
    init_db()
