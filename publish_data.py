#!/usr/bin/env python3
"""Build the dashboard from reviewed source rows; rankings remain unverified until MPA is read."""
import json
from pathlib import Path
from refresh_data import SCHOOLS,source_url
R=Path(__file__).resolve().parent
b=json.loads((R/'reference-september.json').read_text());p=json.loads((R/'verified_schedule.json').read_text());today=p['checked'];rows=p['schedule']
if today!='2026-10-10': raise SystemExit('This reviewed supplemental snapshot is dated October 10. Reverify supplements before building a newer edition.')
def add(sport,day,a,h,score=None,time='TBA',url='',source='Gould Academy',note=''):
 import datetime as dt
 d=dt.date(2026,10,day);row=dict(sport=sport,gender='Girls' if sport=='Girls Soccer' else 'Boys',date=d.strftime('%b %-d, %Y'),dateRaw=f'10.{day}.2026',dateISO=d.isoformat(),away=a,home=h,time=time,completed=score is not None,venueKnown=score is None,eventType='game',coveredTeams=[t for t in p['coverage'] if t in (a,h) or (sport=='Football' and t in ('Oxford Hills','Buckfield') and 'Oxford Hills/Buckfield' in (a,h))],region='Western ME',source=source,sourceUrl=url,sourceUrls=[url],checked=today)
 if score:row.update(awayScore=score[0],homeScore=score[1])
 if note:row['reviewNote']=note
 k=lambda x:(x['sport'],x['dateISO'],frozenset((x['away'],x['home'])))
 for old in list(rows):
  if k(old)==k(row):rows.remove(old)
 rows.append(row)
vm='https://www.varsitymaine.com/daily-scores-and-schedules-combined'
for a,h,s in [('Bonny Eagle','Oxford Hills/Buckfield',(45,6)),('Kennebunk','Fryeburg Academy',(35,34)),('Winthrop','Dirigo',(19,6)),('Telstar','Sacopee Valley',(70,24))]:add('Football',9,a,h,s,url=vm,source='Varsity Maine')
# The official Gould page leaves some past scores blank; retain that uncertainty.
gb='https://www.gouldacademy.org/athleticsfsel-3707/boys-varsity-soccer'
add('Boys Soccer',7,'Gould Academy','Hyde School',(1,8),url='https://www.hyde.edu/athletics/our-teams/boys-varsity-soccer',source='Hyde School')
add('Boys Soccer',10,'Gould Academy','Hebron Academy',time='2 pm',url=gb)
add('Boys Soccer',14,'Gould Academy','Kents Hill',time='3 pm',url=gb)
add('Boys Soccer',17,'Hebron Academy','Gould Academy',time='3 pm',url=gb)
add('Girls Soccer',31,'Hyde School','Gould Academy',time='noon',url='https://www.hyde.edu/athletics/our-teams/girls-varsity-soccer',source='Hyde School')
# Independent football schedule listings supplement missing local listings.
import re, datetime as dt
from refresh_data import plain
slugs={'telstar':'Telstar','sacopee-valley':'Sacopee Valley','mountain-valley':'Mountain Valley','oxford-hills':'Oxford Hills/Buckfield','fryeburg-academy':'Fryeburg Academy','poland':'Poland Regional','dirigo':'Dirigo'}
alias={'OOB':'Old Orchard Beach','Traip':'Traip Academy','Fryeburg':'Fryeburg Academy','Poland':'Poland Regional','MCI':'Maine Central Institute','Mt. Blue':'Mount Blue','MDI':'Mount Desert Island','Oxford Hills':'Oxford Hills/Buckfield','John Bapst':'John Bapst/Bangor Christian/Ce'}
for slug,team in slugs.items():
 body=(R/'source_cache'/('football-'+slug+'.html')).read_text()
 for attrs,content in re.findall(r'<div class="(iq-grow [^"]*)">(.*?)</div>',body,re.S):
  date_match=re.search(r'/game/(2026-\d{2}-\d{2})-',content)
  matchup=re.search(r'<a class="iq-card__link"[^>]*>(.*?)</a>',content)
  final=re.search(r'<span class="iq-grow-r">(.*?)</span>\s*<span class="iq-card__go"',content,re.S)
  if not (date_match and matchup and final):continue
  d=dt.date.fromisoformat(date_match[1]);text=plain(matchup[1]);opponent=re.sub(r'^(?:vs\. |at )','',text);opponent=alias.get(opponent,opponent)
  a,h=(team,opponent) if text.startswith('at ') else (opponent,team)
  score=re.fullmatch(r'[WL] (\d+)–(\d+)',plain(final[1]))
  row=dict(sport='Football',gender='Boys',date=d.strftime('%b %-d, %Y'),dateISO=d.isoformat(),dateRaw=f'{d.month}.{d.day}.2026',away=a,home=h,time='TBA' if score else plain(final[1]),completed=bool(score),venueKnown=True,eventType='game',coveredTeams=[t for t in p['coverage'] if t in (a,h) or (t in ('Oxford Hills','Buckfield') and 'Oxford Hills/Buckfield' in (a,h))],region='Western ME',source='niftiIQ (independent)',sourceUrl=f'https://niftiiq.com/maine/football/{slug}/',checked=today)
  row['sourceUrls']=[row['sourceUrl']]
  if score:
   own,opp=map(int,score.groups());row.update(awayScore=own if a==team else opp,homeScore=own if h==team else opp)
  same=[x for x in rows if x['sport']=='Football' and x['dateISO']==row['dateISO'] and {x['away'],x['home']}=={a,h}]
  if same:
   old=same[0]
   if score and not old['completed']:rows.remove(old);rows.append(row)
   elif score and old['completed']:
    old_scores={old['away']:old['awayScore'],old['home']:old['homeScore']}
    if old_scores!={a:row['awayScore'],h:row['homeScore']}:
     old.update(completed=False,reviewNote='Conflicting reported scores; result withheld.');old.pop('awayScore',None);old.pop('homeScore',None)
  else:rows.append(row)

