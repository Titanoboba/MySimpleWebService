from flask import Flask, request, render_template
from pydantic import ValidationError
from schemas import UserRegistration


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
            print(f"Got Login information, username: {username}, password: {password}")

        return render_template('login.html', message=message)

    @app.route('/register/', methods=['post', 'get'])
    def register():
        username = email = password = confirm_password = birthday = ''
        errors = []
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            birthday = request.form.get('birthday', '').strip()
            email = request.form.get('email', '').strip()

            form_data = {
                'name': username,
                'password': password,
                'confirm_password': confirm_password,
                'email': email,
                'birthday_date': birthday,
            }

            try:
                # Everything is validated in UserRegistration model from pydantic
                user = UserRegistration(**form_data)
                # If we are here, then validation has been finished successfully
                print(f"Registered user! username: {user.name}, password: {user.password}, email: {user.email}, "
                      f"birthday: {user.birthday_date}")
                return f"Registration successful! Please, log in."

            except ValidationError as e:
                for error in e.errors():
                    field = error['loc'][0]
                    msg = error['msg']

                    if msg.startswith('Value error, '):
                        msg = msg[13:]

                    #errors.append(format_error(msg))
                    errors.append(msg)

                    if field == 'email':
                        email = ''
                    elif field == 'birthday_date':
                        birthday = ''
                    elif field == 'confirm_password' or field == 'password':
                        confirm_password = ''
                        password = ''

            if errors:
                return render_template('register.html',
                                       errors=errors,
                                       username=username,
                                       email=email,
                                       password=password,
                                       confirm_password=confirm_password,
                                       birthday=birthday)

        return render_template('register.html',
                                errors=errors,
                                username=username,
                                email=email,
                                password='',
                                confirm_password='',
                                birthday=birthday)
    return app