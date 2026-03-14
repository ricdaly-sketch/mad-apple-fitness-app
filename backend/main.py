import logging
import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database import get_db, create_tables
from models import Workout, WorkoutResponse
from scraper import scrape_all_tracks
from scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


async def run_scrape_and_upsert() -> None:
    """Scrape all tracks and upsert into the database."""
    from database import SessionLocal

    logger.info("Running scheduled scrape...")
    workouts = await scrape_all_tracks()
    if not workouts:
        logger.warning("Scrape returned no workouts")
        return

    db = SessionLocal()
    try:
        for w in workouts:
            stmt = (
                sqlite_insert(Workout)
                .values(
                    track=w.track,
                    day_of_week=w.day_of_week,
                    week_start_date=w.week_start_date,
                    title=w.title,
                    workout_type=w.workout_type,
                    description=w.description,
                )
                .on_conflict_do_update(
                    index_elements=["track", "week_start_date", "day_of_week"],
                    set_={
                        "title": w.title,
                        "workout_type": w.workout_type,
                        "description": w.description,
                    },
                )
            )
            db.execute(stmt)
        db.commit()
        logger.info("Upserted %d workouts into database", len(workouts))
    except Exception as exc:
        db.rollback()
        logger.error("DB upsert failed: %s", exc)
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    start_scheduler(run_scrape_and_upsert)
    yield
    stop_scheduler()


app = FastAPI(title="Mad Apple Fitness API", lifespan=lifespan)


def _current_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/workouts/week", response_model=list[WorkoutResponse])
def get_week_workouts(
    track: str = Query(..., description="Track: wod | competitor | hyrox"),
    db: Session = Depends(get_db),
):
    week_start = _current_week_monday()
    workouts = (
        db.query(Workout)
        .filter(Workout.track == track, Workout.week_start_date == week_start)
        .order_by(Workout.id)
        .all()
    )
    if not workouts:
        raise HTTPException(status_code=503, detail="No workouts available for this week yet")
    return workouts


@app.get("/workouts/{workout_id}", response_model=WorkoutResponse)
def get_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@app.post("/admin/scrape", status_code=202)
async def admin_scrape(x_admin_secret: str = Header(...)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    import asyncio
    asyncio.create_task(run_scrape_and_upsert())
    return {"message": "Scrape triggered"}


@app.get("/admin/debug-page")
async def debug_page(x_admin_secret: str = Header(...)):
    """Return raw page text from the WOD URL to help debug scraper issues."""
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    from playwright.async_api import async_playwright
    from scraper import WOD_URL
    import httpx

    KEYWORDS = ["monday", "tuesday", "wednesday", "thursday", "friday", "amrap", "emom", "for time", "strength", "workout", "competitor", "hyrox"]
    raw_keyword_hits = []
    wp_page_result = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
            r = await client.get(WOD_URL)
            for i, line in enumerate(r.text.splitlines()):
                if any(kw in line.lower() for kw in KEYWORDS):
                    raw_keyword_hits.append({"line": i, "text": line.strip()[:400]})
            r2 = await client.get("https://madapplefitness.com/wp-json/wp/v2/pages/247?_fields=title,content")
            wp_page_result = r2.json() if r2.status_code == 200 else {"status": r2.status_code}
    except Exception as e:
        raw_keyword_hits = [{"error": str(e)}]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.goto(WOD_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(8000)
        content = await page.inner_text("body")
        await browser.close()
    pw_lines = [l.strip() for l in content.splitlines() if l.strip()]
    return {
        "playwright_line_count": len(pw_lines),
        "playwright_lines": pw_lines[:100],
        "raw_keyword_hits": raw_keyword_hits[:30],
        "wp_page_247": wp_page_result,
    }
