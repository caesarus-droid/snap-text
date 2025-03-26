from flask import Blueprint, render_template, request, redirect, url_for
import os
import re
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/upload-audio', methods=['GET', 'POST'])
def upload_audio():
    if request.method == 'POST':
        if 'audioFile' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["audioFile"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        return jsonify({"file_path": file_path})

    return render_template('audio/upload-audio.html', methods=['GET'])


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
