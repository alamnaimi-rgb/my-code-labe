from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db, app
from database.models import CodeFile, Folder, Question, ActivityLog
from datetime import datetime
import os
import json
from pathlib import Path

editor_bp = Blueprint('editor', __name__)

ALLOWED_EXTENSIONS = {'c', 'cpp', 'py', 'java', 'js', 'sql', 'txt', 'h', 'hpp', 'java'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_language_from_extension(filename):
    """Get programming language from file extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'txt'
    
    ext_to_lang = {
        'c': 'c',
        'cpp': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'py': 'python',
        'java': 'java',
        'js': 'javascript',
        'sql': 'sql',
        'txt': 'text'
    }
    
    return ext_to_lang.get(ext, 'text')

@editor_bp.route('/')
@login_required
def index():
    """Editor home page"""
    user = current_user
    
    # Get user's code files and folders
    code_files = CodeFile.query.filter_by(user_id=user.id, folder_id=None, deleted=False).all()
    folders = Folder.query.filter_by(user_id=user.id, parent_id=None).all()
    
    return render_template('editor/index.html',
                         code_files=code_files,
                         folders=folders)

@editor_bp.route('/file/<int:file_id>')
@login_required
def open_file(file_id):
    """Open file in editor"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        flash('You do not have access to this file', 'error')
        return redirect(url_for('editor.index'))
    
    # Get related question if exists
    question = Question.query.get(code_file.question_id) if code_file.question_id else None
    
    return render_template('editor/file.html',
                         code_file=code_file,
                         question=question)

@editor_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_file():
    """Create new code file"""
    if request.method == 'POST':
        filename = request.form.get('filename', '').strip()
        content = request.form.get('content', '')
        folder_id = request.form.get('folder_id', type=int) or None
        question_id = request.form.get('question_id', type=int) or None
        
        if not filename:
            flash('Filename is required', 'error')
            return redirect(url_for('editor.new_file'))
        
        if not allowed_file(filename):
            flash('File type not allowed', 'error')
            return redirect(url_for('editor.new_file'))
        
        language = get_language_from_extension(filename)
        filepath = f"/code/{current_user.id}/{filename}"
        
        code_file = CodeFile(
            user_id=current_user.id,
            filename=filename,
            filepath=filepath,
            content=content,
            language=language,
            folder_id=folder_id,
            question_id=question_id
        )
        
        db.session.add(code_file)
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action='created',
            item_type='code_file',
            item_id=code_file.id,
            description=f'Created code file: {filename}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Code file created successfully!', 'success')
        return redirect(url_for('editor.open_file', file_id=code_file.id))
    
    folders = Folder.query.filter_by(user_id=current_user.id).all()
    questions = Question.query.filter_by(user_id=current_user.id, deleted=False).all()
    
    return render_template('editor/new_file.html',
                         folders=folders,
                         questions=questions)

@editor_bp.route('/file/<int:file_id>/save', methods=['POST'])
@login_required
def save_file(file_id):
    """Save file content"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    content = request.json.get('content', '')
    
    code_file.content = content
    code_file.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Log activity (but not every keystroke, only explicit saves)
    activity = ActivityLog(
        user_id=current_user.id,
        action='saved',
        item_type='code_file',
        item_id=code_file.id,
        description=f'Saved code file: {code_file.filename}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'File saved successfully'})

@editor_bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete code file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    filename = code_file.filename
    code_file.deleted = True
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='deleted',
        item_type='code_file',
        item_id=code_file.id,
        description=f'Deleted code file: {filename}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'File deleted'})

@editor_bp.route('/folder/new', methods=['POST'])
@login_required
def new_folder():
    """Create new folder"""
    data = request.json
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id', type=int) or None
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Folder name is required'}), 400
    
    folder = Folder(
        user_id=current_user.id,
        name=name,
        parent_id=parent_id
    )
    
    db.session.add(folder)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='created',
        item_type='folder',
        item_id=folder.id,
        description=f'Created folder: {name}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'status': 'success', 'folder_id': folder.id, 'message': 'Folder created'})

@editor_bp.route('/folder/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    """Rename folder"""
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    data = request.json
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Folder name is required'}), 400
    
    folder.name = new_name
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Folder renamed'})

@editor_bp.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    """Delete folder"""
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    folder_name = folder.name
    
    # Delete all files in folder
    CodeFile.query.filter_by(folder_id=folder_id).update({'deleted': True})
    
    # Delete folder
    db.session.delete(folder)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='deleted',
        item_type='folder',
        item_id=folder_id,
        description=f'Deleted folder: {folder_name}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Folder deleted'})

@editor_bp.route('/file/<int:file_id>/download')
@login_required
def download_file(file_id):
    """Download code file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        flash('You do not have access to this file', 'error')
        return redirect(url_for('editor.index'))
    
    # Create temporary file and send it
    from io import BytesIO
    
    file_content = BytesIO(code_file.content.encode('utf-8'))
    
    return send_file(
        file_content,
        as_attachment=True,
        download_name=code_file.filename,
        mimetype='text/plain'
    )
