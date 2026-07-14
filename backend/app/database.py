from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # keep 5 connections open and ready
    max_overflow=10,      # allow up to 10 more under burst load
    pool_pre_ping=True,   # check connection is alive before using it (avoids stale-connection errors)
    pool_recycle=1800,    # recycle connections every 30 min (Neon/cloud DBs often close idle connections)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()