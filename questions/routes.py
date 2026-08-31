from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import Question, CodeFile, Note, TestCase, Favorite, Trash, ActivityLog
from datetime import datetime
import json

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/')
@questions_bp.route('/list')
@login_required
def list_questions():
    """List all questions"""
    page = request.args.get('page', 1, type=int)
    difficulty = request.args.get('difficulty', '', type=str)
    language = request.args.get('language', '', type=str)
    topic = request.args.get('topic', '', type=str)
    
    query = Question.query.filter_by(user_id=current_user.id, deleted=False)
    
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if language:
        query = query.filter_by(language=language)
    if topic:
        query = query.filter_by(topic=topic)
    
    questions = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=20)
    
    # Get unique values for filters
    difficulties = db.session.query(Question.difficulty).filter_by(
        user_id=current_user.id, deleted=False
    ).distinct().all()
    languages = db.session.query(Question.language).filter_by(
        user_id=current_user.id, deleted=False
    ).distinct().all()
    topics = db.session.query(Question.topic).filter_by(
        user_id=current_user.id, deleted=False
    ).distinct().all()
    
    return render_template('questions/list.html',
                         questions=questions,
                         difficulties=[d[0] for d in difficulties if d[0]],
                         languages=[l[0] for l in languages if l[0]],
                         topics=[t[0] for t in topics if t[0]])

@questions_bp.route('/view/<int:question_id>')
@login_required
def view_question(question_id):
    """View single question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        flash('You do not have access to this question', 'error')
        return redirect(url_for('questions.list_questions'))
    
    # Get related code files
    code_files = CodeFile.query.filter_by(question_id=question_id, user_id=current_user.id).all()
    
    # Get related notes
    notes = Note.query.filter_by(question_id=question_id, user_id=current_user.id).all()
    
    # Get test cases
    test_cases = TestCase.query.filter_by(question_id=question_id).all()
    
    # Check if favorited
    is_favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first() is not None
    
    return render_template('questions/view.html',
                         question=question,
                         code_files=code_files,
                         notes=notes,
                         test_cases=test_cases,
                         is_favorite=is_favorite)

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
        
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('questions.add_question'))
        
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
        
        flash('Question created successfully!', 'success')
        return redirect(url_for('questions.view_question', question_id=question.id))
    
    return render_template('questions/add.html')

@questions_bp.route('/edit/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        flash('You do not have access to edit this question', 'error')
        return redirect(url_for('questions.list_questions'))
    
    if request.method == 'POST':
        question.title = request.form.get('title', '').strip()
        question.description = request.form.get('description', '').strip()
        question.language = request.form.get('language', 'C')
        question.difficulty = request.form.get('difficulty', 'Easy')
        question.topic = request.form.get('topic', '').strip()
        question.tags = request.form.get('tags', '').strip()
        question.expected_output = request.form.get('expected_output', '').strip()
        question.hints = request.form.get('hints', '').strip()
        question.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action='updated',
            item_type='question',
            item_id=question.id,
            description=f'Updated question: {question.title}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('questions.view_question', question_id=question.id))
    
    return render_template('questions/edit.html', question=question)

@questions_bp.route('/delete/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete question (move to trash)"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Move to trash
    trash = Trash(
        user_id=current_user.id,
        item_type='question',
        item_id=question.id,
        item_data=json.dumps({
            'title': question.title,
            'description': question.description
        })
    )
    db.session.add(trash)
    
    # Mark as deleted
    question.deleted = True
    
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
    return jsonify({'status': 'success'})

@questions_bp.route('/<int:question_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(question_id):
    """Toggle favorite status"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        status = 'unfavorited'
    else:
        favorite = Favorite(
            user_id=current_user.id,
            question_id=question_id
        )
        db.session.add(favorite)
        status = 'favorited'
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Question {status}'})
