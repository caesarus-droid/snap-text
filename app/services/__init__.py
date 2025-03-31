from .transcription import TranscriptionService

# Global service instances
transcription_service = None

def init_services(app):
    """Initialize application services"""
    global transcription_service
    
    try:
        # Initialize transcription service with app instance
        transcription_service = TranscriptionService(app)
        app.logger.info("Services initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize services: {str(e)}")
        raise
