from datetime import date
from scraper import ScrapedWorkout, _current_week_monday, DAYS_OF_WEEK, TRACK_LABELS


def test_current_week_monday_is_monday():
    monday = _current_week_monday()
    assert monday.weekday() == 0


def test_scraped_workout_dataclass():
    w = ScrapedWorkout(
        track="wod",
        day_of_week="Monday",
        week_start_date=date.today(),
        title="AMRAP 20 min",
        workout_type="AMRAP",
        description="5 Pull-ups",
    )
    assert w.track == "wod"
    assert w.workout_type == "AMRAP"


def test_track_labels_cover_all_tracks():
    assert set(TRACK_LABELS.keys()) == {"wod", "competitor", "hyrox"}


def test_days_of_week_complete():
    assert len(DAYS_OF_WEEK) == 7
    assert DAYS_OF_WEEK[0] == "Monday"
    assert DAYS_OF_WEEK[6] == "Sunday"
