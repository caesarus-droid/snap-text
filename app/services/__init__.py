from .transcription import TranscriptionService

# Initialize services
transcription_service = None

def init_services(app):
    """Initialize application services"""
    global transcription_service
    
    try:
        transcription_service = TranscriptionService()
        app.logger.info("Transcription service initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize transcription service: {str(e)}")
        raise
