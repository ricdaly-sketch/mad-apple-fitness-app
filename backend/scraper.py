import logging
from datetime import date, timedelta
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)

PUSHPRESS_URL = "https://train.pushpress.com/widgets/workoutOfDay?tenantId=63104D1E-CFCE-4AFE-BA0B-7AB2FC96FD07"

# Used externally by main.py
WOD_URL = PUSHPRESS_URL

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Section headers that mark the start of each track in PushPress output.
# WOD header starts with "**" artifact from the widget.
TRACK_HEADERS = {
    "wod": ["workout of the day"],
    "competitor": ["competitor track"],
    "hyrox": ["hyrox"],
}


@dataclass
class ScrapedWorkout:
    track: str
    day_of_week: str
    week_start_date: date
    title: str
    workout_type: str
    description: str


def _current_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def _parse_tracks_from_lines(lines: list[str]) -> dict[str, str]:
    """
    Given the text lines for a single day, split into per-track content.
    Returns dict mapping track key -> block of text.
    """
    current_track = None
    track_lines: dict[str, list[str]] = {"wod": [], "competitor": [], "hyrox": []}

    for line in lines:
        low = line.lower().strip().lstrip("*").strip()
        matched = False
        for track, headers in TRACK_HEADERS.items():
            if any(low == h for h in headers):
                current_track = track
                matched = True
                break
        if matched:
            continue
        if current_track:
            track_lines[current_track].append(line)

    return {t: "\n".join(ls).strip() for t, ls in track_lines.items() if ls}


def _infer_workout_type(text: str) -> str:
    upper = text.upper()
    for kw in ["AMRAP", "FOR TIME", "EMOM", "STRENGTH", "SKILL", "CHIPPER", "TABATA", "HYROX"]:
        if kw in upper:
            return kw.title()
    return "WOD"


async def _scrape_day(page: Page, day: str, week_start: date) -> list[ScrapedWorkout]:
    """Click the tab for `day`, wait for content, then extract all tracks."""
    try:
        tab = page.locator(f"div.day-label:has-text('{day}'), button:has-text('{day}'), .tab:has-text('{day}')")
        # PushPress uses mat-button tabs — find by text
        tab = page.get_by_role("tab", name=day)
        if await tab.count() == 0:
            # Fallback: any clickable element with day text
            tab = page.locator(f"text={day}").first
        await tab.click()
        await page.wait_for_timeout(2000)
    except Exception as e:
        logger.warning("Could not click tab for %s: %s", day, e)

    content = await page.inner_text("body")
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    # Drop navigation header lines (chevron, date, day tabs)
    # Content starts after the last day-of-week tab label
    start_idx = 0
    for i, line in enumerate(lines):
        if line in DAYS_OF_WEEK:
            start_idx = i + 1  # keep updating; after last tab label is content
    content_lines = lines[start_idx:]

    track_content = _parse_tracks_from_lines(content_lines)
    workouts = []
    for track, text in track_content.items():
        if not text:
            continue
        first_line = text.splitlines()[0] if text else ""
        workouts.append(ScrapedWorkout(
            track=track,
            day_of_week=day,
            week_start_date=week_start,
            title=first_line[:256],
            workout_type=_infer_workout_type(text),
            description=text[:4096],
        ))
    logger.info("Day %s: extracted %d tracks", day, len(workouts))
    return workouts


async def scrape_all_tracks() -> list[ScrapedWorkout]:
    """
    Main entry point. Loads PushPress widget, iterates through each day tab,
    and extracts workouts for all three tracks.
    """
    week_start = _current_week_monday()
    all_workouts: list[ScrapedWorkout] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 2400},
        )
        page = await context.new_page()
        logger.info("Loading PushPress widget")
        await page.goto(PUSHPRESS_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(5000)

        for day in DAYS_OF_WEEK:
            try:
                workouts = await _scrape_day(page, day, week_start)
                all_workouts.extend(workouts)
            except Exception as exc:
                logger.error("Failed to scrape day '%s': %s", day, exc)

        await browser.close()

    logger.info("Total workouts scraped: %d", len(all_workouts))
    return all_workouts
