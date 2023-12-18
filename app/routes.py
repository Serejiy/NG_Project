from app import app, db, login_manager, bcrypt
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from flask import render_template, redirect, url_for, request, flash, jsonify, send_file,session,abort
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, AudioFile

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
                # Пользователь найден, проверяем пароль
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
        action = request.form.get('action', 'download')  # По умолчанию download

        # Ensure the user has a directory in the audio storage
        user_audio_directory = os.path.join(AUDIO_DIRECTORY, str(current_user.id))
        os.makedirs(user_audio_directory, exist_ok=True)

        # Проверка уникальности имени файла в директории пользователя
        unique_filename = user_filename
        counter = 1
        while os.path.exists(os.path.join(user_audio_directory, f'{unique_filename}.mp3')):
            unique_filename = f'{user_filename}_{counter}'
            counter += 1

        # Использование временного каталога для обработки видео
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'input.mp4')
            video_file.save(video_path)

            # Обрезаем видео с использованием moviepy
            video = VideoFileClip(video_path).subclip(start_time, end_time)

            # Сохраняем файл в директорию пользователя
            output_path = os.path.join(user_audio_directory, f'{unique_filename}.mp3')
            video.audio.write_audiofile(output_path, codec='mp3')

            # Сохраняем информацию о файле в базе данных и привязываем к пользователю
            audio_file = AudioFile(filename=f'{unique_filename}.mp3', path=output_path, user=current_user)
            db.session.add(audio_file)
            db.session.commit()

            if action == 'download':
                return send_file(output_path, as_attachment=True)
            elif action == 'save':
                flash("Audio saved")
                return 'Audio saved to the dashboard successfully.'
    except Exception as e:
        return f"Error during crop: {str(e)}"


@app.route('/profile')
@login_required
def profile():
    audio_files = AudioFile.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, audio_files=audio_files)

@app.route('/profile_settings')
@login_required
def profile_settings():
    return render_template('profile_settings.html')

@app.route('/listen_audio/<user_id>/<filename>')
def listen_audio(user_id, filename):
    return render_template('listen_audio.html', user_id=user_id, filename=filename)

@app.route('/audio_storage/<user_id>/<filename>')
def serve_audio(user_id, filename):
    user_audio_path = os.path.join('audio_storage', str(user_id), filename)
    user_audio_path = os.path.abspath(user_audio_path)


    if os.path.exists(user_audio_path):
        print(f'file exist')
        return send_file(user_audio_path, as_attachment=True)
    else:
        abort(404)

@app.route('/share_audio/<filename>')
def share_audio(filename):
    return render_template('share_audio.html', filename=filename)

