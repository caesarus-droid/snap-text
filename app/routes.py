from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
import os
import re
from werkzeug.utils import secure_filename
from .services.transcription import TranscriptionService
import json


main = Blueprint('main', __name__)

# Ensure "audio" folder exists
UPLOAD_FOLDER = "uploads/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

METADATA_FOLDER = "/uploads/audio/metadata"
os.makedirs(METADATA_FOLDER, exist_ok=True)

# Initialize transcription service
transcription_service = TranscriptionService()

@main.before_app_request
def create_upload_directories():
    """Create necessary upload directories"""
    # Only run this once by checking if directories already exist
    if hasattr(create_upload_directories, 'already_run'):
        return
        
    upload_dirs = [
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio'),
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'video'),
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp'),
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcripts')
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        
    # Mark as already run
    create_upload_directories.already_run = True

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
        json.dump(data, f, indent=4)

    return jsonify({"message": "Metadata saved successfully!"})

@main.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
    """Handle audio transcription with multi-step form"""
    step = request.args.get('step', 'upload')
    
    if step == 'upload':
        return render_template('transcribe/step1_upload.html')
    
    elif step == 'metadata':
        if request.method == 'POST':
            # Handle file upload from step 1
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('main.transcribe'))
                
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('main.transcribe'))
                
            # Save file
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio')
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Pass to metadata form
            return render_template('transcribe/step2_metadata.html', filename=filename)
        else:
            # If someone tries to access step 2 directly, redirect to step 1
            return redirect(url_for('main.transcribe'))
    
    elif step == 'process':
        if request.method == 'POST':
            # Get metadata and filename from form
            metadata = {
                'platform': 'AUDIO',  # Default for audio
                'course_code': request.form.get('course_code', '').upper(),
                'course_name': request.form.get('course_name', '').upper(),
                'week_no': request.form.get('week_no', ''),
                'transcript_type': request.form.get('transcript_type', 'Audio'),
                'part': request.form.get('part', ''),
                'week_topic': request.form.get('week_topic', ''),
                'author': request.form.get('author', ''),
                'keywords': request.form.get('keywords', ''),
                'comments': request.form.get('comments', '')
            }
            
            filename = request.form.get('filename')
            if not filename:
                flash('File information missing', 'error')
                return redirect(url_for('main.transcribe'))
                
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
            
            # Process transcription
            try:
                # Show processing page with progress updates
                return render_template('transcribe/step3_processing.html', 
                                      filename=filename, 
                                      metadata=metadata)
            except Exception as e:
                current_app.logger.error(f"Error preparing transcription: {str(e)}")
                flash('Error preparing transcription', 'error')
                return redirect(url_for('main.transcribe'))
        else:
            return redirect(url_for('main.transcribe'))
    
    elif step == 'result':
        # This endpoint will be called via AJAX to get the actual transcription result
        filename = request.args.get('filename')
        metadata_json = request.args.get('metadata')
        
        if not filename or not metadata_json:
            return jsonify({"error": "Missing parameters"}), 400
            
        metadata = json.loads(metadata_json)
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        
        # Perform actual transcription
        transcription_text, error = transcription_service.transcribe_audio(filepath)
        if error:
            return jsonify({"error": f"Transcription failed: {error}"}), 500
            
        # Create document
        doc, error = transcription_service.create_transcript_document(transcription_text, metadata)
        if error:
            return jsonify({"error": f"Document creation failed: {error}"}), 500
            
        # Save document
        doc_filename = f"W{metadata['week_no']}_{metadata['transcript_type']}_{metadata['course_code']}_Transcript.docx"
        transcripts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcripts')
        doc_path = os.path.join(transcripts_dir, doc_filename)
        doc.save(doc_path)
        
        return jsonify({
            "success": True,
            "download_url": url_for('main.download_file', transcript_path=doc_path),
            "filename": doc_filename
        })
    
    else:
        return redirect(url_for('main.transcribe'))

@main.route('/download/<path:transcript_path>')
def download_file(transcript_path):
    try:
        # Ensure the path is within the uploads directory
        if not transcript_path.startswith(current_app.config['UPLOAD_FOLDER']):
            return jsonify({"error": "Invalid file path"}), 400
            
        if not os.path.exists(transcript_path):
            return jsonify({"error": "File not found"}), 404
            
        return send_file(transcript_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

@main.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": current_app.config.get('VERSION', '1.0.0')
    })

