import logging
from datetime import date, timedelta
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)

TRACK_LABELS = {
    "wod": "Workout of the Day",
    "competitor": "Competitor Track",
    "hyrox": "Hyrox",
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

WOD_URL = "https://madapplefitness.com/workout-of-the-day/"


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


async def _select_track(page: Page, track: str) -> bool:
    """
    Attempt to select a track on the page. The site uses Divi + JS so we look
    for tabs, buttons, or links whose text matches the track label.
    Returns True if found and clicked, False otherwise.
    """
    label = TRACK_LABELS[track]
    # Try common patterns: tab buttons, anchor links, dropdown items
    selectors = [
        f"text={label}",
        f"[data-track='{track}']",
        f"button:has-text('{label}')",
        f"a:has-text('{label}')",
        f"li:has-text('{label}')",
        f".tab:has-text('{label}')",
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if await el.count() > 0:
                await el.click()
                await page.wait_for_load_state("networkidle", timeout=5000)
                logger.info("Selected track '%s' via selector: %s", label, selector)
                return True
        except Exception:
            continue
    logger.warning("Could not find track selector for '%s' — will scrape visible content", label)
    return False


async def _extract_workouts_from_page(page: Page, track: str, week_start: date) -> list[ScrapedWorkout]:
    """
    Extract workouts from the currently visible page content.
    Looks for day headings followed by workout blocks.
    """
    workouts: list[ScrapedWorkout] = []

    # Get all text blocks — we'll parse them looking for day names
    content = await page.inner_text("body")
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    current_day = None
    current_lines: list[str] = []

    def flush_day(day: str, block_lines: list[str]) -> None:
        if not block_lines:
            return
        # First non-empty line is the title/type, rest is description
        title_line = block_lines[0]
        description = "\n".join(block_lines)

        # Infer workout_type from common keywords in the title
        workout_type = "WOD"
        title_upper = title_line.upper()
        for kw in ["AMRAP", "FOR TIME", "EMOM", "STRENGTH", "SKILL", "HYROX", "CHIPPER", "TABATA"]:
            if kw in title_upper:
                workout_type = kw.title()
                break

        workouts.append(ScrapedWorkout(
            track=track,
            day_of_week=day,
            week_start_date=week_start,
            title=title_line[:256],
            workout_type=workout_type,
            description=description[:4096],
        ))

    for line in lines:
        # Check if line is a day heading
        line_title = line.strip().rstrip(":").strip()
        if line_title in DAYS_OF_WEEK:
            if current_day and current_lines:
                flush_day(current_day, current_lines)
            current_day = line_title
            current_lines = []
        elif current_day:
            current_lines.append(line)

    # Flush last day
    if current_day and current_lines:
        flush_day(current_day, current_lines)

    logger.info("Extracted %d workouts for track '%s'", len(workouts), track)
    return workouts


async def scrape_all_tracks() -> list[ScrapedWorkout]:
    """
    Main entry point. Scrapes all three tracks and returns a flat list of ScrapedWorkout objects.
    """
    week_start = _current_week_monday()
    all_workouts: list[ScrapedWorkout] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; MadAppleFitnessBot/1.0)"
        )

        for track in TRACK_LABELS:
            try:
                page = await context.new_page()
                logger.info("Loading WOD page for track: %s", track)
                await page.goto(WOD_URL, wait_until="networkidle", timeout=30000)

                # Only try to switch track if it's not WOD (default view)
                if track != "wod":
                    await _select_track(page, track)

                workouts = await _extract_workouts_from_page(page, track, week_start)
                all_workouts.extend(workouts)
                await page.close()
            except Exception as exc:
                logger.error("Failed to scrape track '%s': %s", track, exc)

        await browser.close()

    return all_workouts
