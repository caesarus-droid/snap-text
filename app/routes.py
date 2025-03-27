from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
import re
from werkzeug.utils import secure_filename


main = Blueprint('main', __name__)

# Ensure "audio" folder exists
UPLOAD_FOLDER = "uploads/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

METADATA_FOLDER = "/uploads/audio/metadata"
os.makedirs(METADATA_FOLDER, exist_ok=True)

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
    return render_template('video/transcribe-video.html')


@main.route('/transcribe-youtube-video')
def transcribe_youtube_video():
    return render_template('youtube/transcribe-youtube-video.html')


@main.route('/result', methods=['POST'])
def result():
    # Just for testing - we'll later hook this up with transcription logic
    dummy_transcription = "This is where your transcript will appear."
    return render_template('result.html', transcription=dummy_transcription)
