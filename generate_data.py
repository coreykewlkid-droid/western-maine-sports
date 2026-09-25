#!/usr/bin/env python3
"""Generate js/data.js for the Western Maine 2026 Fall Sports Dashboard.
All data sourced from MPA bulletins, downtownme.com 2026-2027 schedules,
Fryeburg Academy athletics, and Sun Journal / Central Maine / Press Herald
'players to watch' features. See sources in the sources section."""
import json, re

# ---------------------------------------------------------------------------
# FOOTBALL SCHEDULE (2026) — parsed from downtownme.com sports.asp
# Format: "9.3.2026 | Lawrence at Gorham | 6 pm"
# ---------------------------------------------------------------------------
RAW_FOOTBALL = """
9.3.2026 | Lawrence at Gorham | 6 pm
9.3.2026 | Cheverus/Waynflete at Westbrook | 6 pm
9.3.2026 | Marshwood at Sanford | 6 pm
9.3.2026 | Brunswick at Biddeford | 6 pm
9.3.2026 | Falmouth at Kennebunk | 6 pm
9.4.2026 | Edward Little at Deering | 6 pm
9.4.2026 | Oxford Hills/Buckfield at Windham | 6 pm
9.4.2026 | Cony at Fryeburg Academy | 6:30 pm
9.4.2026 | Winslow at Wells | 6:30 pm
9.4.2026 | Nokomis at Gardiner | 7 pm
9.4.2026 | South Portland at Bonny Eagle | 7 pm
9.4.2026 | Brewer at Belfast | 7 pm
9.4.2026 | Camden Hills at Messalonskee | 7 pm
9.4.2026 | Skowhegan at Mount Blue | 7 pm
9.4.2026 | Scarborough at Thornton Academy | 7 pm
9.4.2026 | Dover at Noble | 7 pm
9.4.2026 | Oak Hill at Maine Central Institute | 7 pm
9.4.2026 | Foxcroft Academy at Hermon | 7 pm
9.4.2026 | Portland at Lewiston | 7 pm
9.4.2026 | Hampden Academy at Oceanside/North Haven | 7 pm
9.4.2026 | Massabesic at Bangor | 7 pm
9.4.2026 | Lisbon at Winthrop | 7 pm
9.4.2026 | John Bapst/Bangor Christian at Madison | 7 pm
9.4.2026 | Morse at Mountain Valley | 7 pm
9.4.2026 | Medomak Valley at Leavitt | 7 pm
9.4.2026 | Poland Regional at Dirigo | 7 pm
9.4.2026 | York at Greely | 7:30 pm
9.5.2026 | Mattanawcook Academy at Freeport | 1 pm
9.10.2026 | Leavitt at Greely | 7 pm
9.11.2026 | Salem at Edward Little | 7 pm
9.11.2026 | Wells at Medomak Valley | 7 pm
9.11.2026 | Bonny Eagle at Noble | 7 pm
9.11.2026 | Madison at Lisbon | TBA
9.11.2026 | Gardiner at York | 6 pm
9.11.2026 | Messalonskee at Brunswick | 6 pm
9.11.2026 | Westbrook at Marshwood | 6 pm
9.11.2026 | Sanford at Windham | 6 pm
9.11.2026 | Winthrop at Freeport | 6 pm
9.11.2026 | Gorham at Biddeford | 6 pm
9.11.2026 | Morse at Dirigo | 7 pm
9.11.2026 | Oceanside/North Haven at Foxcroft Academy | 7 pm
9.11.2026 | Thornton Academy at South Portland | 7 pm
9.11.2026 | Hampden Academy at Brewer | 7 pm
9.11.2026 | Portland at Scarborough | 7 pm
9.11.2026 | Fryeburg Academy at Lawrence | 7 pm
9.11.2026 | Mountain Valley at Mattanawcook Academy | 7 pm
9.11.2026 | Skowhegan at Cony | 7 pm
9.11.2026 | Bangor at Lewiston | 7 pm
9.11.2026 | Deering at Oxford Hills/Buckfield | 7 pm
9.11.2026 | Maine Central Institute at Poland Regional | 7 pm
9.11.2026 | Kennebunk at Massabesic | 7 pm
9.12.2026 | Belfast at Oak Hill | 1 pm
9.12.2026 | Hermon at Nokomis | 1 pm
9.12.2026 | Mount Blue at Camden Hills | 1 pm
9.12.2026 | Falmouth at Cheverus/Waynflete | 12:30 pm
9.17.2026 | Madison at Winthrop | 7 pm
9.18.2026 | Fryeburg Academy at Brunswick | 6 pm
9.18.2026 | Bangor at Deering | 6 pm
9.18.2026 | Leavitt at York | 6 pm
9.18.2026 | Windham at Portland | 6 pm
9.18.2026 | Marshwood at Gorham | 6:30 pm
9.18.2026 | Westbrook at Falmouth | 6:30 pm
9.18.2026 | Freeport at Poland Regional | 7 pm
9.18.2026 | Bonny Eagle at Massabesic | 7 pm
9.18.2026 | Edward Little at Oxford Hills/Buckfield | 7 pm
9.18.2026 | Cony at Mount Blue | 7 pm
9.18.2026 | South Portland at Scarborough | 7 pm
9.18.2026 | Sanford at Noble | 7 pm
9.18.2026 | Biddeford at Morse | 7 pm
9.18.2026 | Lawrence at Skowhegan | 7 pm
9.18.2026 | Mountain Valley at Lisbon | 7 pm
9.18.2026 | Gardiner at Foxcroft Academy | 7 pm
9.18.2026 | Hermon at Hampden Academy | 7 pm
9.18.2026 | Mattanawcook Academy at Maine Central Institute | 7 pm
9.19.2026 | Oak Hill at Winslow | 1 pm
9.19.2026 | Bedford at Thornton Academy | 1 pm
9.19.2026 | Kennebunk at Cheverus/Waynflete | 12:30 pm
9.23.2026 | Bangor at Sanford | 7 pm
9.24.2026 | Poland Regional at Winthrop | 7 pm
9.25.2026 | Windham at Bangor | 6 pm
9.25.2026 | Lewiston at Deering | 6 pm
9.25.2026 | Noble at Marshwood | 6 pm
9.25.2026 | Biddeford at Falmouth | 6:30 pm
9.25.2026 | Brunswick at Skowhegan | 7 pm
9.25.2026 | Brewer at Gardiner | 7 pm
9.25.2026 | Belfast at Mattanawcook Academy | 7 pm
9.25.2026 | Foxcroft Academy at Madison | 7 pm
9.25.2026 | Lawrence at Mount Blue | 7 pm
9.25.2026 | Thornton Academy at Westbrook | 7 pm
9.25.2026 | Medomak Valley at Hermon | 7 pm
9.25.2026 | Cheverus/Waynflete at South Portland | 7 pm
9.25.2026 | Lisbon at Morse | 7 pm
9.25.2026 | Scarborough at Bonny Eagle | 7 pm
9.25.2026 | Dirigo at Mountain Valley | 7 pm
9.25.2026 | Messalonskee at Cony | 7 pm
9.26.2026 | Freeport at Winslow | 1 pm
9.26.2026 | John Bapst/Bangor Christian at Oak Hill | 1 pm
9.26.2026 | Gorham at Kennebunk | 1 pm
9.26.2026 | Wells at Leavitt | 7 pm
10.1.2026 | Maine Central Institute at Madison | 7 pm
10.2.2026 | Bonny Eagle at Windham | 6 pm
10.2.2026 | Morse at Freeport | 6 pm
10.2.2026 | Deering at Kennebunk | 6 pm
10.2.2026 | Gardiner at Wells | 6:30 pm
10.2.2026 | Marshwood at Falmouth | 6:30 pm
10.2.2026 | South Portland at Sanford | 7 pm
10.2.2026 | Noble at Massabesic | 7 pm
10.2.2026 | Hermon at Oceanside | 7 pm
10.2.2026 | Scarborough at Edward Little | 7 pm
10.2.2026 | Belfast at Mountain Valley | 7 pm
10.2.2026 | Winslow at Mattanawcook Academy | 7 pm
10.2.2026 | Oxford Hills/Buckfield at Lewiston | 7 pm
10.2.2026 | Fryeburg Academy at Messalonskee | 7 pm
10.2.2026 | Lisbon at Poland Regional | 7 pm
"""

