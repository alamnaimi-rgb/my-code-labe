from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from database.models import Question, CodeFile, Note, Folder

search_bp = Blueprint('search', __name__)

@search_bp.route('/global', methods=['GET'])
@login_required
def global_search():
    """Global search across all content"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, questions, files, notes
    limit = request.args.get('limit', 20, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'status': 'error', 'message': 'Query must be at least 2 characters'}), 400
    
    results = {'questions': [], 'files': [], 'notes': [], 'folders': []}
    
    search_pattern = f'%{query}%'
    
    # Search questions
    if search_type in ['all', 'questions']:
        questions = Question.query.filter(
            Question.user_id == current_user.id,
            Question.deleted == False,
            or_(
                Question.title.ilike(search_pattern),
                Question.description.ilike(search_pattern),
                Question.tags.ilike(search_pattern)
            )
        ).limit(limit).all()
        
        results['questions'] = [
            {
                'id': q.id,
                'title': q.title,
                'language': q.language,
                'difficulty': q.difficulty,
                'topic': q.topic,
                'created_at': q.created_at.isoformat()
            } for q in questions
        ]
    
    # Search code files
    if search_type in ['all', 'files']:
        files = CodeFile.query.filter(
            CodeFile.user_id == current_user.id,
            CodeFile.deleted == False,
            or_(
                CodeFile.filename.ilike(search_pattern),
                CodeFile.content.ilike(search_pattern)
            )
        ).limit(limit).all()
        
        results['files'] = [
            {
                'id': f.id,
                'filename': f.filename,
                'language': f.language,
                'folder_id': f.folder_id,
                'updated_at': f.updated_at.isoformat()
            } for f in files
        ]
    
    # Search notes
    if search_type in ['all', 'notes']:
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            or_(
                Note.title.ilike(search_pattern),
                Note.content.ilike(search_pattern)
            )
        ).limit(limit).all()
        
        results['notes'] = [
            {
                'id': n.id,
                'title': n.title,
                'note_type': n.note_type,
                'question_id': n.question_id,
                'created_at': n.created_at.isoformat()
            } for n in notes
        ]
    
    # Search folders
    if search_type in ['all', 'folders']:
        folders = Folder.query.filter(
            Folder.user_id == current_user.id,
            Folder.name.ilike(search_pattern)
        ).limit(limit).all()
        
        results['folders'] = [
            {
                'id': f.id,
                'name': f.name,
                'parent_id': f.parent_id
            } for f in folders
        ]
    
    # Remove empty results
    results = {k: v for k, v in results.items() if v}
    
    return jsonify({
        'status': 'success',
        'query': query,
        'results': results
    })

@search_bp.route('/advanced', methods=['GET'])
@login_required
def advanced_search():
    """Advanced search with filters"""
    query = request.args.get('q', '').strip()
    language = request.args.get('language')
    difficulty = request.args.get('difficulty')
    topic = request.args.get('topic')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_type = request.args.get('type', 'questions')
    
    if not query or len(query) < 2:
        return jsonify({'status': 'error', 'message': 'Query must be at least 2 characters'}), 400
    
    search_pattern = f'%{query}%'
    base_query = Question.query.filter(
        Question.user_id == current_user.id,
        Question.deleted == False,
        or_(
            Question.title.ilike(search_pattern),
            Question.description.ilike(search_pattern),
            Question.tags.ilike(search_pattern)
        )
    )
    
    # Apply filters
    if language:
        base_query = base_query.filter_by(language=language)
    if difficulty:
        base_query = base_query.filter_by(difficulty=difficulty)
    if topic:
        base_query = base_query.filter_by(topic=topic)
    
    if date_from:
        from datetime import datetime
        date_from = datetime.fromisoformat(date_from)
        base_query = base_query.filter(Question.created_at >= date_from)
    
    if date_to:
        from datetime import datetime
        date_to = datetime.fromisoformat(date_to)
        base_query = base_query.filter(Question.created_at <= date_to)
    
    questions = base_query.all()
    
    return jsonify({
        'status': 'success',
        'query': query,
        'count': len(questions),
        'results': [
            {
                'id': q.id,
                'title': q.title,
                'language': q.language,
                'difficulty': q.difficulty,
                'topic': q.topic,
                'created_at': q.created_at.isoformat()
            } for q in questions
        ]
    })

@search_bp.route('/suggestions')
@login_required
def search_suggestions():
    """Get search suggestions based on user's data"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 1:
        return jsonify({'suggestions': []})
    
    search_pattern = f'%{query}%'
    
    # Get unique titles from questions
    question_titles = Question.query.filter(
        Question.user_id == current_user.id,
        Question.title.ilike(search_pattern)
    ).with_entities(Question.title).distinct().limit(5).all()
    
    # Get unique filenames
    filenames = CodeFile.query.filter(
        CodeFile.user_id == current_user.id,
        CodeFile.filename.ilike(search_pattern)
    ).with_entities(CodeFile.filename).distinct().limit(5).all()
    
    # Get unique tags
    tags = Question.query.filter(
        Question.user_id == current_user.id,
        Question.tags.ilike(search_pattern)
    ).with_entities(Question.tags).distinct().limit(5).all()
    
    suggestions = []
    suggestions.extend([t[0] for t in question_titles])
    suggestions.extend([f[0] for f in filenames])
    suggestions.extend([t[0] for t in tags if t[0]])
    
    return jsonify({'suggestions': list(set(suggestions))[:10]})
