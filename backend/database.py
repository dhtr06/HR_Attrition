import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
sqlite_fallback_path = BASE_DIR / 'hr_attrition.db'
default_url = f"sqlite:///{sqlite_fallback_path.as_posix()}"

URL = os.getenv('DATABASE_URL', default_url)

engine = None
SessionLocal = None

def init_database():
    global engine, SessionLocal
    try:
        if URL.startswith('mysql'):
            temp_engine = create_engine(URL, pool_pre_ping=True, connect_args={'connect_timeout': 1})
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine = temp_engine
            print(f"[Database] Successfully connected to MySQL: {URL.split('@')[-1]}")
        else:
            engine = create_engine(URL, connect_args={"check_same_thread": False})
            print(f"[Database] Connected to SQLite database: {URL}")
    except Exception as e:
        print(f"[Database] MySQL connection failed ({e}). Falling back to local SQLite.")
        engine = create_engine(default_url, connect_args={"check_same_thread": False})
        print(f"[Database] Active database: {default_url}")

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

init_database()

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