# Boys soccer (2026) — downtownme.com
RAW_BOYS_SOCCER = """
9.1.2026 | Hermon at Brewer | 5 pm
9.1.2026 | Ellsworth at Winslow | 5:30 pm
9.1.2026 | Hall-Dale at Oceanside | 4 pm
9.1.2026 | Mount Abram at Gardiner | 4 pm
9.1.2026 | Waterville at Morse | 4 pm
9.1.2026 | John Bapst at Orono | 4 pm
9.1.2026 | Medomak Valley at Mount View | 5 pm
9.1.2026 | Belfast at Messalonskee | 5 pm
9.1.2026 | Skowhegan at Gray-New Gloucester | 5:30 pm
9.1.2026 | Mt. Ararat at Westbrook | 6 pm
9.3.2026 | Scarborough at Falmouth | 6:30 pm
9.3.2026 | Old Town at Sumner | 4 pm
9.3.2026 | Richmond at Maranacook | 4 pm
9.3.2026 | Maine Central Institute at Nokomis | 3:30 pm
9.3.2026 | Hampden Academy at Camden Hills | 4 pm
9.3.2026 | Lisbon at Buckfield | 4 pm
9.3.2026 | Thornton Academy at Marshwood | 4:15 pm
9.3.2026 | North Yarmouth Academy at Freeport | 4:30 pm
9.3.2026 | Oak Hill at Winthrop | 6 pm
9.3.2026 | Cape Elizabeth at Yarmouth | 6 pm
9.3.2026 | York at Greely | 6 pm
9.3.2026 | Gray-New Gloucester at Lake Region | 6 pm
9.3.2026 | Fryeburg Academy at Wells | 6 pm
9.3.2026 | Belfast at Morse | 6 pm
9.3.2026 | Mountain Valley at Mount Abram | 6 pm
9.3.2026 | Leavitt at Gardiner | 6:30 pm
9.3.2026 | Windham at Deering | 7 pm
9.3.2026 | Brunswick at Brewer | 7 pm
9.4.2026 | Oceanside at Lincoln Academy | 6 pm
9.4.2026 | Skowhegan at Lawrence | 6 pm
9.4.2026 | Cheverus at Massabesic | 6 pm
9.4.2026 | Oxford Hills at Edward Little | 6 pm
9.4.2026 | South Portland at Gorham | 7 pm
"""

