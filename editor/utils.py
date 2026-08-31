from werkzeug.utils import secure_filename
from config import Config
import os

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_file_path(user_id, filename, folder_id=None):
    """Get file path for storage"""
    user_folder = os.path.join(Config.UPLOAD_FOLDER, str(user_id))
    
    if folder_id:
        file_path = os.path.join(user_folder, f'folder_{folder_id}', filename)
    else:
        file_path = os.path.join(user_folder, filename)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path

def create_file_structure(user_id):
    """Create default file structure for user"""
    user_folder = os.path.join(Config.UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    
    return user_folder

def delete_file_structure(user_id):
    """Delete user's file structure"""
    user_folder = os.path.join(Config.UPLOAD_FOLDER, str(user_id))
    
    import shutil
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
