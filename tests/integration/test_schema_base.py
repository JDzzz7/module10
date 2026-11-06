# Tests for the schema base module in the FastAPI application.

import pytest
from pydantic import ValidationError

from app.schemas.base import (
    UserBase,
    PasswordMixin,
    UserCreate,
    UserLogin
)


def test_user_base_accepts_valid_information():
    user = UserBase(
        first_name="Taylor",
        last_name="Smith",
        email="taylor.smith@example.com",
        username="taylorsmith"
    )

    assert user.first_name == "Taylor"
    assert user.last_name == "Smith"
    assert user.email == "taylor.smith@example.com"
    assert user.username == "taylorsmith"


def test_user_base_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserBase(
            first_name="Taylor",
            last_name="Smith",
            email="not-an-email",
            username="taylorsmith"
        )


def test_user_base_rejects_short_username():
    with pytest.raises(ValidationError):
        UserBase(
            first_name="Taylor",
            last_name="Smith",
            email="taylor.smith@example.com",
            username="ts"
        )


def test_user_base_rejects_long_first_name():
    with pytest.raises(ValidationError):
        UserBase(
            first_name="T" * 51,
            last_name="Smith",
            email="taylor.smith@example.com",
            username="taylorsmith"
        )


def test_password_mixin_accepts_valid_password():
    password = PasswordMixin(password="SecurePass123")

    assert password.password == "SecurePass123"


def test_password_mixin_rejects_short_password():
    with pytest.raises(ValidationError):
        PasswordMixin(password="Ab123")


def test_password_mixin_requires_uppercase():
    with pytest.raises(
        ValidationError,
        match="Password must contain at least one uppercase letter"
    ):
        PasswordMixin(password="securepass123")


def test_password_mixin_requires_lowercase():
    with pytest.raises(
        ValidationError,
        match="Password must contain at least one lowercase letter"
    ):
        PasswordMixin(password="SECUREPASS123")


def test_password_mixin_requires_digit():
    with pytest.raises(
        ValidationError,
        match="Password must contain at least one digit"
    ):
        PasswordMixin(password="SecurePassword")


def test_password_mixin_rejects_password_over_maximum_length():
    with pytest.raises(ValidationError):
        PasswordMixin(password="A" + "b" * 127 + "1")


def test_user_create_combines_user_and_password_fields():
    user = UserCreate(
        first_name="Morgan",
        last_name="Holland",
        email="morgan.holland@example.com",
        username="morganholland",
        password="SecurePass123"
    )

    assert user.username == "morganholland"
    assert user.password == "SecurePass123"
    assert user.email == "morgan.holland@example.com"


def test_user_create_rejects_invalid_password():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="Morgan",
            last_name="Holland",
            email="morgan.holland@example.com",
            username="morganholland",
            password="weak"
        )


def test_user_login_accepts_valid_credentials():
    login = UserLogin(
        username="morganholland",
        password="SecurePass123"
    )

    assert login.username == "morganholland"
    assert login.password == "SecurePass123"


def test_user_login_rejects_short_username():
    with pytest.raises(ValidationError):
        UserLogin(
            username="ml",
            password="SecurePass123"
        )


def test_user_login_rejects_invalid_password():
    with pytest.raises(ValidationError):
        UserLogin(
            username="morganholland",
            password="weak"
        )