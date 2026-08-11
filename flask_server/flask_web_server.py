from flask import Flask, request, render_template, redirect, url_for, flash, session
from pydantic import ValidationError
from werkzeug.security import check_password_hash
from models import UserORM
from schemas import UserRegistration
from database import SessionLocal
from services import create_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from collections import defaultdict
import os


def create_app():
    app = Flask(__name__, static_folder='static')
    app.secret_key = os.getenv('FLASK_SECRET_KEY')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login/', methods=['post', 'get'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            with SessionLocal() as db:
                user = db.query(UserORM).filter(
                    or_(
                        UserORM.username == username,
                        UserORM.email == username)).first()

            if user is None:
                return render_template('login.html', error='Invalid username or password')

            if not check_password_hash(user.password_hash, password):
                return render_template('login.html', error="Invalid username or password")

            session['username'] = user.username
            session['user_id'] = user.id
            print(f"Got Login information, {username}, password: {password}")
            return render_template('mainpage.html')

        return render_template('login.html', error="")

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
                'birthday_date': birthday,
            }

            try:
                # Everything is validated in UserRegistration model from pydantic
                reg_data = UserRegistration(**form_data)

                with SessionLocal() as db:

                    # Creating user in database
                    new_user = create_user(db, reg_data)

                    print(
                        f"Registered user! username: {reg_data.username}, password: {reg_data.password}, email: {reg_data.email}, "
                        f"birthday: {reg_data.birthday_date}")

                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('login', registered=True))

            except IntegrityError as e:
                db.rollback()
                error_msg = str(e.orig) if e.orig else str(e)
                print(error_msg)

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