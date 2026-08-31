from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import subprocess
import os
import tempfile
import signal
import json

from app import db
from database.models import CodeFile, Question, TestCase, Execution, ActivityLog
from executor.sandbox import execute_code
from executor.languages import get_compiler_command

executor_bp = Blueprint('executor', __name__)

@executor_bp.route('/run', methods=['POST'])
@login_required
def run_code():
    """Execute code and return output"""
    code_file_id = request.json.get('file_id')
    stdin_input = request.json.get('stdin', '')
    language = request.json.get('language')
    code = request.json.get('code')
    
    if not code_file_id and not code:
        return jsonify({'status': 'error', 'message': 'Code or file ID is required'}), 400
    
    # Get code file if ID provided
    if code_file_id:
        code_file = CodeFile.query.get_or_404(code_file_id)
        if code_file.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        code = code_file.content
        language = code_file.language
    else:
        if not language:
            return jsonify({'status': 'error', 'message': 'Language is required'}), 400
    
    try:
        # Execute code in sandbox
        result = execute_code(
            code=code,
            language=language,
            stdin=stdin_input,
            timeout=30
        )
        
        # Create execution record
        execution = Execution(
            code_file_id=code_file_id if code_file_id else None,
            user_id=current_user.id,
            status=result['status'],
            output=result.get('output', ''),
            error=result.get('error', ''),
            execution_time=result.get('time', 0),
            memory_used=result.get('memory', 0),
            stdin=stdin_input
        )
        
        db.session.add(execution)
        
        # Update code file execution count
        if code_file_id:
            code_file = CodeFile.query.get(code_file_id)
            code_file.execution_count += 1
            code_file.last_executed = datetime.utcnow()
            
            # Log activity
            activity = ActivityLog(
                user_id=current_user.id,
                action='executed',
                item_type='code_file',
                item_id=code_file.id,
                description=f'Executed file: {code_file.filename}'
            )
            db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'execution': {
                'status': result['status'],
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'execution_time': result.get('time', 0),
                'memory_used': result.get('memory', 0)
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@executor_bp.route('/test', methods=['POST'])
@login_required
def run_tests():
    """Run code against test cases"""
    code_file_id = request.json.get('file_id')
    question_id = request.json.get('question_id')
    code = request.json.get('code')
    language = request.json.get('language')
    
    if not code:
        return jsonify({'status': 'error', 'message': 'Code is required'}), 400
    
    if not question_id:
        return jsonify({'status': 'error', 'message': 'Question ID is required'}), 400
    
    # Get question
    question = Question.query.get_or_404(question_id)
    if question.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Get test cases
    test_cases = TestCase.query.filter_by(question_id=question_id).all()
    
    if not test_cases:
        return jsonify({
            'status': 'success',
            'message': 'No test cases found',
            'results': []
        })
    
    results = []
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            result = execute_code(
                code=code,
                language=language,
                stdin=test_case.input_data,
                timeout=10
            )
            
            # Compare output
            expected = test_case.expected_output.strip()
            actual = result.get('output', '').strip()
            is_passed = expected == actual
            
            if is_passed:
                passed += 1
            
            results.append({
                'test_case_id': test_case.id,
                'input': test_case.input_data,
                'expected': expected,
                'actual': actual,
                'passed': is_passed,
                'error': result.get('error', '')
            })
        
        except Exception as e:
            results.append({
                'test_case_id': test_case.id,
                'input': test_case.input_data,
                'expected': test_case.expected_output,
                'actual': '',
                'passed': False,
                'error': str(e)
            })
    
    # Create execution record
    execution = Execution(
        code_file_id=code_file_id if code_file_id else None,
        user_id=current_user.id,
        status='test_completed',
        test_cases_passed=passed,
        test_cases_total=total
    )
    
    db.session.add(execution)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'summary': {
            'passed': passed,
            'total': total,
            'percentage': (passed / total * 100) if total > 0 else 0
        },
        'results': results
    })

@executor_bp.route('/execution/<int:execution_id>')
@login_required
def get_execution(execution_id):
    """Get execution details"""
    execution = Execution.query.get_or_404(execution_id)
    
    if execution.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'status': 'success',
        'execution': {
            'id': execution.id,
            'status': execution.status,
            'output': execution.output,
            'error': execution.error,
            'execution_time': execution.execution_time,
            'memory_used': execution.memory_used,
            'test_cases_passed': execution.test_cases_passed,
            'test_cases_total': execution.test_cases_total,
            'created_at': execution.created_at.isoformat()
        }
    })

@executor_bp.route('/executions/<int:file_id>')
@login_required
def get_file_executions(file_id):
    """Get execution history for a file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    executions = Execution.query.filter_by(
        code_file_id=file_id
    ).order_by(Execution.created_at.desc()).limit(20).all()
    
    return jsonify({
        'status': 'success',
        'executions': [
            {
                'id': e.id,
                'status': e.status,
                'execution_time': e.execution_time,
                'created_at': e.created_at.isoformat()
            } for e in executions
        ]
    })

# API endpoint for supported languages
@executor_bp.route('/languages')
def get_languages():
    """Get list of supported languages"""
    return jsonify({
        'status': 'success',
        'languages': [
            {'id': 'c', 'name': 'C', 'extension': '.c'},
            {'id': 'cpp', 'name': 'C++', 'extension': '.cpp'},
            {'id': 'python', 'name': 'Python', 'extension': '.py'},
            {'id': 'java', 'name': 'Java', 'extension': '.java'},
            {'id': 'javascript', 'name': 'JavaScript', 'extension': '.js'},
            {'id': 'sql', 'name': 'SQL', 'extension': '.sql'}
        ]
    })
