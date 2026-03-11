import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module  # import the module so we can access the data
from src.app import app  # import the FastAPI instance from the module

# fixture to reset the in-memory activities before each test
def pytest_configure(config):
    # ensure the pythonpath includes src if necessary (pytest.ini already sets this)
    pass


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: keep activities clean between tests by resetting the module-level data."""
    # activities live in the module, not on the FastAPI object
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = copy.deepcopy(original)


def test_root_redirects_to_static():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    # FastAPI returns a redirect response object with location header
    assert response.url.path == "/static/index.html"


def test_get_activities_returns_all():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_success_and_duplicate_and_not_found():
    # Arrange
    client = TestClient(app)
    activity = next(iter(app_module.activities))  # grab first activity name
    email = "new@student.com"

    # Act - successful signup
    resp1 = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp1.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # Act - duplicate signup
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Student already signed up for this activity"

    # Act - nonexistent activity
    resp3 = client.post(f"/activities/NotAnActivity/signup", params={"email": email})
    # Assert
    assert resp3.status_code == 404
    assert resp3.json()["detail"] == "Activity not found"


def test_unregister_success_and_not_registered_and_not_found():
    # Arrange
    client = TestClient(app)
    activity = next(iter(app_module.activities))
    email = "temp@student.com"
    # first sign up so we can remove it
    client.post(f"/activities/{activity}/signup", params={"email": email})

    # Act - successful unregister
    resp1 = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp1.status_code == 200
    assert email not in app_module.activities[activity]["participants"]

    # Act - not registered
    resp2 = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Student not registered for this activity"

    # Act - nonexistent activity
    resp3 = client.delete(f"/activities/NotAnActivity/signup", params={"email": email})
    # Assert
    assert resp3.status_code == 404
    assert resp3.json()["detail"] == "Activity not found"
