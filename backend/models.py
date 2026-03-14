from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from database import Base


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    track: Mapped[str] = mapped_column(String(32))
    day_of_week: Mapped[str] = mapped_column(String(16))
    week_start_date: Mapped[date] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(256))
    workout_type: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(4096))
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("track", "week_start_date", "day_of_week", name="uq_track_week_day"),
    )


class WorkoutResponse(BaseModel):
    id: int
    track: str
    day_of_week: str
    week_start_date: date
    title: str
    workout_type: str
    description: str
    scraped_at: datetime

    model_config = {"from_attributes": True}
