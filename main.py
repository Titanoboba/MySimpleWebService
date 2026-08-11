from database import get_db
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from models import UserORM
from faker import Faker
from flask_server.flask_web_server import create_app
import os

def add_10_random_people():
    fake = Faker()
    users = []
    for _ in range(10):
        try:
            users.append({
                'username': fake.first_name(),
                'email': fake.email(),
                'birthday_date': fake.date_of_birth(minimum_age=18, maximum_age=100)
            })
        except IntegrityError:
            print("Could not add user")

    with get_db() as session:
        for data in users:
            user = UserORM(**data)
            session.add(user)
        session.commit()

def print_db_data():
    with get_db() as connection:
        result = connection.execute(text("SELECT * FROM pydantic_test.users;"))

        rows = result.fetchall()
        for row in rows:
            print(row)


if __name__ == '__main__':
    app = create_app()
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    app.run(host=host, port=5000, debug=True)