rows.sort(key=lambda x:(x['dateISO'],x['sport'],x['away'],x['home']))
meta=dict(b['meta'],generated=today,checked=today,coverage='Mountain Valley · Dirigo · Telstar · Buckfield · Oxford Hills · Gould Academy · Fryeburg Academy · Sacopee Valley · Poland Regional',coverageNote='Schedules and reported scores checked October 10. Missing results remain pending; source listings may be incomplete. Cross country and volleyball need a fresh source check. Official MPA rankings could not be retrieved. This is a reviewed snapshot, not a live feed.')
teams=[dict(name=n,highlight=True) for n in p['coverage']]
summary=[]
for team in p['coverage']:
 for sport in ['Football','Boys Soccer','Girls Soccer','Field Hockey']:
  relevant=[x for x in rows if x['sport']==sport and (team in (x['away'],x['home']) or (team in ('Oxford Hills','Buckfield') and sport=='Football' and 'Oxford Hills/Buckfield' in (x['away'],x['home'])))]
  if not relevant:continue
  completed=[x for x in relevant if x['completed']];pending=[x for x in relevant if not x['completed'] and x['dateISO']<=today];latest=completed[-1] if completed else None
  summary.append(dict(team=team,sport=sport,rank='—',record='Not verified',status='Official ranking pending',latest=(f"{latest['date']}: {latest['away']} {latest['awayScore']}–{latest['homeScore']} {latest['home']}" if latest else 'No verified result'),sourceUrl='https://www.mpa.cc/TournamentCentralRankings.aspx',pending=len(pending)))
data=dict(meta=meta,schedule=rows,teams=teams,athletes=[],realignments=b['realignments'],standings=dict(lastUpdated=today+' — official rankings pending verification',rows=summary,football=[],note='The September preseason predictions have been removed. Official ranks, full-season records and playoff eligibility are withheld until verified against the current MPA standings. Football has separate seeding rules. Listed scores are reported results; missing scores are not losses.'),updateLog=[dict(week='October refresh',date=today,summary=f"Refreshed {len(rows)} source-linked games and reported results for WMR coverage schools. Duplicate scheduled/result rows reconciled. Missing results and source conflicts flagged. Official rankings remain pending.")],sources=[dict(name='Local school schedules and reported results',url='https://www.downtownme.com/sports/sports.asp',use='September–October listings checked October 10; dates/times may need school confirmation.'),dict(name='niftiIQ football schedules',url='https://niftiiq.com/maine/football/',use='Independent football schedule/result listings, checked October 10. Not official MPA rankings.'),dict(name='Varsity Maine daily scores',url=vm,use='October 9 football results.'),dict(name='Gould Academy athletics',url='https://www.gouldacademy.org/athletics',use='Prep-school schedules; Gould does not share the public-school MPA ranking structure.'),dict(name='Hyde School boys soccer',url='https://www.hyde.edu/athletics/our-teams/boys-varsity-soccer',use='October 7 Gould result.'),dict(name='MPA official standings',url='https://www.mpa.cc/TournamentCentralRankings.aspx',use='Official ranks and tournament seeds; automated retrieval was blocked.'),dict(name='MPA 2026 soccer bulletin',url='https://www.mpa.cc/resources/Tournament%20Info/Soccer%20Boys/Bulletin%202026-27.pdf',use='Current soccer playoff rules and dates.')])
(R/'js/data.js').write_text('/* Reviewed sports snapshot; see linked sources and verification notes. */\nwindow.WM_DATA = '+json.dumps(data,indent=2,ensure_ascii=False)+';\n')
print(len(rows),'rows;',sum(x['completed'] for x in rows),'reported scores;',len(summary),'team/sport entries')
