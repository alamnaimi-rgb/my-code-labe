import subprocess
import tempfile
import os
import signal
from datetime import datetime

def execute_code(code, language, stdin='', timeout=30):
    """
    Execute code in a sandboxed environment
    Returns: {'status': 'success'|'error'|'timeout', 'output': '', 'error': '', 'time': 0.0}
    """
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=get_file_extension(language), delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        start_time = datetime.utcnow()
        
        # Get compile and run commands
        compile_cmd, run_cmd = get_commands(language, temp_file)
        
        # Compile if needed
        if compile_cmd:
            compile_result = subprocess.run(
                compile_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if compile_result.returncode != 0:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                return {
                    'status': 'error',
                    'output': '',
                    'error': compile_result.stderr,
                    'time': execution_time
                }
        
        # Run code
        process = subprocess.Popen(
            run_cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        try:
            output, error = process.communicate(input=stdin, timeout=timeout)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cleanup
            cleanup_temp_files(language, temp_file)
            
            return {
                'status': 'success' if process.returncode == 0 else 'error',
                'output': output,
                'error': error,
                'time': execution_time
            }
        
        except subprocess.TimeoutExpired:
            # Kill process group
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.kill()
            except:
                pass
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            cleanup_temp_files(language, temp_file)
            
            return {
                'status': 'timeout',
                'output': '',
                'error': f'Execution timeout after {timeout} seconds',
                'time': execution_time
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'error': str(e),
            'time': 0
        }

def get_file_extension(language):
    """Get file extension for language"""
    extensions = {
        'c': '.c',
        'cpp': '.cpp',
        'python': '.py',
        'java': '.java',
        'javascript': '.js',
        'sql': '.sql'
    }
    return extensions.get(language, '.txt')

def get_commands(language, temp_file):
    """
    Get compile and run commands for language
    Returns: (compile_cmd, run_cmd)
    """
    commands = {
        'c': (
            f'gcc -o {temp_file}.out {temp_file}',
            f'{temp_file}.out'
        ),
        'cpp': (
            f'g++ -o {temp_file}.out {temp_file}',
            f'{temp_file}.out'
        ),
        'python': (
            None,
            f'python3 {temp_file}'
        ),
        'java': (
            f'javac {temp_file}',
            f'java -cp {os.path.dirname(temp_file)} {os.path.basename(temp_file)[:-5]}'
        ),
        'javascript': (
            None,
            f'node {temp_file}'
        ),
        'sql': (
            None,
            f'sqlite3 :memory: < {temp_file}'
        )
    }
    
    return commands.get(language, (None, None))

def cleanup_temp_files(language, temp_file):
    """Clean up temporary files"""
    files_to_remove = [temp_file]
    
    # Add compiled output files
    if language in ['c', 'cpp']:
        files_to_remove.append(f'{temp_file}.out')
    elif language == 'java':
        class_file = f"{temp_file[:-5]}.class"
        files_to_remove.append(class_file)
    
    for f in files_to_remove:
        try:
            if os.path.exists(f):
                os.remove(f)
        except:
            pass
