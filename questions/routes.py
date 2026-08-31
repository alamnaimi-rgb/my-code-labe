from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import json

from app import db
from database.models import Question, Note, TestCase, Favorite, Trash, ActivityLog

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/')
@login_required
def list_questions():
    """List all questions for current user"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    language = request.args.get('language')
    difficulty = request.args.get('difficulty')
    topic = request.args.get('topic')
    search = request.args.get('search')
    
    query = Question.query.filter_by(user_id=current_user.id, deleted=False)
    
    if language:
        query = query.filter_by(language=language)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if topic:
        query = query.filter_by(topic=topic)
    if search:
        query = query.filter(Question.title.ilike(f'%{search}%') | 
                           Question.description.ilike(f'%{search}%'))
    
    questions = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique values for filters
    languages = db.session.query(Question.language).filter_by(
        user_id=current_user.id
    ).distinct().all()
    difficulties = db.session.query(Question.difficulty).filter_by(
        user_id=current_user.id
    ).distinct().all()
    topics = db.session.query(Question.topic).filter_by(
        user_id=current_user.id
    ).distinct().all()
    
    return render_template('questions/list.html',
                         questions=questions,
                         languages=[l[0] for l in languages],
                         difficulties=[d[0] for d in difficulties],
                         topics=[t[0] for t in topics if t[0]],
                         search=search,
                         language=language,
                         difficulty=difficulty,
                         topic=topic)

@questions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_question():
    """Add new question"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        language = request.form.get('language', 'C')
        difficulty = request.form.get('difficulty', 'Easy')
        topic = request.form.get('topic', '').strip()
        tags = request.form.get('tags', '').strip()
        expected_output = request.form.get('expected_output', '').strip()
        hints = request.form.get('hints', '').strip()
        
        errors = []
        
        if not title:
            errors.append('Title is required')
        if not description:
            errors.append('Description is required')
        if difficulty not in ['Easy', 'Medium', 'Hard']:
            errors.append('Invalid difficulty level')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('questions/add.html')
        
        question = Question(
            user_id=current_user.id,
            title=title,
            description=description,
            language=language,
            difficulty=difficulty,
            topic=topic,
            tags=tags,
            expected_output=expected_output,
            hints=hints
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action='created',
            item_type='question',
            item_id=question.id,
            description=f'Created question: {title}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('questions.view_question', question_id=question.id))
    
    return render_template('questions/add.html')

@questions_bp.route('/<int:question_id>')
@login_required
def view_question(question_id):
    """View single question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        flash('You do not have permission to view this question', 'error')
        return redirect(url_for('questions.list_questions'))
    
    # Get related data
    notes = Note.query.filter_by(question_id=question_id).all()
    test_cases = TestCase.query.filter_by(question_id=question_id).all()
    is_favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first() is not None
    
    return render_template('questions/view.html',
                         question=question,
                         notes=notes,
                         test_cases=test_cases,
                         is_favorite=is_favorite)

@questions_bp.route('/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        flash('You do not have permission to edit this question', 'error')
        return redirect(url_for('questions.list_questions'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        language = request.form.get('language', question.language)
        difficulty = request.form.get('difficulty', question.difficulty)
        topic = request.form.get('topic', '').strip()
        tags = request.form.get('tags', '').strip()
        expected_output = request.form.get('expected_output', '').strip()
        hints = request.form.get('hints', '').strip()
        
        errors = []
        
        if not title:
            errors.append('Title is required')
        if not description:
            errors.append('Description is required')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('questions/edit.html', question=question)
        
        question.title = title
        question.description = description
        question.language = language
        question.difficulty = difficulty
        question.topic = topic
        question.tags = tags
        question.expected_output = expected_output
        question.hints = hints
        question.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action='updated',
            item_type='question',
            item_id=question.id,
            description=f'Updated question: {title}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('questions.view_question', question_id=question.id))
    
    return render_template('questions/edit.html', question=question)

@questions_bp.route('/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete question (soft delete to trash)"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Move to trash
    trash_item = Trash(
        user_id=current_user.id,
        item_type='question',
        item_id=question.id,
        item_data=json.dumps({
            'title': question.title,
            'description': question.description
        })
    )
    
    question.deleted = True
    db.session.add(trash_item)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action='deleted',
        item_type='question',
        item_id=question.id,
        description=f'Deleted question: {question.title}'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('Question moved to trash', 'success')
    return redirect(url_for('questions.list_questions'))

@questions_bp.route('/<int:question_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(question_id):
    """Toggle favorite for question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        is_favorite = False
        message = 'Removed from favorites'
    else:
        favorite = Favorite(
            user_id=current_user.id,
            question_id=question_id
        )
        db.session.add(favorite)
        is_favorite = True
        message = 'Added to favorites'
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': message,
        'is_favorite': is_favorite
    })

@questions_bp.route('/<int:question_id>/test-case', methods=['POST'])
@login_required
def add_test_case(question_id):
    """Add test case to question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    input_data = request.form.get('input', '').strip()
    expected_output = request.form.get('expected_output', '').strip()
    description = request.form.get('description', '').strip()
    is_visible = request.form.get('is_visible', 'true').lower() == 'true'
    
    if not input_data or not expected_output:
        return jsonify({'status': 'error', 'message': 'Input and output are required'}), 400
    
    test_case = TestCase(
        question_id=question_id,
        input_data=input_data,
        expected_output=expected_output,
        description=description,
        is_visible=is_visible
    )
    
    db.session.add(test_case)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Test case added',
        'test_case': {
            'id': test_case.id,
            'input': test_case.input_data,
            'expected_output': test_case.expected_output,
            'description': test_case.description
        }
    })

@questions_bp.route('/test-case/<int:test_case_id>/delete', methods=['DELETE'])
@login_required
def delete_test_case(test_case_id):
    """Delete test case"""
    test_case = TestCase.query.get_or_404(test_case_id)
    question = test_case.question
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    db.session.delete(test_case)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Test case deleted'})

@questions_bp.route('/<int:question_id>/note', methods=['POST'])
@login_required
def add_note(question_id):
    """Add note to question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    note_type = request.form.get('type', 'general')
    
    if not title or not content:
        return jsonify({'status': 'error', 'message': 'Title and content are required'}), 400
    
    note = Note(
        user_id=current_user.id,
        question_id=question_id,
        title=title,
        content=content,
        note_type=note_type
    )
    
    db.session.add(note)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Note added',
        'note': {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'type': note.note_type
        }
    })

# API endpoint for quick stats
@questions_bp.route('/api/stats')
@login_required
def api_question_stats():
    """Get question statistics"""
    total = Question.query.filter_by(user_id=current_user.id, deleted=False).count()
    
    by_difficulty = db.session.query(
        Question.difficulty,
        db.func.count(Question.id)
    ).filter_by(user_id=current_user.id, deleted=False).group_by(
        Question.difficulty
    ).all()
    
    by_language = db.session.query(
        Question.language,
        db.func.count(Question.id)
    ).filter_by(user_id=current_user.id, deleted=False).group_by(
        Question.language
    ).all()
    
    return jsonify({
        'total': total,
        'by_difficulty': {d[0]: d[1] for d in by_difficulty},
        'by_language': {l[0]: l[1] for l in by_language}
    })
