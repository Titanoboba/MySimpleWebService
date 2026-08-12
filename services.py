from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session
from models import UserORM
from schemas import UserRegistration, UserCreate

"""
The purpose of this file is to perform some tasks for database. Function create_user
will take information from UserRegistration pydantic model and create ORM user with hashed password
"""

def hash_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256')

def create_user(user_data: UserRegistration) -> UserORM:
    hashed_password = hash_password(user_data.password)

    user_create = UserCreate(
        email=user_data.email,
        username=user_data.username,
        birthday_date=user_data.birthday_date,
    )

    user = UserORM(
        **user_create.model_dump(),
        password_hash = hashed_password
    )

    return user

def add_user(db: Session, user_data: UserRegistration) -> UserORM:

    new_user = create_user(user_data)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(db: Session, update_dict: dict, user_id: int) -> UserORM:
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    for key, value in update_dict.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
