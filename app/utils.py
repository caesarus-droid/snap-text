import os
from werkzeug.utils import secure_filename
from flask import current_app
import logging

def setup_logger():
    """Configure application logging"""
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder):
    """Safely save uploaded file"""
    if file and allowed_file(file.filename, current_app.config['ALLOWED_AUDIO_EXTENSIONS']):
        filename = secure_filename(file.filename)
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        return filepath, None
    return None, "Invalid file type or no file provided"

def ensure_folder_exists(folder_path):
    """Ensure a folder exists, create if it doesn't"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