# Western-Maine-centric teams (for region tagging). Anything else = "Statewide".
WESTERN_TEAMS = {
    "Gorham","Westbrook","Marshwood","Sanford","Brunswick","Biddeford","Falmouth",
    "Kennebunk","Bonny Eagle","Thornton Academy","Scarborough","South Portland",
    "Noble","Massabesic","Windham","Oxford Hills","Oxford Hills/Buckfield",
    "Fryeburg Academy","Cony","Lawrence","Messalonskee","Mount Blue","Skowhegan",
    "Lewiston","Portland","Edward Little","Deering","Poland Regional","Dirigo",
    "Freeport","Lisbon","Morse","Mountain Valley","Oak Hill","Greely","York",
    "Wells","Leavitt","Winslow","Madison","Maine Central Institute","Buckfield",
    "Maranacook","Hall-Dale","Monmouth Academy","Cape Elizabeth","Yarmouth",
    "North Yarmouth Academy","Gray-New Gloucester","Lake Region","Waynflete",
    "Cheverus","Cheverus/Waynflete","Boothbay","Traip","Sacopee Valley","Telstar",
    "Spruce Mountain","Mt. Ararat","Camden Hills","Belfast","Brewer","Hermon",
    "Hampden Academy","Gardiner","Nokomis","Oceanside","Oceanside/North Haven",
    "Old Town","Medomak Valley","Foxcroft Academy","Mattanawcook Academy",
    "John Bapst","John Bapst/Bangor Christian","Mount View","Waterville","Orono",
    "Ellsworth","Sumner","Richmond","Piscataquis","Penquis Valley",
    "Lincoln Academy","Mount Abram","Valley","Carrabec","Greenville","Pine Tree Academy",
}

MONTHS = {"9":"Sep","10":"Oct","11":"Nov"}

def parse_date(d):
    m, day, y = d.split(".")
    return f"{MONTHS[m]} {int(day)}, {y}"

def parse_game(line, sport, gender=None):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3:
        return None
    date_raw, matchup, time = parts[0], parts[1], parts[2]
    if " at " not in matchup:
        return None
    away, home = [x.strip() for x in matchup.split(" at ")]
    region = "Western ME" if (away in WESTERN_TEAMS and home in WESTERN_TEAMS) else "Statewide"
    return {
        "sport": sport,
        "gender": gender,
        "date": parse_date(date_raw),
        "dateRaw": date_raw,
        "away": away,
        "home": home,
        "time": time,
        "region": region,
        "source": "downtownme.com" if sport in ("Football","Boys Soccer") else "Fryeburg Academy",
    }

schedule = []
for line in RAW_FOOTBALL.strip().splitlines():
    g = parse_game(line, "Football")
    if g: schedule.append(g)
for line in RAW_BOYS_SOCCER.strip().splitlines():
    g = parse_game(line, "Boys Soccer", "Boys")
    if g: schedule.append(g)

# Fryeburg Academy verified fall 2026 schedule (Fryeburg Academy athletics page)
FA_GAMES = [
    # Football (Class B North)
    ("Sep 4, 2026","Football","Boys","Cony","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 11, 2026","Football","Boys","Fryeburg Academy","Lawrence","Away","Fryeburg Academy"),
    ("Sep 18, 2026","Football","Boys","Fryeburg Academy","Brunswick","Away","Fryeburg Academy"),
    ("Sep 24, 2026","Football","Boys","Camden Hills","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Oct 2, 2026","Football","Boys","Fryeburg Academy","Messalonskee","Away","Fryeburg Academy"),
    # Boys Soccer
    ("Sep 3, 2026","Boys Soccer","Boys","Fryeburg Academy","Wells","Away","Fryeburg Academy"),
    ("Sep 5, 2026","Boys Soccer","Boys","North Yarmouth Academy","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 8, 2026","Boys Soccer","Boys","Fryeburg Academy","Cape Elizabeth","Away","Fryeburg Academy"),
    ("Sep 12, 2026","Boys Soccer","Boys","Lincoln Academy","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 15, 2026","Boys Soccer","Boys","Fryeburg Academy","York","Away","Fryeburg Academy"),
    ("Sep 17, 2026","Boys Soccer","Boys","Yarmouth","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 22, 2026","Boys Soccer","Boys","Cape Elizabeth","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 26, 2026","Boys Soccer","Boys","Greely","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Oct 1, 2026","Boys Soccer","Boys","Freeport","Fryeburg Academy","Away","Fryeburg Academy"),
    # Girls Soccer
    ("Sep 3, 2026","Girls Soccer","Girls","Wells","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 5, 2026","Girls Soccer","Girls","North Yarmouth Academy","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Sep 8, 2026","Girls Soccer","Girls","Cape Elizabeth","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 12, 2026","Girls Soccer","Girls","Lincoln Academy","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 15, 2026","Girls Soccer","Girls","York","Fryeburg Academy","Home","Fryeburg Academy"),
    ("Sep 17, 2026","Girls Soccer","Girls","Yarmouth","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Sep 19, 2026","Girls Soccer","Girls","Waynflete","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Sep 22, 2026","Girls Soccer","Girls","Cape Elizabeth","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Sep 26, 2026","Girls Soccer","Girls","Greely","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Oct 1, 2026","Girls Soccer","Girls","Freeport","Fryeburg Academy","Home","Fryeburg Academy"),
    # Field Hockey
    ("Sep 2, 2026","Field Hockey","Girls","Wells","Fryeburg Academy","Away","Fryeburg Academy"),
    ("Sep 9, 2026","Field Hockey","Girls","Poland Regional","Fryeburg Academy","Home","Fryeburg Academy"),
]