# Placeholder routes for features to be implemented later
@main.route('/transcribe-video', methods=['GET', 'POST'])
def transcribe_video():
    """Handle video transcription with multi-step form"""
    step = request.args.get('step', 'upload')
    
    if step == 'upload':
        return render_template('video/step1_upload.html')
    
    elif step == 'metadata':
        if request.method == 'POST':
            # Handle file upload from step 1
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('main.transcribe_video'))
                
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('main.transcribe_video'))
                
            # Validate video file type
            if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv')):
                flash('Invalid file type. Please upload a video file.', 'error')
                return redirect(url_for('main.transcribe_video'))
                
            # Save file
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'video')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Pass to metadata form
            return render_template('video/step2_metadata.html', filename=filename)
        else:
            # If someone tries to access step 2 directly, redirect to step 1
            return redirect(url_for('main.transcribe_video'))
    
    elif step == 'process':
        if request.method == 'POST':
            # Get metadata and filename from form
            metadata = {
                'platform': 'PANOPTO',  # Default for video
                'course_code': request.form.get('course_code', '').upper(),
                'course_name': request.form.get('course_name', '').upper(),
                'week_no': request.form.get('week_no', ''),
                'transcript_type': request.form.get('transcript_type', 'Lecture Video'),
                'part': request.form.get('part', ''),
                'week_topic': request.form.get('week_topic', ''),
                'author': request.form.get('author', ''),
                'keywords': request.form.get('keywords', ''),
                'comments': request.form.get('comments', '')
            }
            
            filename = request.form.get('filename')
            if not filename:
                flash('File information missing', 'error')
                return redirect(url_for('main.transcribe_video'))
                
            # Show processing page with progress updates
            return render_template('video/step3_processing.html', 
                                  filename=filename, 
                                  metadata=metadata)
        else:
            return redirect(url_for('main.transcribe_video'))
    
    elif step == 'result':
        # Handle AJAX request for processing
        filename = request.args.get('filename')
        metadata_json = request.args.get('metadata')
        
        if not filename or not metadata_json:
            return jsonify({"error": "Missing parameters"}), 400
            
        metadata = json.loads(metadata_json)
        
        try:
            # Get file path
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'video', filename)
            
            # Extract audio from video
            from moviepy.editor import VideoFileClip
            import os
            
            video = VideoFileClip(filepath)
            temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            audio_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}.mp3")
            video.audio.write_audiofile(audio_path)
            
            # Perform transcription
            transcription_text, error = transcription_service.transcribe_audio(audio_path)
            if error:
                return jsonify({"error": f"Transcription failed: {error}"}), 500
                
            # Create document
            doc, error = transcription_service.create_transcript_document(transcription_text, metadata)
            if error:
                return jsonify({"error": f"Document creation failed: {error}"}), 500
                
            # Save document
            doc_filename = f"W{metadata['week_no']}_{metadata['transcript_type']}_{metadata['course_code']}_Transcript.docx"
            transcripts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcripts')
            os.makedirs(transcripts_dir, exist_ok=True)
            doc_path = os.path.join(transcripts_dir, doc_filename)
            doc.save(doc_path)
            
            # Clean up temporary audio file
            try:
                os.remove(audio_path)
            except:
                pass
            
            return jsonify({
                "success": True,
                "download_url": url_for('main.download_file', transcript_path=doc_path),
                "filename": doc_filename
            })
            
        except Exception as e:
            current_app.logger.error(f"Video transcription error: {str(e)}")
            return jsonify({"error": f"Failed to process video: {str(e)}"}), 500
    
    else:
        return redirect(url_for('main.transcribe_video'))

