import os

import pytest
from fastapi.testclient import TestClient
from polygon.rest.models import DailyOpenCloseAgg
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import Session, SQLModel, create_engine

from app.databases import get_redis
from app.main import app, get_db

POSTGRES_URL = os.getenv("POSTGRES_TEST_URL")

# engine = create_engine(POSTGRES_URL)
# TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(POSTGRES_URL)
    if not database_exists(engine.url):
        create_database(engine.url)

    SQLModel.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()

    # begin a non-ORM transaction
    transaction = connection.begin()

    # bind an individual Session to the connection
    db = Session(bind=connection)

    try:
        yield db
    finally:
        transaction.rollback()
        db.rollback()
        connection.close()


@pytest.fixture(scope="function")
def test_client(db):
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as c:
        yield c


@pytest.fixture
def redis():
    cli = get_redis()
    cli.flushdb()
    yield cli
    cli.flushdb()


@pytest.fixture
def mock_polygon_get_daily_open_close_agg(mocker):
    # setup
    old_api_key = os.environ.get("POLYGON_API_KEY", None)
    os.environ["POLYGON_API_KEY"] = "some key"
    # yield
    yield mocker.patch(
        "app.polygon_cli.RESTClient.get_daily_open_close_agg",
        return_value=DailyOpenCloseAgg(
            after_hours=207.91,
            close=223.89,
            from_="2025-04-02",
            high=225.19,
            low=221.02,
            open=221.315,
            pre_market=222.82,
            status="OK",
            symbol="AAPL",
            volume=35905904.0,
        ),
    )
    # teardown
    if old_api_key is None:
        os.environ.pop("POLYGON_API_KEY")
    else:
        os.environ["POLYGON_API_KEY"] = old_api_key