def fa_date_to_raw(ds):
    mo = {"Sep":"9","Oct":"10","Nov":"11"}
    m = ds.split(" ")[0]
    day = ds.split(" ")[1].replace(",","")
    return f"{mo[m]}.{day}.2026"

for (date, sport, gender, away, home, loc, src) in FA_GAMES:
    region = "Western ME"
    schedule.append({
        "sport": sport, "gender": gender, "date": date, "dateRaw": fa_date_to_raw(date),
        "away": away, "home": home, "time": "TBA", "region": region,
        "source": src, "location": loc,
    })

# ---------------------------------------------------------------------------
# CROSS COUNTRY MEETS — verified from MPA SportPageSchedule (official).
# Built by build_xc.py -> js/xc_meets.json. Only meets with >=1 dashboard team;
# every row has verified date, time, location, host, and participating schools.
# ---------------------------------------------------------------------------
try:
    xc = json.load(open("./western-maine-sports/js/xc_meets.json"))
    schedule.extend(xc)
except Exception as e:
    print("WARN: xc_meets.json not loaded:", e)

# ---------------------------------------------------------------------------
# VOLLEYBALL MATCHES — verified from MaxPreps / school schedules.
# Built by build_vb.py -> js/vb_matches.json (date, time, location, home/away,
# opponent, source URL). Only fully-verified rows.
# ---------------------------------------------------------------------------
try:
    vb = json.load(open("./western-maine-sports/js/vb_matches.json"))
    schedule.extend(vb)
except Exception as e:
    pass  # vb_matches.json optional until verified data exists

# Sort schedule by date then time
def sort_key(g):
    m, d, y = g["dateRaw"].split(".")
    t = g["time"]
    # numeric hour for sorting
    th = re.search(r"(\d+)(?::\d+)?\s*(pm|am|PM|AM)?", t)
    hour = 0
    if th:
        hour = int(th.group(1))
        suf = (th.group(2) or "").lower()
        if suf == "pm" and hour != 12: hour += 12
        if suf == "am" and hour == 12: hour = 0
        if not suf and "pm" in t.lower() and hour != 12: hour += 12
    if t.upper() == "TBA": hour = 25
    return (int(y), int(m), int(d), hour)

schedule.sort(key=sort_key)

# ---- Deduplicate: same sport + teams + date may arrive from both
# downtownme.com and a school's own page. Keep the richer row
# (non-TBA time preferred; preserve location if present).
SEEN = {}
deduped = []
for g in schedule:
    if g.get("eventType") == "meet":
        # meets: dedup by date + location + eventName + gender + time + teams.
        # away/home are display-only for meets, and eventName can be empty for
        # venue-named meets, so time + team roster must be in the key to avoid
        # merging distinct meets hosted at the same site on the same day.
        key = ("meet", g["dateRaw"], g.get("location",""), g.get("eventName",""),
               g.get("gender",""), g.get("time",""), tuple(sorted(g.get("coveredTeams",[]))))
    else:
        # games: original dedup key (no gender) — preserves existing FB/soccer/FH data exactly
        key = (g["sport"], g["dateRaw"], frozenset([g["away"], g["home"]]))
    if key in SEEN:
        prev = SEEN[key]
        # prefer non-TBA time
        if g["time"] != "TBA" and prev["time"] == "TBA":
            deduped[deduped.index(prev)] = g; SEEN[key] = g
        # merge location if missing
        elif "location" in g and "location" not in prev:
            prev["location"] = g["location"]
        continue
    SEEN[key] = g
    deduped.append(g)
schedule = sorted(deduped, key=sort_key)

