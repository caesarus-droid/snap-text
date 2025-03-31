import whisper
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
import os
from flask import current_app
import torch

class TranscriptionService:
    def __init__(self):
        # Check if CUDA is available for GPU acceleration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.model = whisper.load_model("medium", device=self.device)
            current_app.logger.info(f"Whisper model loaded successfully on {self.device}")
        except Exception as e:
            current_app.logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    def transcribe_audio(self, audio_path, language='en'):
        """Transcribe audio file using Whisper"""
        try:
            # Log the transcription start
            current_app.logger.info(f"Starting transcription of {audio_path}")
            
            # Ensure the file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Perform transcription
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=torch.cuda.is_available()  # Use FP16 if on GPU
            )
            
            current_app.logger.info(f"Transcription completed for {audio_path}")
            return result['text'], None
            
        except Exception as e:
            current_app.logger.error(f"Transcription error: {str(e)}")
            return None, str(e)
    
    def create_transcript_document(self, transcription_text, metadata):
        """Create a formatted Word document with the transcription"""
        try:
            doc = Document()
            
            # Set document metadata
            doc.core_properties.title = metadata.get('title', 'Video Transcript')
            doc.core_properties.author = metadata.get('author', '')
            doc.core_properties.keywords = metadata.get('keywords', '')
            doc.core_properties.comments = metadata.get('comments', '')
            
            # Add headers
            headers = [
                f"{metadata.get('platform', '')} VIDEO TRANSCRIPT",
                f"{metadata.get('course_code', '')} – {metadata.get('course_name', '')}",
                f"WEEK {metadata.get('week_no', '')} {metadata.get('transcript_type', '')} {metadata.get('part', '')} Transcript",
                metadata.get('week_topic', '')
            ]
            
            for header in headers:
                p = doc.add_paragraph()
                run = p.add_run(header)
                p.style = 'Heading 1'
                run.font.size = Pt(18)
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.space_before = Pt(0)
                p.space_after = Pt(0)
            
            # Add transcription paragraphs
            paragraphs = self._split_text_into_paragraphs(transcription_text)
            for paragraph in paragraphs:
                p = doc.add_paragraph(paragraph)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                for run in p.runs:
                    run.font.size = Pt(16)
            
            return doc, None
            
        except Exception as e:
            current_app.logger.error(f"Document creation error: {str(e)}")
            return None, str(e)
    
    def _split_text_into_paragraphs(self, text, max_sentences=5):
        """Split text into paragraphs based on sentence boundaries"""
        sentences = re.split(r'(?<=[.!?]) +', text)
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            if len(current_paragraph) >= max_sentences:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return paragraphs 