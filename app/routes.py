from flask import Blueprint, render_template, request, redirect, url_for

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/result', methods=['POST'])
def result():
    # Just for testing - we'll later hook this up with transcription logic
    dummy_transcription = "This is where your transcript will appear."
    return render_template('result.html', transcription=dummy_transcription)