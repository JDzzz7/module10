# Tests for the user authentication dependencies in the FastAPI application.

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.auth.dependencies import (
    get_current_user,
    get_current_active_user
)
from app.models.user import User
from app.schemas.user import UserResponse


@pytest.fixture
def active_user():
    return User(
        id=uuid4(),
        first_name="Taylor",
        last_name="Smith",
        email="taylor.smith@example.com",
        username="taylorsmith",
        password="HashedPassword123",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def inactive_user():
    return User(
        id=uuid4(),
        first_name="Morgan",
        last_name="Holland",
        email="morgan.holland@example.com",
        username="morganholland",
        password="HashedPassword123",
        is_active=False,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_database():
    return MagicMock()


def test_get_current_user_returns_user_response(
    mock_database, active_user
):
    with patch.object(User, "verify_token", return_value=active_user.id) as verify:
        mock_database.query.return_value.filter.return_value.first.return_value = active_user

        result = get_current_user(
            db=mock_database,
            token="valid-token"
        )

    assert isinstance(result, UserResponse)
    assert result.id == active_user.id
    assert result.username == active_user.username
    assert result.email == active_user.email

    verify.assert_called_once_with("valid-token")
    mock_database.query.assert_called_once_with(User)


def test_get_current_user_rejects_invalid_token(mock_database):
    with patch.object(User, "verify_token", return_value=None) as verify:
        with pytest.raises(HTTPException) as error:
            get_current_user(
                db=mock_database,
                token="invalid-token"
            )

    assert error.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert error.value.detail == "Could not validate credentials"
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}

    verify.assert_called_once_with("invalid-token")
    mock_database.query.assert_not_called()


def test_get_current_user_rejects_user_not_found(
    mock_database, active_user
):
    with patch.object(User, "verify_token", return_value=active_user.id):
        mock_database.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as error:
            get_current_user(
                db=mock_database,
                token="valid-token"
            )

    assert error.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert error.value.detail == "Could not validate credentials"


def test_get_current_active_user_accepts_active_account(active_user):
    response = UserResponse.model_validate(active_user)

    result = get_current_active_user(current_user=response)

    assert result is response
    assert result.is_active is True


def test_get_current_active_user_rejects_inactive_account(inactive_user):
    response = UserResponse.model_validate(inactive_user)

    with pytest.raises(HTTPException) as error:
        get_current_active_user(current_user=response)

    assert error.value.status_code == status.HTTP_400_BAD_REQUEST
    assert error.value.detail == "Inactive user"
