from datetime import timedelta

from flask import Flask, request, render_template, redirect, url_for, flash, session
from pydantic import ValidationError
from werkzeug.security import check_password_hash
from models import UserORM
from schemas import UserRegistration
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

    @app.route('/main/', methods=['GET', 'POST'])
    def mainpage():
        return render_template('mainpage.html')

    @app.route('/profile/edit/', methods=['GET', 'POST'])
    def profile_edit():
        if 'user_id' not in session:
            flash('You must be logged in.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']
        with SessionLocal() as db:
            user = db.query(UserORM).filetr(UserORM.id == user_id).first()

            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('logout'))

            if request.method == 'POST':
                new_data = UserRegistration(
                    username=request.form.get('username'),
                    email=request.form.get('email'),
                    birthday_date=request.form.get('birthday'),
                    password=request.form.get('password'),
                    confirm_password=request.form.get('confirm_password')
                )
                try:
                    updated_user = update_user(db, new_data, user.id)
                    flash('Profile updated successfully.', 'success')
                    return redirect(url_for('mainpage'))

                except ValueError as e:
                    flash(str(e), 'danger')

                except Exception as e:
                    flash('An error occurred.', 'danger')

            return render_template('edit_profile.html', user=user)

    @app.route('/login/', methods=['GET', 'POST'])
    def login():

        if 'user_id' in session:
            return redirect(url_for('mainpage'))

        reset = request.args.get('reset', 'false').lower() == 'true'

        print(reset)

        if request.method == 'POST':

            if reset:

                email = request.form.get('email')
                if email: email = email.strip()

                with SessionLocal() as db:
                    user = db.query(UserORM).filter_by(email=email).first()
                    if user:
                        flash('Your password has been reset to 123456. Please change your password.', 'info')
                        new_user_data = {
                            'username': user.username,
                            'password': '123456',
                            'confirm_password': '123456',
                            'email': email,
                            'birthday_date': user.birthday_date
                        }

                        user = update_user(db, UserRegistration(**new_user_data), user.id)

                        return redirect(url_for('login'))

                if not email:
                    return render_template('login.html', error = "Please enter your email address.", reset=True)

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