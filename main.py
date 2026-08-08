from database import get_db
from sqlalchemy import text
from models import UserORM
from faker import Faker

def add_10_random_people():
    fake = Faker()
    users = []
    for _ in range(10):
        users.append({
            'name': fake.first_name(),
            'email': fake.email(),
            'birthday_date': fake.date_of_birth(minimum_age=18, maximum_age=100)
        })

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
    print_db_data()
    #TODO Add flask registration web page and create FastAPI web page to see the db.