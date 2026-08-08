from flask import Flask, request, render_template
import os
from dotenv import load_dotenv
import re

load_dotenv()
FLASK_HOST=os.getenv('FLASK_HOST', '127.0.0.1')

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
    message = None
    username = email = password = confirm_password = ''
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email').strip()

        if password != confirm_password:
            message = "Passwords don't match"
            confirm_password = ''
            return render_template('register.html',
                            message=message,
                            username=username,
                            email=email,
                            password=password,
                            confirm_password=confirm_password)
        if not is_valid_email(email):
            message = "Invalid email"
            email = ''
            return render_template('register.html',
                                   message=message,
                                   username=username,
                                   email=email,
                                   password=password,
                                   confirm_password=confirm_password)

        print(f"Got information, username: {username}, password: {password}, email: {email}")
    return render_template('register.html',
                           message=message,
                           username=username,
                           email=email,
                           password=password,
                           confirm_password=confirm_password)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

if __name__ == '__main__':
    app.run(host=f'{FLASK_HOST}', port=5000, debug=True)
