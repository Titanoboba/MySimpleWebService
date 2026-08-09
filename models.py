from database import Base
from sqlalchemy import Column, Integer, String, Date

class UserORM(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(45), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    birthday_date = Column(Date, nullable=False)
    password_hash = Column(String(128), nullable=False)