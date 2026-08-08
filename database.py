from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("DB_USER, DB_PASSWORD, DB_NAME must be set")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

try:
    with engine.connect() as connection:
        print("Connected to MySQL database")
except Exception as e:
    print(f"Error during connection {e}")

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()