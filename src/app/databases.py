import os

import redis
from sqlmodel import Session, SQLModel, create_engine

POSTGRES_URL = os.getenv("POSTGRES_URL")
REDIS_URL = os.getenv("REDIS_URL")
engine = create_engine(POSTGRES_URL, echo=True, connect_args={"connect_timeout": 5})
SessionLocal = Session(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()


def create_pg_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_redis():
    return redis.from_url(REDIS_URL)
