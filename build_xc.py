#!/usr/bin/env python3
"""Normalize + filter MPA cross country meets to those with >=1 dashboard team.
Outputs js/xc_meets.json. Verified source: MPA SportPageSchedule (official)."""
import json, re, os

# ---- Dashboard coverage set (81 teams) — built from js/data.js so multi-word
# names like "Mountain Valley" and "Foxcroft Academy" stay intact. ----
import json as _json
_raw=open('./western-maine-sports/js/data.js').read()
_d=_json.loads(_raw.split('window.WM_DATA = ',1)[1].rsplit(';',1)[0])
COV=set()
for _g in _d['schedule']:
    for _side in ('away','home'):
        for _part in _g[_side].split('/'):
            COV.add(_part.strip())
for _a in _d.get('athletes',[]): COV.add(_a['school'])
for _row in _d.get('standings',{}).get('football',[]): COV.add(_row.get('team',''))
COV={c for c in COV if c and c.lower()!='tba'}

# Aliases: XC page name -> canonical dashboard name. Handles "X HS", "X Academy",
# "X Area", "X Regional", "X Community", "X Memorial", and co-ops.
ALIASES = {
    "Belfast Area":"Belfast","Belfast Troy Howard Middle Sch":"Belfast",
    "Camden Hills Regional":"Camden Hills","Cony HS":"Cony","Gardiner Area":"Gardiner",
    "Hall-Dale HS":"Hall-Dale","John Bapst Memorial":"John Bapst","Leavitt Area":"Leavitt",
    "Madison High School":"Madison","Maranacook Community":"Maranacook",
    "Mattanawcook Academy/Lee/Penob":"Mattanawcook Academy","Skowhegan Area":"Skowhegan",
    "Sumner Memorial":"Sumner","Richmond HS":"Richmond","Mt. Blue":"Mount Blue",
    "Dirigo/Mountain Valley Coop":"Dirigo; Mountain Valley",
    "Foxcroft":"Foxcroft Academy","Hampden":"Hampden Academy","Lincoln":"Lincoln Academy",
    "Thornton":"Thornton Academy","Mattanawcook":"Mattanawcook Academy",
}
_SUFFIXES=(" HS"," Academy"," Area"," Regional"," Community"," Memorial")

def norm_team(raw):
    """Return list of canonical dashboard team names from a raw XC team string."""
    name = raw.split(" - ")[0].strip()
    name = ALIASES.get(name, name)
    out=[]
    for part in re.split(r"[/;]", name):
        p=part.strip()
        if not p: continue
        out.append(p)
        for suf in _SUFFIXES:
            if p.endswith(suf): out.append(p[:-len(suf)].strip())
    matches=[]
    for x in out:
        if x in COV and x not in matches:
            matches.append(x)
    return matches

WESTERN={"Gorham","Westbrook","Marshwood","Sanford","Brunswick","Biddeford","Falmouth",
"Kennebunk","Bonny Eagle","Thornton Academy","Scarborough","South Portland","Noble",
"Massabesic","Windham","Oxford Hills","Fryeburg Academy","Cony","Lawrence","Messalonskee",
"Mount Blue","Skowhegan","Lewiston","Portland","Edward Little","Deering","Poland Regional",
"Dirigo","Freeport","Lisbon","Morse","Mountain Valley","Oak Hill","Greely","York","Wells",
"Leavitt","Winslow","Madison","Maine Central Institute","Buckfield","Maranacook","Hall-Dale",
"Monmouth Academy","Cape Elizabeth","Yarmouth","Mt. Ararat","Lake Region","Brewer","Gardiner",
"Waterville","Lincoln Academy","Mt. Abram","Spruce Mountain","Camden Hills","Hampden Academy",
"Hermon","John Bapst","Orono","Old Town","Oceanside","Medomak Valley","Mount View",
"Mattanawcook Academy","Bangor","Belfast","Ellsworth","North Yarmouth Academy",
"Waynflete","Foxcroft Academy","Sumner","Richmond","Salem"}
def host_region(host):
    return "Western ME" if host in WESTERN else "Statewide"

def parse_iso_date(s):
    # s like 2026-09-04
    y,mo,d = s.split("-")
    months={"09":"Sep","10":"Oct","11":"Nov","08":"Aug"}
    return f"{months.get(mo,mo)} {int(d)}, {y}", f"{int(mo)}.{int(d)}.{y}"

SRC_BOYS="https://www.mpa.cc/SportPages/SportPageSchedule.aspx?TournamentID=1"
SRC_GIRLS="https://www.mpa.cc/SportPages/SportPageSchedule.aspx?TournamentID=9"

