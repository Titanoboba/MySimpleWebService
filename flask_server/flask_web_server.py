from datetime import timedelta, datetime
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from pydantic import ValidationError
from werkzeug.security import check_password_hash
from models import UserORM, TaskORM, TaskStatus
from schemas import UserRegistration, UserUpdate
from database import SessionLocal
from services import add_user, update_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from collections import defaultdict
import os


def create_app():
    app = Flask(__name__, static_folder='static')
    app.secret_key = os.getenv('FLASK_SECRET_KEY')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/logout/')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        data = request.get_json()
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        user_id = session['user_id']
        try:
            with SessionLocal() as db:
                task = TaskORM(title=title, user_id=user_id, status = TaskStatus.todo)
                db.add(task)
                db.commit()
                db.refresh(task)
                return jsonify({
                    'id': task.id,
                    'title': task.title,
                    'status': task.status.value if hasattr(task.status, 'value') else task.status,
                    'created_at': task.created_at.isoformat()
                }), 201
        except Exception as e:
            db.rollback()
            print(f"Error creating task: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
    def update_task(task_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Unathorized'}), 401

        data = request.get_json()
        new_status = data.get('status')

        if new_status not in ['todo', 'in_progress', 'done']:
            return jsonify({'error': 'Invalid status'}), 400

        user_id = session['user_id']
        with SessionLocal() as db:
            task = db.query(TaskORM).filter(TaskORM.id == task_id, TaskORM.user_id == user_id).first()

            if task is None:
                return jsonify({'error': 'Task not found'}), 404

            task.status = TaskStatus(new_status)
            task.updated_at = datetime.utcnow()
            db.commit()
            return jsonify({'message': 'Status updated'}), 200

    @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Unathorized'}), 401

        user_id = session['user_id']
        with SessionLocal() as db:
            task = db.query(TaskORM).filter(TaskORM.id == task_id, TaskORM.user_id == user_id).first()

            if not task:
                return jsonify({'error': 'Task not found'}), 404

            db.delete(task)
            db.commit()
            return jsonify({'message': 'Task deleted'}), 200

    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        if 'user_id' not in session:
            return jsonify([]), 401
        user_id = session['user_id']
        with SessionLocal() as db:
            tasks = db.query(TaskORM).filter(TaskORM.user_id == user_id).order_by(TaskORM.created_at).all()
            result = []
            for task in tasks:
                result.append({
                    'id': task.id,
                    'title': task.title,
                    'status': task.status.value if hasattr(task.status, 'value') else task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                })
            return jsonify(result)

    @app.route('/main/', methods=['GET', 'POST'])
    def mainpage():
        return render_template('mainpage.html')

    @app.route('/profile/', methods=['GET', 'POST'])
    def profile():

        field_errors = defaultdict(list)

        if 'user_id' not in session:
            flash('You must be logged in.', 'warning')
            return redirect(url_for('login'))

        update = request.args.get('update', 'false').lower() == 'true'
        user_id = session['user_id']
        with SessionLocal() as db:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()

            if update:
                if not user:
                    flash('User not found', 'danger')
                    return redirect(url_for('logout'))

                if request.method == 'POST':
                    form_data = {
                        'username': request.form.get('username'),
                        'email': request.form.get('email'),
                        'prev_password': request.form.get('prev_password'),
                        'password': request.form.get('password'),
                        'confirm_password': request.form.get('confirm_password')
                    }

                    if form_data['username'] != user.username:
                        existing = db.query(UserORM).filter(UserORM.username == form_data['username']).first()
                        if existing:
                            field_errors['username'].append("Username already taken")

                    if form_data['email'] != user.email:
                        existing = db.query(UserORM).filter(UserORM.email == form_data['email']).first()
                        if existing:
                            field_errors['email'].append("Email already taken")

                    try:

                        update_data = UserUpdate(**form_data)

                        if update_data.password:
                            if not update_data.prev_password:
                                field_errors['prev_password'].append("Previous password is required")

                            elif not check_password_hash(user.password_hash, update_data.prev_password):
                                field_errors['prev_password'].append("Invalid previous password")

                            elif len(update_data.password) < 6:
                                field_errors['password'].append("Password must be at least 6 characters")

                            elif update_data.password != update_data.confirm_password:
                                field_errors['confirm_password'].append("Passwords do not match")

                        else:
                            update_data.password = None
                            update_data.confirm_password = None
                            update_data.prev_password = None

                        if not field_errors:
                            update_dict = {
                                key: value for key, value in update_data.model_dump(exclude={'prev_password', 'confirm_passwrod'}).items()
                                if value is not None
                            }

                            if 'password' in update_dict:
                                from werkzeug.security import generate_password_hash
                                update_dict['password_hash'] = generate_password_hash(update_dict['password'], method='pbkdf2:sha256')

                            updated_user = update_user(db, update_dict, user.id)

                            if 'username' in update_dict:
                                session['username'] = updated_user.username

                            flash('Profile updated successfully.', 'success')
                            return redirect(url_for('mainpage'))

                    except ValidationError as e:
                        for error in e.errors():
                            field = error['loc'][0] if error['loc'] else ''
                            msg = error['msg']

                            if msg.startswith('Value error, '):
                                msg = msg[13:]
                            field_errors[field].append(msg)

                    return render_template('edit_profile.html',
                                           user=user,
                                           update=update,
                                           errors=field_errors,
                                           username=form_data['username'],
                                           email=form_data['email'])

        return render_template('edit_profile.html',
                               user=user,
                               update=update,
                               errors=field_errors,
                               username=user.username,
                               email=user.email)

    @app.route('/login/', methods=['GET', 'POST'])
    def login():

        if 'user_id' in session:
            return redirect(url_for('mainpage'))

        reset = request.args.get('reset', 'false').lower() == 'true'

        if request.method == 'POST':

            if reset:

                email = request.form.get('email')
                if email: email = email.strip()
                else: return render_template('login.html', error = "Please enter your email address.", reset=True)

                with SessionLocal() as db:
                    user = db.query(UserORM).filter_by(email=email).first()
                    if user:
                        from werkzeug.security import generate_password_hash

                        flash('Your password has been reset to 123456. Please change your password.', 'info')
                        new_user_data = {
                            'username': user.username,
                            'password_hash': generate_password_hash('123456', method='pbkdf2:sha256'),
                            'email': email,
                            'birthday_date': user.birthday_date
                        }

                        user = update_user(db, new_user_data, user.id)

                        return redirect(url_for('login'))
                    else:
                        return render_template('login.html', error="There is no user with this email.", reset=True)

            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember')

            with SessionLocal() as db:
                user = db.query(UserORM).filter(
                    or_(
                        UserORM.username == username,
                        UserORM.email == username)).first()

            if user is None:
                return render_template('login.html', error='Invalid username or password', reset=reset)

            if not check_password_hash(user.password_hash, password):
                return render_template('login.html', error="Invalid username or password", reset=reset)

            session['username'] = user.username
            session['user_id'] = user.id

            if remember:
                session.permanent = True

            print(f"Got Login information, {username}, password: {password}, remember: {remember}")
            return redirect(url_for('mainpage', registered=True))

        return render_template('login.html', error="", reset=reset)

    @app.route('/register/', methods=['post', 'get'])
    def register():
        username = email = password = confirm_password = birthday = ''
        field_errors = defaultdict(list)
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            birthday = request.form.get('birthday', '').strip()
            email = request.form.get('email', '').strip()

            form_data = {
                'username': username,
                'password': password,
                'confirm_password': confirm_password,
                'email': email,
                'birthday_date': birthday
            }

            try:
                # Everything is validated in UserRegistration model from pydantic
                reg_data = UserRegistration(**form_data)

                with SessionLocal() as db:
                    # Creating user in database
                    new_user = add_user(db, reg_data)

                    print(
                        f"Registered user! username: {reg_data.username}, password: {reg_data.password}, email: {reg_data.email}, "
                        f"birthday: {reg_data.birthday_date}")

                    return redirect(url_for('login', registered=True))

            except IntegrityError as e:
                db.rollback()
                error_msg = str(e.orig) if e.orig else str(e)

                if "Duplicate entry" in error_msg:
                    if "key 'users.name_UNIQUE'" in error_msg or "key 'name_UNIQUE'" in error_msg:
                        field_errors["username"].append("Username already taken")
                    elif "key 'users.email_UNIQUE'" in error_msg or "key 'email_UNIQUE'" in error_msg:
                        field_errors["email"].append("Email already taken")

            except ValidationError as e:
                for error in e.errors():
                    field = error['loc'][0]
                    msg = error['msg']

                    if msg.startswith('Value error, '):
                        msg = msg[13:]
                    field_errors[field].append(msg)

                    if field == 'email':
                        email = ''
                    elif field == 'birthday_date':
                        birthday = ''
                    elif field == 'confirm_password' or field == 'password':
                        confirm_password = ''
                        password = ''

            if field_errors:
                return render_template('register.html',
                                       errors=field_errors,
                                       username=username,
                                       email=email,
                                       password=password,
                                       confirm_password=confirm_password,
                                       birthday=birthday)

        return render_template('register.html',
                                errors={},
                                username=username,
                                email=email,
                                password='',
                                confirm_password='',
                                birthday=birthday)

    return app