#!/usr/bin/env python3
"""Pull 2026 schedules/results from Varsity Maine for Western Maine coverage.

This script is intentionally SAFE: it does NOT modify js/data.js.
It writes varsitymaine_schedule.json so the results can be reviewed before
being merged into the dashboard.

Source: https://www.varsitymaine.com/
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from sports_data import canonical_team, covered_teams
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE = "https://www.varsitymaine.com/school/{team}/{sport}"
OUT = Path(__file__).resolve().parent / "varsitymaine_schedule.json"

# The Western Maine Report coverage list: Oxford County schools + Poland.
# Slugs are Varsity Maine URL slugs.
TEAMS = {
    "Oxford Hills": "oxford-hills",
    "Poland Regional": "poland",
    "Fryeburg Academy": "fryeburg-academy",
    "Mountain Valley": "mountain-valley",
    "Telstar": "telstar",
    "Dirigo": "dirigo",
    "Buckfield": "buckfield",
    "Sacopee Valley": "sacopee-valley",
    "Gould Academy": "gould-academy",
}

SPORTS = {
    "Football": "football",
    "Boys Soccer": "boys-soccer",
    "Girls Soccer": "girls-soccer",
    "Field Hockey": "field-hockey",
    "Boys Cross Country": "boys-cross-country",
    "Girls Cross Country": "girls-cross-country",
    "Volleyball": "volleyball",
}

HEADERS = {
    "User-Agent": "Western-Maine-Sports-Dashboard/1.0 (personal project; contact via GitHub repo)"
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_date(value: str) -> tuple[str, str] | None:
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", value)
    if not m:
        return None
    mm, dd, yyyy = m.groups()
    if yyyy != "2026":
        return None
    dt = datetime(int(yyyy), int(mm), int(dd))
    return dt.strftime("%b %-d, %Y"), f"{int(mm)}.{int(dd)}.{yyyy}"


def split_score_game(game: str, focus_team: str):
    """Turn 'Oxford Hills 34, Lewiston 0' into away/home where possible."""
    # Drop overtime/period notes after the second score.
    m = re.match(r"^(.+?)\s+(\d+),\s+(.+?)\s+(\d+)(?:,.*)?$", game)
    if not m:
        return None
    left, _, right, _ = m.groups()
    left = clean(left)
    right = clean(right)
    if canonical_team(focus_team) == canonical_team(left):
        return left, right
    if canonical_team(focus_team) == canonical_team(right):
        return left, right
    return None


def parse_game(game: str, focus_team: str):
    game = clean(game)
    if not game:
        return None

    if " at " in game:
        away, home = [clean(x) for x in game.split(" at ", 1)]
        return away, home, False

    scored = split_score_game(game, focus_team)
    if scored:
        away, home = scored
        return away, home, True

    # Cross-country meets and unusual combined-team entries are retained as
    # a meet-style item rather than discarded.
    return game, focus_team, True


def read_tables(url: str):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return pd.read_html(response.text)


def main():
    records = []
    warnings = []
    seen = set()

    session = requests.Session()
    session.headers.update(HEADERS)

    for display_team, slug in TEAMS.items():
        for sport, sport_slug in SPORTS.items():
            url = BASE.format(team=quote(slug), sport=quote(sport_slug))
            print(f"Checking {display_team} — {sport}")
            try:
                response = session.get(url, timeout=30)
                if response.status_code == 404:
                    warnings.append(f"404: {url}")
                    continue
                response.raise_for_status()
                tables = pd.read_html(response.text)
            except Exception as exc:
                warnings.append(f"{url} -> {type(exc).__name__}: {exc}")
                continue

            table = None
            for candidate in tables:
                cols = [clean(c).lower() for c in candidate.columns]
                if "date" in cols and "game" in cols:
                    table = candidate
                    break
            if table is None:
                continue

            for _, row in table.iterrows():
                date_info = parse_date(clean(row.get("Date", "")))
                if not date_info:
                    continue
                pretty_date, raw_date = date_info
                game = clean(row.get("Game", ""))
                parsed = parse_game(game, display_team)
                if not parsed:
                    continue
                away, home, completed = parsed
                away, home = canonical_team(away), canonical_team(home)
                clock = clean(row.get("Time", "")) or "TBA"
                result = clean(row.get("W/L/T", ""))

                key = (sport, raw_date, away, home, clock)
                if key in seen:
                    continue
                seen.add(key)

                event_type = "game"
                if "Cross Country" in sport and " at " not in game and not re.search(r"\d+,.*\d+", game):
                    event_type = "meet"

                month, day, year = map(int, raw_date.split('.'))
                entry = {
                    "sport": "Cross Country" if "Cross Country" in sport else sport,
                    "gender": "Boys" if sport.startswith("Boys") else ("Girls" if sport.startswith("Girls") or sport == "Field Hockey" or sport == "Volleyball" else "Boys"),
                    "date": pretty_date,
                    "dateRaw": raw_date,
                    "dateISO": f"{year:04d}-{month:02d}-{day:02d}",
                    "away": away,
                    "home": home,
                    "time": clock,
                    "result": result,
                    "completed": completed,
                    "eventType": event_type,
                    "coveredTeam": display_team,
                    "region": "Western ME",
                    "source": "Varsity Maine",
                    "sourceUrl": url,
                    "checked": datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
                    "verification": "pending",
                    "venueKnown": not completed and ' at ' in game,
                }
                score = re.match(r'^(.+?)\s+(\d+),\s+(.+?)\s+(\d+)(?:,.*)?$', game)
                if completed and score:
                    entry.update(awayScore=int(score.group(2)), homeScore=int(score.group(4)))
                entry['coveredTeams'] = covered_teams(entry)
                if entry['coveredTeams']:
                    records.append(entry)
            time.sleep(0.15)

    records.sort(key=lambda r: (r["dateISO"], r["sport"], r["away"], r["home"]))

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "source": "Varsity Maine",
        "publicationStatus": "Unreviewed candidates — not for publication",
        "sourceUrl": "https://www.varsitymaine.com/daily-scores-and-schedules-combined",
        "recordCount": len(records),
        "warnings": warnings,
        "schedule": records,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(records)} records to {OUT}")
    if warnings:
        print(f"Warnings: {len(warnings)} — review them before publishing.")


if __name__ == "__main__":
    main()

