#!/usr/bin/env python3
"""Refresh source-linked local scores. Never infer official rankings or missing scores."""
import argparse, concurrent.futures, datetime as dt, html, json, re, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
from sports_data import COVERAGE, canonical_team, covered_teams, game_key
ROOT=Path(__file__).resolve().parent
SCHOOLS={'Buckfield':11,'Dirigo':26,'Fryeburg Academy':39,'Mountain Valley':90,'Oxford Hills':100,'Oxford Hills/Buckfield':227,'Poland Regional':104,'Sacopee Valley':111,'Telstar':123}
SPORTS={'Football':'Football','Soccer - Boys':'Boys Soccer','Soccer - Girls':'Girls Soccer','Field Hockey':'Field Hockey'}
def plain(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def source_url(i): return f'https://www.downtownme.com/sports/sports.asp?strFunction=GetScheduleBySchool&intSchool={i}'
def parse_page(body, school, url, today):
    sport=None; rows=[]
    if '2026-2027 Schedules' not in plain(body): raise ValueError('Wrong season or missing schedule')
    for attrs,content in re.findall(r'<tr\b([^>]*)>(.*?)</tr>',body,re.S|re.I):
        if 'sport-title' in attrs:
            sport=SPORTS.get(plain(content));continue
        if not sport or 'line-single' not in attrs: continue
        t=plain(content); m=re.match(r'(.*?)\s*(\d{1,2})\.(\d{1,2})\.(2026)\s*[–—-]\s*(.*)',t)
        if not m: continue
        time,month,day,year,game=m.groups(); date=dt.date(int(year),int(month),int(day))
        if date.month<9: continue # exhibition dates precede the regular season
        result=re.fullmatch(r'(.+?) (\d+), (.+?) (\d+)(?:,? (?:tie|OT|2OT))?',game,re.I)
        scheduled=re.fullmatch(r'(.+?) at (.+)',game)
        if result:
            left,ls,right,rs=result.groups(); ls=int(ls);rs=int(rs)
            row={'away':canonical_team(left),'home':canonical_team(right),'awayScore':ls,'homeScore':rs,'completed':True,'venueKnown':False}
            if date>today: raise ValueError('Future result')
        elif scheduled:
            left,right=scheduled.groups();row={'away':canonical_team(left),'home':canonical_team(right),'completed':False,'venueKnown':True}
        else: continue
        row.update(sport=sport,gender='Girls' if sport in ('Girls Soccer','Field Hockey') else 'Boys',date=date.strftime('%b %-d, %Y'),dateRaw=f'{date.month}.{date.day}.{date.year}',dateISO=date.isoformat(),time=time or 'TBA',eventType='game',region='Western ME',source='downtownme.com',sourceUrl=url,sourceUrls=[url],checked=today.isoformat(),verification='pending')
        row['coveredTeams']=covered_teams(row)
        if not row['coveredTeams']: continue
        rows.append(row)
    if not rows and school!='Oxford Hills/Buckfield': raise ValueError('Empty schedule')
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cached',action='store_true');args=ap.parse_args()
    today=dt.datetime.now(ZoneInfo('America/New_York')).date();cache=ROOT/'source_cache';cache.mkdir(exist_ok=True)
    def read(item):
        school,i=item;path=cache/(school.lower().replace('/','-').replace(' ','-')+'.html');url=source_url(i)
        if args.cached:body=path.read_text(encoding="cp1252")
        else:
            body=urllib.request.urlopen(url,timeout=30).read().decode('cp1252');path.write_bytes(body.encode("cp1252"))
        return parse_page(body,school,url,today)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: batches=list(pool.map(read,SCHOOLS.items()))
    groups={}
    for row in sum(batches,[]):
        # Result lists put the winner first; they do not specify venue.
        k=game_key(row)
        if k not in groups: groups[k]=[]
        groups[k].append(row)
    rows=[];conflicts=[]
    for key,items in groups.items():
        finals=[x for x in items if x['completed']]; chosen=(finals or items)[0].copy()
        scores={tuple(sorted([(x['away'],x['awayScore']),(x['home'],x['homeScore'])])) for x in finals}
        if len(scores)>1:
            chosen['scoreReports']=[{'away':x['away'],'awayScore':x['awayScore'],'home':x['home'],'homeScore':x['homeScore'],'sourceUrl':x['sourceUrl']} for x in finals]
            chosen['completed']=False;chosen['verification']='disputed';chosen.pop('awayScore',None);chosen.pop('homeScore',None);chosen['reviewNote']='Conflicting reported scores; result withheld.';conflicts.append({'key':key,'reason':chosen['reviewNote']})
        clocks={x['time'] for x in items if x['time']!='TBA'}
        if not finals and len(clocks)>1:
            chosen['time']='Confirm time';chosen['reviewNote']='Sources list different start times.';conflicts.append({'key':key,'reason':chosen['reviewNote']})
        elif clocks: chosen['time']=sorted(clocks)[0]
        chosen['coveredTeams']=sorted({t for x in items for t in x['coveredTeams']});chosen['sourceUrls']=sorted({x['sourceUrl'] for x in items})
        rows.append(chosen)
    # A stale scheduled duplicate on another nearby date must not become an upcoming game.
    for row in rows:
        if row['completed']:continue
        for other in rows:
            if other['completed'] and other['sport']==row['sport'] and {other['away'],other['home']}=={row['away'],row['home']} and abs((dt.date.fromisoformat(other['dateISO'])-dt.date.fromisoformat(row['dateISO'])).days)<=3:
                row['reviewNote']='Possible rescheduled duplicate; confirm with school.'
                break
    rows.sort(key=lambda x:(x['dateISO'],x['sport'],x['away'],x['home']))
    payload={'checked':today.isoformat(),'publicationStatus':'Unreviewed candidates — not for publication','schedule':rows,'conflicts':conflicts,'coverage':list(COVERAGE)}
    (ROOT/'schedule_candidates.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'records':len(rows),'results':sum(x['completed'] for x in rows),'conflicts':conflicts},indent=2))
if __name__=='__main__':main()

