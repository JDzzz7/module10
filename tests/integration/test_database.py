# Tests for the database module in the FastAPI application.

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session
import importlib
import sys
from unittest.mock import MagicMock

DATABASE_MODULE = "app.database"

@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to mock the settings.DATABASE_URL before app.database is imported."""
    mock_url = "postgresql://user:password@localhost:5432/test_db"
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = mock_url
    # Ensure 'app.database' is not loaded
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    # Patch settings in 'app.database'
    monkeypatch.setattr(f"{DATABASE_MODULE}.settings", mock_settings)
    return mock_settings

def reload_database_module():
    """Helper function to reload the database module after patches."""
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    return importlib.import_module(DATABASE_MODULE)

def test_base_declaration(mock_settings):
    """Test that Base is an instance of declarative_base."""
    database = reload_database_module()
    Base = database.Base
    assert isinstance(Base, database.declarative_base().__class__)

def test_get_engine_success(mock_settings):
    """Test that get_engine returns a valid engine."""
    database = reload_database_module()
    engine = database.get_engine()
    assert isinstance(engine, Engine)

def test_get_engine_failure(mock_settings):
    """Test that get_engine raises an error if the engine cannot be created."""
    database = reload_database_module()
    with patch("app.database.create_engine", side_effect=SQLAlchemyError("Engine error")):
        with pytest.raises(SQLAlchemyError, match="Engine error"):
            database.get_engine()

def test_get_sessionmaker(mock_settings):
    """Test that get_sessionmaker returns a valid sessionmaker."""
    database = reload_database_module()
    engine = database.get_engine()
    SessionLocal = database.get_sessionmaker(engine)
    assert isinstance(SessionLocal, sessionmaker)
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import app.database as database


def test_get_engine_creates_engine():
    engine = database.get_engine("sqlite:///:memory:")

    try:
        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"
        assert engine.echo is True
    finally:
        engine.dispose()


def test_get_engine_propagates_sqlalchemy_error():
    with pytest.MonkeyPatch.context() as monkeypatch:
        def raise_database_error(*args, **kwargs):
            raise SQLAlchemyError("Unable to create engine")

        monkeypatch.setattr(database, "create_engine", raise_database_error)

        with pytest.raises(SQLAlchemyError):
            database.get_engine("invalid://database")


def test_get_sessionmaker_returns_session_factory():
    engine = create_engine("sqlite:///:memory:")

    try:
        session_factory = database.get_sessionmaker(engine)
        session = session_factory()

        assert isinstance(session, Session)
        assert session.bind is engine

        session.close()
    finally:
        engine.dispose()


def test_get_sessionmaker_disables_autocommit_and_autoflush():
    engine = create_engine("sqlite:///:memory:")

    try:
        session_factory = database.get_sessionmaker(engine)

        assert session_factory.kw["autocommit"] is False
        assert session_factory.kw["autoflush"] is False
        assert session_factory.kw["bind"] is engine
    finally:
        engine.dispose()


def test_get_db_yields_database_session(monkeypatch):
    mock_session = MagicMock()

    monkeypatch.setattr(
        database,
        "SessionLocal",
        lambda: mock_session
    )

    generator = database.get_db()
    yielded_session = next(generator)

    assert yielded_session is mock_session

    with pytest.raises(StopIteration):
        next(generator)

    mock_session.close.assert_called_once()


def test_get_db_closes_session_after_use(monkeypatch):
    mock_session = MagicMock()

    monkeypatch.setattr(
        database,
        "SessionLocal",
        lambda: mock_session
    )

    generator = database.get_db()
    next(generator)

    generator.close()

    mock_session.close.assert_called_once()
