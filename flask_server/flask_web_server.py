from flask import Flask, request, render_template
import re
from datetime import datetime, date

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login/', methods=['post', 'get'])
    def login():
        message = None
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            print(f"Got information, username: {username}, password: {password}")

        return render_template('login.html', message=message)

    @app.route('/register/', methods=['post', 'get'])
    def register():
        username = email = password = confirm_password = birthday_raw = ''
        errors = []
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            email = request.form.get('email', '').strip()

            birthday_raw = request.form.get('birthday', '')
            birthday = datetime.strptime(birthday_raw, '%Y-%m-%d').date()

            if password != confirm_password:
                errors.append("Passwords don't match")
                confirm_password = ''

            if not is_valid_email(email):
                errors.append("Invalid email")
                email = ''

            age = calculate_age(birthday)

            if age < 18:
                errors.append("You must be at least 18 years old")
                birthday_raw = ''

            if age > 100:
                errors.append("Age cannot exceed 100 years.")
                birthday_raw = ''

            if errors:
                return render_template('register.html',
                                       errors=errors,
                                       username=username,
                                       email=email,
                                       password=password,
                                       confirm_password=confirm_password,
                                       birthday=birthday_raw)

            print(f"Got information, username: {username}, password: {password}, email: {email}, birthday: {birthday}")
        return render_template('register.html',
                                errors=errors,
                                username=username,
                                email=email,
                                password=password,
                                confirm_password=confirm_password,
                                birthday=birthday_raw)
    return app

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_age(birth_date):
    today = date.today()
    age = today.year - birth_date.year
    # If birthday has not been yet
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age