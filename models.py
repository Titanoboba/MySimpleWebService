from database import Base
from sqlalchemy import Column, Integer, String, Date

class UserORM(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    email = Column(String(45), nullable=False)
    birthday_date = Column(Date, nullable=False)