# ---- Upcoming meets from JSON ----
rows = []
for path, gender, src in [
    ("./data/boys_final.json","Boys",SRC_BOYS),
    ("./data/girls_final.json","Girls",SRC_GIRLS)]:
    for m in json.load(open(path)):
        teams = m.get("teams",[]) or []
        covered = []
        for t in teams:
            covered += norm_team(t)
        # dedupe covered
        cov=[]
        for c in covered:
            if c not in cov: cov.append(c)
        if not cov:
            continue  # no dashboard team -> skip
        host = m.get("host") or ""
        host_clean = (host.split(" - ")[0].strip() if host else "")
        venue = m.get("venue","") or ""
        title = m.get("meet_title") or ""
        date_disp, date_raw = parse_iso_date(m["iso_date"])
        participants_all = []
        for t in teams:
            n=t.split(" - ")[0].strip()
            if n and n not in participants_all:
                participants_all.append(n)
        away = title if title else "Cross Country Meet"
        home = host_clean if host_clean else venue
        rows.append({
            "sport":"Cross Country","gender":gender,"eventType":"meet",
            "eventName":title,"date":date_disp,"dateRaw":date_raw,
            "time":m.get("time_str") or "TBA","away":away,"home":home,
            "location":venue,"host":host_clean,
            "participants":participants_all,"coveredTeams":cov,
            "region":host_region(host_clean),
            "meetInfo":f"XC · {len(cov)} team{'s' if len(cov)!=1 else ''}",
            "source":"MPA","sourceUrl":src,
        })

# ---- 9/3 current-week meets (verified from MPA today's-meets page) ----
TODAY="9.3.2026"; DATE_DISP="Sep 3, 2026"
nine_three = [
 # Boys
 ("Boys","Maranacook Invitational","Maranacook Community High School, Readfield, ME","Maranacook",
   ["Maranacook","Hall-Dale","Lisbon","Spruce Mountain","Winthrop"]),
 ("Boys","Ellsworth Invitational","Ellsworth HS, Ellsworth, ME","Ellsworth",
   ["Ellsworth","Foxcroft Academy"]),
 ("Boys","Kennebunk Multi-Team Meet","Kennebunk Elementary School, Kennebunk, ME","Kennebunk",
   ["Kennebunk","Cheverus","Gorham","Massabesic","South Portland"]),
 ("Boys","Edward Little Home Meet","Edward Little HS / Auburn MS, Auburn, ME","Edward Little",
   ["Edward Little","Lewiston","Mt. Ararat","Nokomis","Oxford Hills","Winslow"]),
 ("Boys","Marshwood Home Meet","Marshwood (Great Works School), South Berwick, ME","Marshwood",
   ["Marshwood","Falmouth","Thornton Academy","Westbrook"]),
 # Girls
 ("Girls","Kennebunk Multi-Team Meet","Kennebunk Elementary School, Kennebunk, ME","Kennebunk",
   ["Kennebunk","Cheverus","Gorham","Massabesic","South Portland"]),
 ("Girls","Edward Little Home Meet","Edward Little HS / Auburn MS, Auburn, ME","Edward Little",
   ["Edward Little","Lewiston","Mt. Ararat","Nokomis","Oxford Hills","Winslow"]),
 ("Girls","Maranacook Invitational","Maranacook Community High School, Readfield, ME","Maranacook",
   ["Maranacook","Hall-Dale","Lisbon","Spruce Mountain","Winthrop"]),
 ("Girls","Ellsworth Invitational","Ellsworth HS, Ellsworth, ME","Ellsworth",
   ["Ellsworth","Foxcroft Academy"]),
 ("Girls","Marshwood Home Meet","Marshwood (Great Works School), South Berwick, ME","Marshwood",
   ["Marshwood","Falmouth","Thornton Academy","Westbrook"]),
]
for gender,title,venue,host,cov in nine_three:
    rows.append({
        "sport":"Cross Country","gender":gender,"eventType":"meet","eventName":title,
        "date":DATE_DISP,"dateRaw":TODAY,"time":"4:00 PM","away":title,"home":host,
        "location":venue,"host":host,"participants":cov,"coveredTeams":cov,
        "region":host_region(host),"meetInfo":f"XC · {len(cov)} teams","source":"MPA","sourceUrl":SRC_BOYS if gender=="Boys" else SRC_GIRLS,
    })

# sort by date then time
def sk(r):
    mo,d,y=r["dateRaw"].split(".")
    t=r["time"]; th=re.search(r"(\d+)(?::\d+)?\s*(pm|am|PM|AM)?",t); h=int(th.group(1)) if th else 25
    if th:
        suf=(th.group(2) or "").lower()
        if suf=="pm" and h!=12: h+=12
        if suf=="am" and h==12: h=0
    if t.upper()=="TBA": h=25
    return (int(y),int(mo),int(d),h)
rows.sort(key=sk)

os.makedirs("./western-maine-sports/js",exist_ok=True)
with open("./western-maine-sports/js/xc_meets.json","w") as f:
    json.dump(rows,f,indent=2)
print(f"Wrote js/xc_meets.json — {len(rows)} XC meets")
# stats
print("Boys:",sum(1 for r in rows if r['gender']=='Boys'),"Girls:",sum(1 for r in rows if r['gender']=='Girls'))
print("Distinct covered teams appearing:",len(set(c for r in rows for c in r['coveredTeams'])))
