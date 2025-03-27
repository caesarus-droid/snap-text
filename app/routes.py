from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
import re
from werkzeug.utils import secure_filename


main = Blueprint('main', __name__)

# Ensure "audio" folder exists
UPLOAD_FOLDER = "uploads/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route('/')
def index():
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
    return render_template('audio/metadata_form.html')

# Step 3: Process Metadata
@main.route('/process-metadata', methods=['POST'])
def process_metadata():
    metadata = {
        "filename": request.form.get("filename"),
        "instructor_name": request.form.get("instructor_name"),
        "course_name": request.form.get("course_name"),
        "course_code": request.form.get("course_code"),
        "transcript_topic": request.form.get("transcript_topic"),
        "audio_source": request.form.get("audio_source"),
        "transcript_type": request.form.get("transcript_type"),
    }

    print("✅ Metadata Captured:", metadata)
    flash(f"Metadata for {metadata['filename']} saved. Transcription will start soon!")

    return redirect(url_for("main.upload_audio"))  # Or go to a transcription page

@main.route('/transcribe-video')
def transcribe_video():
    return render_template('video/transcribe-video.html')


@main.route('/transcribe-youtube-video')
def transcribe_youtube_video():
    return render_template('youtube/transcribe-youtube-video.html')


@main.route('/result', methods=['POST'])
def result():
    # Just for testing - we'll later hook this up with transcription logic
    dummy_transcription = "This is where your transcript will appear."
    return render_template('result.html', transcription=dummy_transcription)