# ---------------------------------------------------------------------------
# TEAMS — key area teams with class assignments
# ---------------------------------------------------------------------------
teams = [
    {"name":"Oxford Hills","mascot":"Vikings","town":"South Paris","football":"Class A North","fieldHockey":"Class A North","boysSoccer":"Class A","girlsSoccer":"Class A","highlight":True},
    {"name":"Fryeburg Academy","mascot":"Raiders","town":"Fryeburg","football":"Class B North","fieldHockey":"Class B South","boysSoccer":"Class B South","girlsSoccer":"Class B South","highlight":True},
    {"name":"Winthrop","mascot":"Ramblers","town":"Winthrop","football":"Class D South (coop)","fieldHockey":"Class C South (coop)","boysSoccer":"Class C","girlsSoccer":"Class C","highlight":True},
    {"name":"Windham","mascot":"Eagles","town":"Windham","football":"Class A North","fieldHockey":"Class A South"},
    {"name":"Bonny Eagle","mascot":"Scots","town":"Standish","football":"Class A South","fieldHockey":"Class A South"},
    {"name":"Thornton Academy","mascot":"Trojans","town":"Saco","football":"Class A South","fieldHockey":"Class A South"},
    {"name":"Scarborough","mascot":"Red Storm","town":"Scarborough","football":"Class A South","fieldHockey":"Class A South"},
    {"name":"Greely","mascot":"Rangers","town":"Cumberland","football":"Class C","fieldHockey":"Class B South"},
    {"name":"Marshwood","mascot":"Hawks","town":"Eliot","football":"Class B South","fieldHockey":"Class A South"},
    {"name":"Leavitt","mascot":"Hornets","town":"Turner","football":"Class C","fieldHockey":"Class B North"},
    {"name":"Cony","mascot":"Rams","town":"Augusta","football":"Class B North","fieldHockey":"Class B North"},
    {"name":"Brunswick","mascot":"Dragons","town":"Brunswick","football":"Class B North","fieldHockey":"Class A North"},
    {"name":"Lawrence","mascot":"Bulldogs","town":"Fairfield","football":"Class B North","fieldHockey":"Class B North"},
    {"name":"Messalonskee","mascot":"Eagles","town":"Oakland","football":"Class B North","fieldHockey":"Class A North"},
    {"name":"Wells","mascot":"Warriors","town":"Wells","football":"Class C","fieldHockey":"Class C South"},
    {"name":"Mountain Valley","mascot":"Falcons","town":"Rumford","football":"Class D South","fieldHockey":"Class C North"},
    {"name":"Dirigo","mascot":"Cougars","town":"Dixfield","football":"Class D South","fieldHockey":"Class C South"},
    {"name":"Poland Regional","mascot":"Knights","town":"Poland","football":"Class D South","fieldHockey":"Class B South"},
    {"name":"Lisbon","mascot":"Greyhounds","town":"Lisbon","football":"Class D South","fieldHockey":"Class C South"},
    {"name":"Mt. Blue","mascot":"Cougars","town":"Farmington","football":"Class B North","fieldHockey":"Class A North"},
    {"name":"Skowhegan","mascot":"River Hawks","town":"Skowhegan","football":"Class B North","fieldHockey":"Class A North"},
]

# ---------------------------------------------------------------------------
# STANDOUT ATHLETES (verified)
# ---------------------------------------------------------------------------
athletes = [
    {"name":"Drew Mertzel","school":"Winthrop","sport":"Golf","gender":"Boys","grade":"Sophomore","note":"Defending Class C individual state champion (75 in 2025); 38.1 nine-hole avg; Varsity Maine All-State; shot 76 at New England championship.","stat":"Defending Class C champ","source":"https://www.sunjournal.com/?p=11288724","featured":True},
    {"name":"Kay Allaire","school":"Winthrop","sport":"Golf","gender":"Girls","grade":"Junior","note":"Runner-up in the Class C girls state championship (90); 47.5 regular-season scoring average.","stat":"Class C girls runner-up","source":"https://www.sunjournal.com/?p=11288724","featured":True},
    {"name":"Finn Coburn","school":"Scarborough","sport":"Boys Soccer","gender":"Boys","grade":"Senior","note":"2025 Varsity Maine Boys Soccer Player of the Year and Gatorade Soccer Player of the Year.","stat":"2025 POY","source":"https://www.centralmaine.com/sports/highschoolsports/"},
    {"name":"Noelle Mallory","school":"Cape Elizabeth","sport":"Girls Soccer","gender":"Girls","grade":"Senior","note":"Gatorade Girls Soccer Player of the Year; led Cape Elizabeth to a perfect state-championship season.","stat":"Gatorade POY","source":"https://www.centralmaine.com/sports/highschoolsports/"},
    {"name":"Phoebe Bell","school":"Maranacook","sport":"Girls Soccer","gender":"Girls","grade":"Senior","note":"MVC and Class C Player of the Year; 20 goals, 8 assists; led Maranacook to state title.","stat":"Class C POY","source":"https://www.centralmaine.com/2026/01/01/meet-the-2025-varsity-maine-all-state-girls-soccer-team/"},
    {"name":"Reese Beaudoin","school":"Sanford/Kennebunk","sport":"Field Hockey","gender":"Girls","grade":"Sophomore","note":"21 goals, 13 assists as a freshman; first-team all-SMAA.","stat":"21 G / 13 A","source":"https://www.pressherald.com/?p=7714652"},
    {"name":"Sydney Brunelle","school":"Cheverus","sport":"Field Hockey","gender":"Girls","grade":"Senior","note":"Returning Varsity Maine All-State midfielder; centerpiece of a Class A South contender.","stat":"All-State","source":"https://www.pressherald.com/2026/09/01/meet-10-southern-maine-field-hockey-teams-to-watch-in-2026/"},
    {"name":"Aisla Armandi","school":"Spruce Mountain","sport":"Field Hockey","gender":"Girls","grade":"Senior","note":"First-team MVC pick; quick left wing and offensive catalyst for the Phoenix.","stat":"First-team MVC","source":"https://www.sunjournal.com/?p=11289792"},
    {"name":"Ainsley Barry","school":"Leavitt","sport":"Field Hockey","gender":"Girls","grade":"Senior","note":"One of the Hornets' go-to players; key returner for a Class B North contender.","stat":"Key returner","source":"https://www.sunjournal.com/?p=11289792"},
    {"name":"Helen Dineen","school":"Cony","sport":"Field Hockey","gender":"Girls","grade":"Senior","note":"KVAC B first-team and Maine FH Association All-State pick; top returner for Cony.","stat":"All-State","source":"https://www.centralmaine.com/?p=3416413"},
    {"name":"Wyatt Banow","school":"Oceanside","sport":"Football","gender":"Boys","grade":"Junior","note":"Workhorse RB; rushed for 800+ yards in 2025 despite an 0-8 Mariners season.","stat":"800+ rush yds","source":"https://www.pressherald.com/?p=7715278"},
    {"name":"Braden Beveridge","school":"Camden Hills","sport":"Football","gender":"Boys","grade":"Senior","note":"Key contributor to the 8-Man Large School championship team; 577 rushing yards, 6 TDs.","stat":"577 rush yds","source":"https://www.pressherald.com/?p=7715278"},
]

