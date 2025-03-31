from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
import os
import re
from werkzeug.utils import secure_filename
from .services.transcription import TranscriptionService


main = Blueprint('main', __name__)

# Ensure "audio" folder exists
UPLOAD_FOLDER = "uploads/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

METADATA_FOLDER = "/uploads/audio/metadata"
os.makedirs(METADATA_FOLDER, exist_ok=True)

# Initialize transcription service
transcription_service = TranscriptionService()

@main.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


# Step 1: Upload Audio File
@main.route('/upload_audio', methods=['GET', 'POST'])
def upload_audio():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Validate audio file type
        if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg')):
            return jsonify({"error": "Invalid file type. Please upload an audio file."}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)  # Save file to Google Colab

        return jsonify({
            "message": "Upload successful!",
            "file_name": file.filename
        })

    return render_template("audio/upload_audio.html")

# Step 2: Metadata Form
@main.route('/metadata', methods=['GET', 'POST'])
def metadata_form():
    try:
        file_name = request.args.get('file_name')
        if not file_name:
            flash('No file name provided', 'error')
            return redirect(url_for('main.upload_audio'))
            
        return render_template('audio/metadata_form.html', file_name=file_name)
    except Exception as e:
        app.logger.error(f"Error in metadata_form: {str(e)}")
        flash('An error occurred while loading the form', 'error')
        return redirect(url_for('main.index'))

# Step 3: Process Metadata
@main.route('/submit_metadata', methods=['POST'])
def submit_metadata():
    data = request.form.to_dict()
    file_name = data.get("file_name")

    if not file_name:
        return jsonify({"error": "Missing file name"}), 400

    metadata_path = os.path.join(METADATA_FOLDER, f"{file_name}.json")
    with open(metadata_path, "w") as f:
        import json
        json.dump(data, f, indent=4)

    return jsonify({"message": "Metadata saved successfully!"})

@main.route('/transcribe-video')
def transcribe_video():
    try:
        return render_template('video/transcribe-video.html')
    except Exception as e:
        app.logger.error(f"Error in transcribe_video: {str(e)}")
        flash('An error occurred while loading the video transcription page', 'error')
        return redirect(url_for('main.index'))


@main.route('/transcribe-youtube-video')
def transcribe_youtube_video():
    try:
        return render_template('youtube/transcribe-youtube-video.html')
    except Exception as e:
        app.logger.error(f"Error in transcribe_youtube_video: {str(e)}")
        flash('An error occurred while loading the YouTube transcription page', 'error')
        return redirect(url_for('main.index'))


@main.route('/result', methods=['POST'])
def result():
    # Just for testing - we'll later hook this up with transcription logic
    dummy_transcription = "This is where your transcript will appear."
    return render_template('result.html', transcription=dummy_transcription)

@main.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
    """Handle transcription requests"""
    if request.method == 'GET':
        return render_template('transcribe_form.html')
        
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Get metadata from form
        metadata = {
            'platform': request.form.get('platform', 'PANOPTO'),
            'course_code': request.form.get('course_code', '').upper(),
            'course_name': request.form.get('course_name', '').upper(),
            'week_no': request.form.get('week_no', ''),
            'transcript_type': request.form.get('transcript_type', 'Overview Video'),
            'part': request.form.get('part', ''),
            'week_topic': request.form.get('week_topic', ''),
            'author': request.form.get('author', ''),
            'keywords': request.form.get('keywords', ''),
            'comments': request.form.get('comments', '')
        }
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio')
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        current_app.logger.info(f"Processing file: {filepath}")
        
        # Transcribe audio
        transcription_text, error = transcription_service.transcribe_audio(filepath)
        if error:
            raise Exception(f"Transcription failed: {error}")
            
        # Create document
        doc, error = transcription_service.create_transcript_document(transcription_text, metadata)
        if error:
            raise Exception(f"Document creation failed: {error}")
            
        # Save document
        doc_filename = f"W{metadata['week_no']}_{metadata['transcript_type']}_{metadata['course_code']}_Transcript.docx"
        transcripts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcripts')
        doc_path = os.path.join(transcripts_dir, doc_filename)
        doc.save(doc_path)
        
        return send_file(
            doc_path,
            as_attachment=True,
            download_name=doc_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        current_app.logger.error(f"Transcription error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main.route('/download/<path:transcript_path>')
def download_transcript(transcript_path):
    try:
        # Ensure the path is within the uploads directory
        if not transcript_path.startswith(current_app.config['UPLOAD_FOLDER']):
            return jsonify({"error": "Invalid file path"}), 400
            
        if not os.path.exists(transcript_path):
            return jsonify({"error": "File not found"}), 404
            
        return send_file(
            transcript_path,
            as_attachment=True,
            download_name=os.path.basename(transcript_path)
        )
        
    except Exception as e:
        current_app.logger.error(f"Download failed: {str(e)}")
        return jsonify({"error": "Download failed"}), 500

@main.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": current_app.config.get('VERSION', '1.0.0')
    })
