from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from app import db
from database.models import CodeFile, Folder, Question, ActivityLog, Trash
from editor.utils import allowed_file, get_file_path, create_file_structure

editor_bp = Blueprint('editor', __name__)

@editor_bp.route('/')
@login_required
def index():
    """Code editor main page"""
    # Get root folders
    folders = Folder.query.filter_by(user_id=current_user.id, parent_id=None).all()
    
    # Get recent files
    recent_files = CodeFile.query.filter_by(
        user_id=current_user.id,
        deleted=False
    ).order_by(CodeFile.updated_at.desc()).limit(10).all()
    
    return render_template('editor/index.html',
                         folders=folders,
                         recent_files=recent_files)

@editor_bp.route('/new', methods=['POST'])
@login_required
def create_file():
    """Create new code file"""
    filename = request.form.get('filename', '').strip()
    language = request.form.get('language', 'c')
    folder_id = request.form.get('folder_id', type=int)
    question_id = request.form.get('question_id', type=int)
    
    errors = []
    
    if not filename:
        errors.append('Filename is required')
    
    # Validate filename
    filename = secure_filename(filename)
    if not filename:
        errors.append('Invalid filename')
    
    # Get extension based on language
    extensions = {
        'c': '.c',
        'cpp': '.cpp',
        'python': '.py',
        'java': '.java',
        'javascript': '.js',
        'sql': '.sql'
    }
    
    ext = extensions.get(language, '.txt')
    if not filename.endswith(ext):
        filename = filename + ext
    
    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400
    
    # Check folder ownership if provided
    if folder_id:
        folder = Folder.query.get(folder_id)
        if not folder or folder.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Invalid folder'}), 403
    
    # Check question ownership if provided
    if question_id:
        question = Question.query.get(question_id)
        if not question or question.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Invalid question'}), 403
    
    # Create file
    filepath = get_file_path(current_user.id, filename, folder_id)
    
    code_file = CodeFile(
        user_id=current_user.id,
        filename=filename,
        filepath=filepath,
        language=language,
        question_id=question_id,
        folder_id=folder_id,
        content=''
    )
    
    db.session.add(code_file)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='created',
        item_type='code_file',
        item_id=code_file.id,
        description=f'Created file: {filename}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'File created',
        'file': {
            'id': code_file.id,
            'filename': code_file.filename,
            'language': code_file.language,
            'content': code_file.content
        }
    })

@editor_bp.route('/<int:file_id>')
@login_required
def edit_file(file_id):
    """Open file in editor"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        flash('You do not have permission to edit this file', 'error')
        return redirect(url_for('editor.index'))
    
    # Get all files in folder
    if code_file.folder_id:
        related_files = CodeFile.query.filter_by(
            folder_id=code_file.folder_id,
            deleted=False
        ).all()
    else:
        related_files = CodeFile.query.filter_by(
            user_id=current_user.id,
            folder_id=None,
            deleted=False
        ).limit(20).all()
    
    return render_template('editor/editor.html',
                         file=code_file,
                         related_files=related_files)

@editor_bp.route('/file/<int:file_id>/content', methods=['GET'])
@login_required
def get_file_content(file_id):
    """Get file content"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'status': 'success',
        'content': code_file.content,
        'filename': code_file.filename,
        'language': code_file.language
    })

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
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='updated',
        item_type='code_file',
        item_id=code_file.id,
        description=f'Updated file: {code_file.filename}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'File saved'
    })

@editor_bp.route('/file/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    """Rename file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    new_name = request.json.get('name', '').strip()
    new_name = secure_filename(new_name)
    
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Invalid filename'}), 400
    
    code_file.filename = new_name
    code_file.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'File renamed',
        'filename': code_file.filename
    })

@editor_bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete file (soft delete)"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Move to trash
    trash_item = Trash(
        user_id=current_user.id,
        item_type='code_file',
        item_id=code_file.id,
        item_data=json.dumps({
            'filename': code_file.filename,
            'content': code_file.content
        })
    )
    
    code_file.deleted = True
    db.session.add(trash_item)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'File moved to trash'
    })

@editor_bp.route('/file/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """Download file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        flash('You do not have permission to download this file', 'error')
        return redirect(url_for('editor.index'))
    
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(code_file.content)
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=code_file.filename
    )

# FOLDER MANAGEMENT

@editor_bp.route('/folder/create', methods=['POST'])
@login_required
def create_folder():
    """Create new folder"""
    name = request.form.get('name', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Folder name is required'}), 400
    
    # Check parent folder ownership
    if parent_id:
        parent = Folder.query.get(parent_id)
        if not parent or parent.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Invalid parent folder'}), 403
    
    folder = Folder(
        user_id=current_user.id,
        parent_id=parent_id,
        name=name
    )
    
    db.session.add(folder)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Folder created',
        'folder': {
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id
        }
    })

@editor_bp.route('/folder/<int:folder_id>')
@login_required
def view_folder(folder_id):
    """View folder contents"""
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        flash('You do not have permission to view this folder', 'error')
        return redirect(url_for('editor.index'))
    
    # Get subfolders
    subfolders = Folder.query.filter_by(
        parent_id=folder_id,
        user_id=current_user.id
    ).all()
    
    # Get files in folder
    files = CodeFile.query.filter_by(
        folder_id=folder_id,
        user_id=current_user.id,
        deleted=False
    ).all()
    
    return render_template('editor/folder.html',
                         folder=folder,
                         subfolders=subfolders,
                         files=files)

@editor_bp.route('/folder/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    """Rename folder"""
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    new_name = request.json.get('name', '').strip()
    
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Folder name is required'}), 400
    
    folder.name = new_name
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Folder renamed',
        'name': folder.name
    })

@editor_bp.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    """Delete folder (with all files)"""
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Mark all files in folder as deleted
    files = CodeFile.query.filter_by(folder_id=folder_id).all()
    for f in files:
        f.deleted = True
    
    db.session.delete(folder)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Folder deleted'
    })

# FILE EXPLORER

@editor_bp.route('/explorer')
@login_required
def file_explorer():
    """File explorer view"""
    # Get all folders
    folders = Folder.query.filter_by(user_id=current_user.id).all()
    
    # Get all files
    files = CodeFile.query.filter_by(
        user_id=current_user.id,
        deleted=False
    ).all()
    
    return render_template('editor/file_explorer.html',
                         folders=folders,
                         files=files)

# API endpoint for file structure
@editor_bp.route('/api/structure')
@login_required
def api_structure():
    """Get file structure as JSON"""
    folders = Folder.query.filter_by(user_id=current_user.id, parent_id=None).all()
    files = CodeFile.query.filter_by(
        user_id=current_user.id,
        folder_id=None,
        deleted=False
    ).all()
    
    def folder_to_dict(folder):
        return {
            'id': folder.id,
            'name': folder.name,
            'type': 'folder',
            'children': [
                folder_to_dict(f) for f in Folder.query.filter_by(parent_id=folder.id).all()
            ] + [
                {
                    'id': f.id,
                    'name': f.filename,
                    'type': 'file',
                    'language': f.language
                } for f in CodeFile.query.filter_by(folder_id=folder.id, deleted=False).all()
            ]
        }
    
    structure = {
        'folders': [folder_to_dict(f) for f in folders],
        'files': [
            {
                'id': f.id,
                'name': f.filename,
                'type': 'file',
                'language': f.language
            } for f in files
        ]
    }
    
    return jsonify(structure)