# ---------------------------------------------------------------------------
# CLASS REALIGNMENTS — MPA football (2025 & 2026 cycle) + field hockey
# ---------------------------------------------------------------------------
realignments = {
    "football": {
        "season": "2025 & 2026 (MPA Football Committee, approved Jan 2025)",
        "cutoffs": "Class A 850+ · Class B 635-849 · Class C 400-634 (statewide) · Class D 0-399",
        "changes": [
            "Class A grew from 12 to 14 teams — Deering and Massabesic moved up from Class B.",
            "Class C and Class D moved to statewide playoff brackets (no North/South split).",
            "Class A and Class B state championships remain North region champ vs. South region champ.",
        ],
        "classes": [
            {"class":"Class A","region":"North","teams":"Bangor, Deering, Edward Little, Lewiston, Oxford Hills, Portland, Windham"},
            {"class":"Class A","region":"South","teams":"Bonny Eagle, Massabesic, Noble, Sanford, Scarborough, South Portland, Thornton Academy"},
            {"class":"Class B","region":"North","teams":"Brunswick, Cony, Fryeburg Academy, Lawrence, Messalonskee, Mt. Blue, Skowhegan"},
            {"class":"Class B","region":"South","teams":"Biddeford, Cheverus, Gorham, Falmouth, Kennebunk, Marshwood, Westbrook"},
            {"class":"Class C","region":"Statewide","teams":"Brewer, Foxcroft Academy, Gardiner, Greely, Hampden Academy, Hermon, Leavitt, Medomak Valley, Nokomis, Oceanside, Old Town, Wells, York"},
            {"class":"Class D","region":"North","teams":"Belfast, John Bapst, Madison, Maine Central Institute, Maranacook, Mattanawcook Academy, Winslow"},
            {"class":"Class D","region":"South","teams":"Dirigo, Freeport, Lisbon, Morse, Mountain Valley, Oak Hill, Poland, Winthrop/Monmouth/Hall-Dale"},
        ],
    },
    "fieldHockey": {
        "season": "2025-26 (MPA Field Hockey Bulletin, approved Jan 2025)",
        "cutoffs": "Class A 665+ · Class B 435-664 · Class C 0-434",
        "changes": [
            "Three-class structure (A/B/C) by enrollment, split North and South within each class.",
            "Class A South is the largest division (15 schools); Cheverus petitioned in.",
        ],
        "classes": [
            {"class":"Class A","region":"North","teams":"Lewiston, Edward Little, Bangor, Oxford Hills, Hampden, Mt. Ararat, Camden Hills, Brunswick, Messalonskee, Skowhegan, Mt. Blue, Brewer"},
            {"class":"Class A","region":"South","teams":"Thornton, Portland/Deering, Sanford, Bonny Eagle, So. Portland/Westbrook, Noble, Windham, Scarborough, Massabesic, Gorham, Kennebunk, Falmouth, Biddeford, Marshwood, Cheverus"},
            {"class":"Class B","region":"North","teams":"Nokomis, Cony, Gardiner, Hermon, Leavitt, Old Town, Erskine, Lawrence, John Bapst, Oceanside, Belfast"},
            {"class":"Class B","region":"South","teams":"Fryeburg, Freeport, Morse, Greely, GNG/NYA, Yarmouth, Lincoln, Cape Elizabeth, York, Lake Region, Poland"},
            {"class":"Class C","region":"North","teams":"Foxcroft, Mountain Valley, Winslow, Orono, Central, Mattanawcook, Mt. View, Dexter, MCI, Dirigo, Piscataquis, Stearns/Schenck"},
            {"class":"Class C","region":"South","teams":"Spruce Mountain, Wells, Oak Hill, Lisbon, Traip, Sacopee Valley, Waynflete, Hall-Dale, Winthrop/Maranacook, Telstar, Boothbay"},
        ],
    },
    "soccer": {
        "season": "2025-26 (MPA Soccer Bulletin)",
        "cutoffs": "Class A, B, C, D by enrollment + 8-player class",
        "changes": [
            "Boys and girls soccer each run Class A, B, C, D plus an 8-player division.",
            "Regional tournaments in late October; state championships early November.",
        ],
        "classes": [
            {"class":"Tournament sites","region":"Class A North","teams":"Cameron Stadium, Bangor (girls 4:30 / boys 6:00)"},
            {"class":"Tournament sites","region":"Class A South","teams":"Falmouth High School"},
            {"class":"Tournament sites","region":"Class C North","teams":"Hampden Academy"},
        ],
    },
    "crossCountry": {
        "season": "2025-26 (MPA)",
        "cutoffs": "Class A 700+ · Class B 400-699 · Class C 0-399",
        "changes": [
            "State championship meet Nov 1, 2025; New Englands Nov 8.",
            "No North/South split — classes compete as single statewide fields.",
        ],
        "classes": [
            {"class":"Class A","region":"Statewide","teams":"Enrollment 700+ (e.g., Lewiston, Portland, Bangor, Oxford Hills, Windham, Bonny Eagle, Thornton Academy)"},
            {"class":"Class B","region":"Statewide","teams":"Enrollment 400-699 (e.g., Fryeburg Academy, Greely, Cony, Messalonskee, Brunswick, Leavitt)"},
            {"class":"Class C","region":"Statewide","teams":"Enrollment 0-399 (e.g., Winthrop, Dirigo, Lisbon, Mountain Valley, Orono)"},
        ],
    },
    "volleyball": {
        "season": "2025-26 (MPA Volleyball Bulletin)",
        "cutoffs": "Class B/A (combined), Class C, Class D",
        "changes": [
            "Girls volleyball runs Class B/A, Class C, and Class D state championships Nov 1.",
            "State semis Oct 29; Class D, C, and B/A state finals all Nov 1.",
        ],
        "classes": [
            {"class":"Class B/A","region":"State","teams":"Combined Class A & B schools; state final at USM, 3:00 (B) / 5:30 (A)"},
            {"class":"Class C","region":"State","teams":"State final at Hampden Academy, 1:00"},
            {"class":"Class D","region":"State","teams":"State final at Brewer High School, 12:00"},
        ],
    },
}

