from app import app, db, login_manager, bcrypt
import os
import tempfile
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from flask import render_template, redirect, url_for, request, flash, jsonify,send_file,send_from_directory,session,abort
from pydub import AudioSegment
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, AudioFile
import time
from uuid import uuid4

AUDIO_DIRECTORY = 'audio_storage'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract')
def extract():
    return render_template('extract.html')

@app.route('/share')
def share():
    return render_template('share.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username is already taken. Please choose another one.', 'error')
        else:
            # Хеширование пароля с использованием Flask-Bcrypt
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logged_index')
@login_required
def logged_index():
    return render_template('logged_index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('login-username')
            password = request.form.get('login-password')

            user = User.query.filter_by(username=username).first()

            if user:
                if bcrypt.check_password_hash(user.password, password):
                    
                    login_user(user)
                    flash('Login successful!', 'success')
                    return redirect(url_for('logged_index'))
                else:
                    print('Invalid password')
                    flash('Invalid username or password', 'error')
            else:
                flash('Invalid username or password', 'error')

        return render_template('login.html')

    except Exception as e:
        return 'Internal Server Error', 500



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/crop', methods=['POST'])
@login_required
def crop():
    try:
        start_time = float(request.form.get('start_time'))
        end_time = float(request.form.get('end_time'))
        video_file = request.files['video']
        user_filename = request.form.get('filename', 'output')
        action = request.form.get('action', 'download')

        user_audio_directory = os.path.join(AUDIO_DIRECTORY, str(current_user.id))
        os.makedirs(user_audio_directory, exist_ok=True)

        unique_filename = user_filename
        counter = 1
        while os.path.exists(os.path.join(user_audio_directory, f'{unique_filename}.mp3')):
            unique_filename = f'{user_filename}_{counter}'
            counter += 1

        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'input.mp4')
            video_file.save(video_path)

            # Используйте moviepy для отрезки видео и сохранения аудио
            video = VideoFileClip(video_path)
            audio = video.audio.subclip(start_time, end_time)
            
            output_path = os.path.join(user_audio_directory, f'{unique_filename}.mp3')
            audio.write_audiofile(output_path, codec='mp3', fps=44100)

            audio_file = AudioFile(filename=f'{unique_filename}.mp3', path=output_path, user=current_user)
            db.session.add(audio_file)
            db.session.commit()

            if action == 'download':
                return send_file(output_path, as_attachment=True)
            elif action == 'save':
                filename = f'{unique_filename}.mp3'
                return send_file(output_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"Error during crop: {str(e)}"


@app.route('/profile')
@login_required
def profile():
    audio_files = AudioFile.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, audio_files=audio_files)


@app.route('/listen_audio/<user_id>/<filename>')
def listen_audio(user_id, filename):
    user = User.query.filter_by(id=user_id).first()
    username = user.username
    return render_template('listen_audio.html', user_id=user_id, filename=filename,username=username)

@app.route('/audio_storage/<user_id>/<filename>')
def serve_audio(user_id, filename):
    user_audio_path = os.path.join('audio_storage', str(user_id), filename)
    user_audio_path = os.path.abspath(user_audio_path)


    if os.path.exists(user_audio_path):
        print(f'file exist')
        return send_file(user_audio_path, as_attachment=True)
    else:
        abort(404)


@app.route('/search_profiles', methods=['GET', 'POST'])
@login_required
def search_profiles():
    search_results = []

    if request.method == 'POST':
        search_username = request.form.get('search_username')

        # Perform a simple case-insensitive search for matching usernames
        search_results = User.query.filter(User.username.ilike(f'%{search_username}%')).all()

    return render_template('search_profiles.html', search_results=search_results)


@app.route('/view_profile/<user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get(user_id)
    audio_files = AudioFile.query.filter_by(user_id=user_id).all()
    return render_template('view_profile.html', user=user, audio_files=audio_files)