@main.route('/transcribe-youtube-video', methods=['GET', 'POST'])
def transcribe_youtube_video():
    """Handle YouTube video transcription with multi-step form"""
    step = request.args.get('step', 'url')
    
    if step == 'url':
        return render_template('youtube/step1_url.html')
    
    elif step == 'metadata':
        if request.method == 'POST':
            # Get YouTube URL from form
            youtube_url = request.form.get('youtube_url')
            if not youtube_url:
                flash('No YouTube URL provided', 'error')
                return redirect(url_for('main.transcribe_youtube_video'))
                
            # Validate YouTube URL
            import re
            youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            match = re.match(youtube_regex, youtube_url)
            
            if not match:
                flash('Invalid YouTube URL', 'error')
                return redirect(url_for('main.transcribe_youtube_video'))
                
            video_id = match.group(6)
            
            # Pass to metadata form
            return render_template('youtube/step2_metadata.html', youtube_url=youtube_url, video_id=video_id)
        else:
            # If someone tries to access step 2 directly, redirect to step 1
            return redirect(url_for('main.transcribe_youtube_video'))
    
    elif step == 'download':
        if request.method == 'POST':
            # Get metadata and YouTube URL from form
            metadata = {
                'platform': 'YOUTUBE',
                'course_code': request.form.get('course_code', '').upper(),
                'course_name': request.form.get('course_name', '').upper(),
                'week_no': request.form.get('week_no', ''),
                'transcript_type': request.form.get('transcript_type', 'YouTube Video'),
                'part': request.form.get('part', ''),
                'week_topic': request.form.get('week_topic', ''),
                'author': request.form.get('author', ''),
                'keywords': request.form.get('keywords', ''),
                'comments': request.form.get('comments', '')
            }
            
            youtube_url = request.form.get('youtube_url')
            video_id = request.form.get('video_id')
            
            if not youtube_url or not video_id:
                flash('YouTube video information missing', 'error')
                return redirect(url_for('main.transcribe_youtube_video'))
                
            # Show download page
            return render_template('youtube/step3_download.html', 
                                  youtube_url=youtube_url,
                                  video_id=video_id,
                                  metadata=metadata)
        else:
            return redirect(url_for('main.transcribe_youtube_video'))
    
    elif step == 'process':
        if request.method == 'POST':
            # Get parameters from form
            youtube_url = request.form.get('youtube_url')
            video_id = request.form.get('video_id')
            metadata_json = request.form.get('metadata')
            
            if not youtube_url or not video_id or not metadata_json:
                flash('Missing parameters', 'error')
                return redirect(url_for('main.transcribe_youtube_video'))
                
            metadata = json.loads(metadata_json)
            
            # Show processing page
            return render_template('youtube/step4_processing.html',
                                  youtube_url=youtube_url,
                                  video_id=video_id,
                                  metadata=metadata)
        else:
            return redirect(url_for('main.transcribe_youtube_video'))
    
    elif step == 'result':
        # Handle AJAX request for processing
        youtube_url = request.args.get('youtube_url')
        video_id = request.args.get('video_id')
        metadata_json = request.args.get('metadata')
        
        if not youtube_url or not video_id or not metadata_json:
            return jsonify({"error": "Missing parameters"}), 400
            
        metadata = json.loads(metadata_json)
        
        try:
            # Download YouTube video audio
            from pytube import YouTube
            import os
            
            yt = YouTube(youtube_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                return jsonify({"error": "Could not find audio stream for this YouTube video"}), 500
                
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download the audio
            audio_file = audio_stream.download(output_path=temp_dir, filename=f"{video_id}")
            
            # Rename to add extension if needed
            base, ext = os.path.splitext(audio_file)
            if not ext:
                audio_file_with_ext = f"{base}.mp4"
                os.rename(audio_file, audio_file_with_ext)
                audio_file = audio_file_with_ext
            
            # Get video title for metadata
            video_title = yt.title
            if not metadata.get('comments'):
                metadata['comments'] = f"Transcribed from YouTube video: {video_title}"
                
            # Perform transcription
            transcription_text, error = transcription_service.transcribe_audio(audio_file)
            if error:
                return jsonify({"error": f"Transcription failed: {error}"}), 500
                
            # Create document
            doc, error = transcription_service.create_transcript_document(transcription_text, metadata)
            if error:
                return jsonify({"error": f"Document creation failed: {error}"}), 500
                
            # Save document
            doc_filename = f"W{metadata['week_no']}_{metadata['transcript_type']}_{metadata['course_code']}_Transcript.docx"
            transcripts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcripts')
            os.makedirs(transcripts_dir, exist_ok=True)
            doc_path = os.path.join(transcripts_dir, doc_filename)
            doc.save(doc_path)
            
            # Clean up temporary audio file
            try:
                os.remove(audio_file)
            except:
                pass
            
            return jsonify({
                "success": True,
                "download_url": url_for('main.download_file', transcript_path=doc_path),
                "filename": doc_filename,
                "video_title": video_title
            })
            
        except Exception as e:
            current_app.logger.error(f"YouTube transcription error: {str(e)}")
            return jsonify({"error": f"Failed to process YouTube video: {str(e)}"}), 500
    
    else:
        return redirect(url_for('main.transcribe_youtube_video'))