# ---------------------------------------------------------------------------
# STANDINGS / PLAYOFF TRACKER — preseason baseline (to be updated weekly)
# Football: Heal Point standings not yet published for 2026 (season starts Sep 3).
# Values below are preseason outlook labels, not computed standings.
# ---------------------------------------------------------------------------
standings = {
    "lastUpdated": "2026-09-03 (preseason baseline — Week 0)",
    "football": [
        {"team":"Oxford Hills","class":"A North","record":"0-0","heal":"—","status":"Preseason — Class A North contender (2025 finished 5-4, reached Class A North semifinal)","key":"at Windham 9/4; vs Edward Little 9/18; at Lewiston 10/2"},
        {"team":"Fryeburg Academy","class":"B North","record":"0-0","heal":"—","status":"Preseason — Class B North (2025 finished 6-2, top of Class C computer rankings)","key":"vs Cony 9/4; at Brunswick 9/18; at Messalonskee 10/2"},
        {"team":"Winthrop","class":"D South","record":"0-0","heal":"—","status":"Preseason — Class D South co-op (Winthrop/Monmouth/Hall-Dale)","key":"vs Lisbon 9/4; vs Madison 9/17; vs Poland Regional 9/24"},
        {"team":"Thornton Academy","class":"A South","record":"0-0","heal":"—","status":"Preseason — Class A South favorite (MaxPreps #1 in Maine)","key":"vs Scarborough 9/4"},
        {"team":"Bonny Eagle","class":"A South","record":"0-0","heal":"—","status":"Preseason — Class A South (MaxPreps #2 in Maine)","key":"vs South Portland 9/4"},
        {"team":"Leavitt","class":"C","record":"0-0","heal":"—","status":"Preseason — Class C statewide (MaxPreps #3 in Maine)","key":"vs Medomak Valley 9/4"},
    ],
    "note": "Heal Point standings are computed by the MPA after the season begins and are not yet published for fall 2026. Status labels reflect preseason outlook only and will be replaced with computed standings once MPA releases weekly Heal Point reports. Verify at mpa.cc before citing.",
}

# ---------------------------------------------------------------------------
# WEEKLY UPDATE LOG
# ---------------------------------------------------------------------------
updateLog = [
    {"week":"Week 0","date":"Sep 3, 2026","summary":"Season opens. Preseason baseline loaded. Football first countable games Sep 3-5. Soccer, field hockey, volleyball, cross country also begin this week. Standings = preseason outlook only."},
]

# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------
sources = [
    {"name":"MPA — Maine Principals' Association", "url":"https://www.mpa.cc/", "use":"Classifications, season dates, tournament structure, Heal Point standings"},
    {"name":"MPA Football Bulletin 2025-26 (PDF)", "url":"https://mpa.fpsports.org/resources/Tournament%20Info/Football/Bulletin%202025-26.pdf", "use":"Football classifications & enrollment cutoffs"},
    {"name":"MPA Field Hockey Bulletin 2025-26 (PDF)", "url":"https://www.mpa.cc/resources/Tournament%20Info/Field%20Hockey/Bulletin%202025-26.pdf", "use":"Field hockey classifications by class/region"},
    {"name":"MPA Sport Season Dates 2025-2026 (PDF)", "url":"https://www.mpa.cc/resources/Resources/Sport%20Season%20Dates%202025-2026.pdf", "use":"First practice / first countable game / closing dates"},
    {"name":"Downtown ME High School Sports (2026-2027 schedules)", "url":"https://www.downtownme.com/sports/sports.asp", "use":"Football & boys soccer game schedules Sep-Oct 2026"},
    {"name":"Fryeburg Academy Athletics — Schedules", "url":"https://www.fryeburgacademy.org/athletics/schedules", "use":"Fryeburg Academy fall 2026 football, soccer, field hockey schedules"},
    {"name":"High School Football America — Maine realignment", "url":"https://highschoolfootballamerica.com/maine-high-school-football-realignment-approved-for-next-two-seasons/", "use":"2025 & 2026 football realignment summary by class/region"},
    {"name":"Sun Journal — Western Maine golfers to watch 2026", "url":"https://www.sunjournal.com/?p=11288724", "use":"Kay Allaire & Drew Mertzel profiles"},
    {"name":"Sun Journal — Western Maine field hockey players to watch 2026", "url":"https://www.sunjournal.com/?p=11289792", "use":"Field hockey athlete profiles"},
    {"name":"Central Maine — field hockey players to watch 2026", "url":"https://www.centralmaine.com/?p=3416413", "use":"Field hockey athlete profiles"},
    {"name":"Portland Press Herald — 30 southern Maine football players to watch 2026", "url":"https://www.pressherald.com/?p=7715278", "use":"Football athlete profiles"},
    {"name":"Portland Press Herald — 25 southern Maine field hockey players to watch", "url":"https://www.pressherald.com/?p=7714652", "use":"Field hockey athlete profiles"},
    {"name":"Central Maine — 2025 Varsity Maine All-State girls soccer", "url":"https://www.centralmaine.com/2026/01/01/meet-the-2025-varsity-maine-all-state-girls-soccer-team/", "use":"Soccer athlete honors"},
    {"name":"MaxPreps — Maine Football 2026 rankings", "url":"https://www.maxpreps.com/me/football/rankings/1/", "use":"Preseason football rankings"},
    {"name":"Central Maine — 2026 football schedule takeaways", "url":"https://www.centralmaine.com/2026/03/30/the-2026-maine-high-school-football-schedule-is-out-here-are-5-takeaways/", "use":"Schedule notes (Oxford Hills Week 4 bye)"},
    {"name":"MPA Cross Country — Boys schedule (SportPageSchedule)", "url":"https://www.mpa.cc/SportPages/SportPageSchedule.aspx?TournamentID=1", "use":"2026 boys cross country meet dates, times, venues, team rosters"},
    {"name":"MPA Cross Country — Girls schedule (SportPageSchedule)", "url":"https://www.mpa.cc/SportPages/SportPageSchedule.aspx?TournamentID=9", "use":"2026 girls cross country meet dates, times, venues, team rosters"},
]

meta = {
    "title": "Western Maine 2026 Fall Sports Dashboard",
    "season": "Fall 2026",
    "generated": "2026-09-03",
    "seasonDates": {
        "firstPractice": "Aug 17, 2026",
        "firstCountableGame": "Sep 3, 2026",
        "regularSeasonClose": "Oct 18-25, 2026 (sport-dependent)",
        "stateChampionships": "Late Oct – Nov 8, 2026",
    },
    "coverage": "Football, Boys & Girls Soccer, Field Hockey, Cross Country, Volleyball (+ standout golfers)",
}

data = {
    "meta": meta,
    "schedule": schedule,
    "teams": teams,
    "athletes": athletes,
    "realignments": realignments,
    "standings": standings,
    "updateLog": updateLog,
    "sources": sources,
}

js = "/* Western Maine 2026 Fall Sports — data module\n   Generated from verified MPA / school / local-news sources. See sources list. */\n"
js += "window.WM_DATA = " + json.dumps(data, indent=2) + ";\n"

import os
os.makedirs("./western-maine-sports/js", exist_ok=True)
with open("./western-maine-sports/js/data.js","w") as f:
    f.write(js)
print(f"Wrote js/data.js — {len(schedule)} games, {len(athletes)} athletes, {len(sources)} sources")
