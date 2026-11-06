# Test for user authentication and registration functionalities in the User model.

import pytest
from app.models.user import User


def test_password_is_hashed_and_verified():
    password = "SecurePass123"
    hashed_password = User.hash_password(password)

    user = User(
        first_name="Taylor",
        last_name="Smith",
        email="taylor.smith@example.com",
        username="taylorsmith",
        password=hashed_password
    )

    assert hashed_password != password
    assert user.verify_password(password) is True
    assert user.verify_password("Incorrect123") is False


def test_register_new_user(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    registered_user = User.register(db_session, fake_user_data)
    db_session.commit()
    db_session.refresh(registered_user)

    assert registered_user.id is not None
    assert registered_user.first_name == fake_user_data["first_name"]
    assert registered_user.last_name == fake_user_data["last_name"]
    assert registered_user.email == fake_user_data["email"]
    assert registered_user.username == fake_user_data["username"]
    assert registered_user.is_active is True
    assert registered_user.is_verified is False
    assert registered_user.verify_password("SecurePass123")


def test_registration_rejects_existing_email(db_session):
    first_data = {
        "first_name": "Henry",
        "last_name": "Parker",
        "email": "henry.parker@example.com",
        "username": "henryparker",
        "password": "SecurePass123"
    }

    second_data = {
        "first_name": "Morgan",
        "last_name": "Holland",
        "email": "henry.parker@example.com",
        "username": "morganholland",
        "password": "SecurePass123"
    }

    User.register(db_session, first_data)
    db_session.commit()

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, second_data)


def test_registration_rejects_existing_username(db_session):
    first_data = {
        "first_name": "Alex",
        "last_name": "Brown",
        "email": "alex.brown@example.com",
        "username": "alexbrown",
        "password": "SecurePass123"
    }

    second_data = {
        "first_name": "Chris",
        "last_name": "Green",
        "email": "chris.green@example.com",
        "username": "alexbrown",
        "password": "SecurePass123"
    }

    User.register(db_session, first_data)
    db_session.commit()

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, second_data)


def test_registration_rejects_short_password(db_session):
    user_data = {
        "first_name": "Jamie",
        "last_name": "Wilson",
        "email": "jamie.wilson@example.com",
        "username": "jamiewilson",
        "password": "Ab123"
    }

    with pytest.raises(
        ValueError,
        match="Password must be at least 6 characters long"
    ):
        User.register(db_session, user_data)


def test_registration_rejects_missing_password(db_session):
    user_data = {
        "first_name": "Casey",
        "last_name": "Jones",
        "email": "casey.jones@example.com",
        "username": "caseyjones"
    }

    with pytest.raises(
        ValueError,
        match="Password must be at least 6 characters long"
    ):
        User.register(db_session, user_data)


def test_authentication_with_username(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(
        db_session,
        fake_user_data["username"],
        "SecurePass123"
    )

    assert result is not None
    assert result["token_type"] == "bearer"
    assert "access_token" in result
    assert "user" in result


def test_authentication_with_email(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(
        db_session,
        fake_user_data["email"],
        "SecurePass123"
    )

    assert result is not None
    assert "access_token" in result


def test_authentication_rejects_wrong_password(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(
        db_session,
        fake_user_data["username"],
        "WrongPassword123"
    )

    assert result is None


def test_authentication_rejects_unknown_user(db_session):
    result = User.authenticate(
        db_session,
        "unknownuser",
        "SecurePass123"
    )

    assert result is None


def test_authentication_updates_last_login(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    user = User.register(db_session, fake_user_data)
    db_session.commit()

    assert user.last_login is None

    User.authenticate(
        db_session,
        fake_user_data["username"],
        "SecurePass123"
    )

    db_session.refresh(user)
    assert user.last_login is not None


def test_generated_token_can_be_verified(db_session, fake_user_data):
    fake_user_data["password"] = "SecurePass123"

    user = User.register(db_session, fake_user_data)
    db_session.commit()

    token = User.create_access_token({"sub": str(user.id)})
    verified_id = User.verify_token(token)

    assert verified_id == user.id


def test_invalid_token_returns_none():
    assert User.verify_token("not.a.valid.token") is None


def test_user_string_representation(test_user):
    expected = (
        f"<User(name={test_user.first_name} "
        f"{test_user.last_name}, email={test_user.email})>"
    )

    assert str(test_user) == expected
