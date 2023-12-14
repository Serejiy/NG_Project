from app import app
from app import db
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, AudioFile
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверяем, существует ли пользователь с таким именем
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username is already taken. Please choose another one.', 'error')
        else:
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('logged_index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logged_index')
@login_required
def logged_index():
    return render_template('logged_index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    audio_files = AudioFile.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, audio_files=audio_files)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    audio_files = AudioFile.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, audio_files=audio_files)
