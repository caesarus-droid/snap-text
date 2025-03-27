from flask import Blueprint, render_template, request, redirect, url_for, flash
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
@main.route('/upload-audio', methods=['GET', 'POST'])
def upload_audio():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            flash('No file selected.')
            return redirect(request.url)

        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            flash('No selected file.')
            return redirect(request.url)

        if audio_file:
            file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
            audio_file.save(file_path)

            flash(f"File {audio_file.filename} uploaded successfully!")
            return redirect(url_for("main.metadata_form", filename=audio_file.filename))

    return render_template('audio/upload_audio.html')

# Step 2: Metadata Form
@main.route('/metadata', methods=['GET', 'POST'])
def metadata_form():
    filename = request.args.get('filename')

    if not filename:
        flash("No audio file found.")
        return redirect(url_for("main.upload_audio"))

    return render_template('metadata_form.html', filename=filename)

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
