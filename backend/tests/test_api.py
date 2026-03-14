import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from models import Workout
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def _monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def _seed_workout(track: str = "wod") -> Workout:
    db = TestingSessionLocal()
    w = Workout(
        track=track,
        day_of_week="Monday",
        week_start_date=_monday(),
        title="AMRAP 20 min",
        workout_type="AMRAP",
        description="5 Pull-ups\n10 Push-ups\n15 Squats",
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    db.close()
    return w


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_week_workouts_returns_data(client):
    _seed_workout("wod")
    response = client.get("/workouts/week?track=wod")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["track"] == "wod"
    assert data[0]["title"] == "AMRAP 20 min"


def test_get_week_workouts_no_data(client):
    response = client.get("/workouts/week?track=wod")
    assert response.status_code == 503


def test_get_workout_by_id(client):
    w = _seed_workout("competitor")
    response = client.get(f"/workouts/{w.id}")
    assert response.status_code == 200
    assert response.json()["track"] == "competitor"


def test_get_workout_not_found(client):
    response = client.get("/workouts/9999")
    assert response.status_code == 404


def test_admin_scrape_forbidden(client):
    response = client.post("/admin/scrape", headers={"x-admin-secret": "wrong"})
    assert response.status_code == 403


def test_get_week_workouts_filters_by_track(client):
    _seed_workout("wod")
    _seed_workout("hyrox")
    response = client.get("/workouts/week?track=hyrox")
    assert response.status_code == 200
    data = response.json()
    assert all(w["track"] == "hyrox" for w in data)
