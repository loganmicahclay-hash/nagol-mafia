
import pytest

from app import create_app
from database import db


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()

        yield app.test_client()

        db.session.remove()
        db.engine.dispose()
