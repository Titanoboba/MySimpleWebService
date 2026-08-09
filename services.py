from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session
from models import UserORM
from schemas import UserRegistration, UserCreate

"""
The purpose of this file is to perform some tasks for database. Function create_user
will take information from UserRegistration pydantic model and create ORM user with hashed password
"""

def create_user(db: Session, user_data: UserRegistration) -> UserORM:
    hashed_password = generate_password_hash(user_data.password, method='pbkdf2:sha256')

    user_create = UserCreate(
        email=user_data.email,
        name=user_data.name,
        birthday_date=user_data.birthday_date,
    )

    new_user = UserORM(
        **user_create.model_dump(),
        password_hash = hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

