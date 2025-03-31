import os
from datetime import timedelta

class Config:
    """Base configuration"""
    VERSION = '1.0.0'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'aac', 'ogg'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv'}
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Ensure required directories exist
    @staticmethod
    def init_app(app):
        """Initialize application"""
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'transcripts'), exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Override secret key with a fallback for development
    SECRET_KEY = os.environ.get('SECRET_KEY', 'temporary-production-key')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Only warn about missing SECRET_KEY when actually running the app
        if cls.SECRET_KEY == 'temporary-production-key':
            app.logger.warning(
                "WARNING: Using temporary SECRET_KEY in production. "
                "This is insecure! Please set SECRET_KEY environment variable."
            )

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'test_uploads')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 