def get_compiler_command(language):
    """
    Get compiler command for language
    """
    commands = {
        'c': 'gcc',
        'cpp': 'g++',
        'python': 'python3',
        'java': 'javac',
        'javascript': 'node',
        'sql': 'sqlite3'
    }
    return commands.get(language, None)

def get_language_info(language):
    """
    Get language information
    """
    languages = {
        'c': {
            'name': 'C',
            'extension': '.c',
            'compiler': 'gcc',
            'version': '11.0'
        },
        'cpp': {
            'name': 'C++',
            'extension': '.cpp',
            'compiler': 'g++',
            'version': '11.0'
        },
        'python': {
            'name': 'Python',
            'extension': '.py',
            'compiler': 'python3',
            'version': '3.9+'
        },
        'java': {
            'name': 'Java',
            'extension': '.java',
            'compiler': 'javac',
            'version': '11+'
        },
        'javascript': {
            'name': 'JavaScript',
            'extension': '.js',
            'compiler': 'node',
            'version': '14+'
        },
        'sql': {
            'name': 'SQL',
            'extension': '.sql',
            'compiler': 'sqlite3',
            'version': '3.0+'
        }
    }
    return languages.get(language, {})
