#!/usr/bin/env python3
"""Reproduce the reviewed dashboard offline. No fetching or automatic score approval."""
import hashlib
import json
import re
from pathlib import Path
from sports_data import COVERAGE, covered_teams, game_key, iso_date, source_url_valid, verified_final

ROOT = Path(__file__).resolve().parent
MPA = 'https://www.mpa.cc/TournamentCentralRankings.aspx'
SPORTS = ('Football', 'Boys Soccer', 'Girls Soccer', 'Field Hockey', 'Volleyball', 'Girls Volleyball', 'Golf', 'Cross Country')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def build_data(root=ROOT):
    reference = json.loads((root / 'reference-september.json').read_text())
    reviewed = json.loads((root / 'verified_schedule.json').read_text())
    standings = json.loads((root / 'standings_verified.json').read_text())
    checked = reviewed['checked']
    review_date = reviewed['reviewedOn']
    require(iso_date(checked) <= iso_date(review_date), 'Review cannot precede source capture')
    require(set(reviewed['coverage']) == set(COVERAGE), 'Exactly the nine WMR coverage schools are required')
    rows = reviewed['schedule']
    seen = set()
    for row in rows:
        key = game_key(row)
        require(key not in seen, f'Duplicate game: {key}')
        seen.add(key)
        played = iso_date(row['dateISO'])
        require(2026 == played.year and 9 <= played.month <= 11, f'Wrong fall season: {key}')
        require(row['sport'] in SPORTS, f'Unsupported sport: {key}')
        require(row['dateRaw'] == f'{played.month}.{played.day}.{played.year}', f'Conflicting date fields: {key}')
        require(covered_teams(row), f'Game outside WMR coverage: {key}')
        require(source_url_valid(row.get('sourceUrl')), f'Source link required: {key}')
        require(row.get('verification') in ('verified', 'pending', 'disputed'), f'Explicit verification required: {key}')
        require(iso_date(row['checked']) <= iso_date(review_date), f'Future source check: {key}')
        if row['verification'] == 'verified':
            require(verified_final(row, review_date), f'Final needs valid scores, dates and an explicit source review: {key}')
        if row.get('completed'):
            require(played <= iso_date(checked), f'Final after source snapshot: {key}')
            require(all(type(row.get(k)) is int and row[k] >= 0 for k in ('awayScore', 'homeScore')), f'Invalid score: {key}')
        row['coveredTeams'] = covered_teams(row)
    rows.sort(key=lambda g: (g['dateISO'], g['sport'], g['away'], g['home']))

    summary = []
    for team in COVERAGE:
        for sport in SPORTS:
            relevant = [g for g in rows if g['sport'] == sport and team in g['coveredTeams']]
            if not relevant:
                continue
            finals = [g for g in relevant if verified_final(g, review_date)]
            latest = finals[-1] if finals else None
            summary.append(dict(
                team=team, sport=sport, rank='—', record='Not verified',
                status='Official ranking pending', classification='Pending verification',
                region='Pending verification', checked=checked, sourceUrl=MPA,
                pending=sum(not verified_final(g, review_date) and g['dateISO'] <= checked for g in relevant),
                latest=(f"{latest['date']}: {latest['away']} {latest['awayScore']}–{latest['homeScore']} {latest['home']}" if latest else 'No confirmed final in this snapshot'),
            ))
    for item in summary:
        if item['team'] == 'Gould Academy':
            item.update(classification='Prep school', region='MAISAD / NEPSAC', status='Separate prep-school standings', rank='N/A', record='Not verified', sourceUrl='https://www.gouldacademy.org/athletics')

    seen = set()
    for entry in standings:
        key = (entry['team'], entry['sport'])
        require(key not in seen, f'Duplicate standings: {key}')
        seen.add(key)
        require(entry['team'] in COVERAGE or key == ('Massabesic/Sacopee Coop', 'Girls Volleyball'), f'Unknown MPA team: {key}')
        require(entry['team'] != 'Gould Academy', 'Gould prep-school rankings cannot be labeled MPA')
        require(type(entry['rank']) is int and entry['rank'] > 0, f'Invalid rank: {key}')
        require(iso_date(entry['checked']) <= iso_date(checked), f'Standings after source snapshot: {key}')
        require(re.fullmatch(r'\d+-\d+(?:-\d+)?', entry['record']), f'Invalid W-L or W-L-T record: {key}')
        require(source_url_valid(entry['sourceUrl'], official=True), f'Official MPA source required: {key}')
        require(entry['classification'] and entry['region'], f'Class and region required: {key}')
        if entry.get('playoff'):
            playoff = entry['playoff']
            require(playoff.get('confirmed') is True and isinstance(playoff.get('status'), str) and playoff['status'], f'Playoff status must be explicitly confirmed: {key}')
            require(source_url_valid(playoff.get('sourceUrl'), official=True), f'Official playoff source required: {key}')
            require(iso_date(playoff['checked']) <= iso_date(review_date), f'Future playoff confirmation: {key}')
            if playoff.get('seed') is not None:
                require(type(playoff['seed']) is int and playoff['seed'] > 0, f'Invalid confirmed seed: {key}')
        matches = [s for s in summary if (s['team'], s['sport']) == key]
        if not matches:
            summary.append(dict(team=entry['team'], sport=entry['sport'], latest='No confirmed final in this snapshot', pending=0))
            matches = [summary[-1]]
        require(len(matches) == 1, f'Ambiguous standings: {key}')
        matches[0].update(entry, status='Verified MPA snapshot')
    unique = {(s.get('standingTeam', s['team']), s['sport'], s['classification'], s['region']) for s in summary if s['status'] == 'Verified MPA snapshot'}
    standings_date = max((s['checked'] for s in summary if s['status'] == 'Verified MPA snapshot'), default=checked)
    counts = sum(verified_final(g, review_date) for g in rows)
    meta = dict(reference['meta'], generated=checked, checked=checked, reviewedOn=review_date,
        coverage=' · '.join('Oxford Hills Comprehensive' if t == 'Oxford Hills' else t for t in COVERAGE),
        coverageNote=f'Schedules and results are from the {checked} source snapshot; integrity reviewed {review_date}. Finals retain their dated source review. Missing or disputed results are withheld from weekly reports. Cross country and volleyball game listings need a fresh source check. Each MPA rank retains its capture date and is not live.')
    return dict(meta=meta, schedule=rows,
        teams=[dict(name=t, displayName='Oxford Hills Comprehensive' if t == 'Oxford Hills' else t, highlight=True) for t in COVERAGE],
        athletes=[], realignments=reference['realignments'],
        standings=dict(lastUpdated=standings_date, rows=summary, football=[],
            note='Each MPA ranking and season record shows its original capture date; the page update timestamp was not supplied. The cooperative Oxford Hills/Buckfield football entry appears once in the table. Its supplied MPA record differs from score listings and is preserved for reconciliation. Gould follows separate prep-school standings. In-season ranks are not confirmed playoff berths or seeds. Missing scores are not losses.'),
        updateLog=[dict(week='Verification review', date=review_date, summary='Withheld Gould–Hyde boys soccer because official school pages disagree; original score retained. Expanded Mountain Valley’s truncated football opponent name using the official MPA page, retaining the original label. No scores or MPA standings were substituted.'),
            dict(week='October snapshot', date=checked, summary=f'{len(rows)} source-linked entries; {counts} confirmed finals after the conflict review. {len(unique)} distinct MPA tournament entries captured October 10. Missing results and possible rescheduled duplicates remain flagged.')],
        sources=[
            dict(name='MPA official standings', url=MPA, use='Official tournament ranks and season records captured October 10; current pages can differ from this historical snapshot.'),
            dict(name='School athletics pages', url='https://www.gouldacademy.org/athletics', use='Primary schedules and finals; Gould follows prep-school competition. Conflicting scores require confirmation.'),
            dict(name='Hyde School boys soccer', url='https://www.hyde.edu/athletics/our-teams/boys-varsity-soccer', use='October 7 Gould result conflicts with Gould’s page; withheld pending confirmation.'),
            dict(name='Gould boys soccer', url='https://www.gouldacademy.org/athleticsfsel-3707/boys-varsity-soccer', use='October 7 score discrepancy reviewed October 11; school schedules include separate prep competitions.'),
            dict(name='Varsity Maine daily scores', url='https://www.varsitymaine.com/daily-scores-and-schedules-combined', use='Reviewed October 9 football scores in the October 10 snapshot.'),
            dict(name='Local schedules and reported results', url='https://www.downtownme.com/sports/sports.asp', use='Secondary listings reviewed October 10. Confirm missing results, schedule changes and disputes with schools or MPA.'),
            dict(name='niftiIQ football schedules', url='https://niftiiq.com/maine/football/', use='Independent football listings from the reviewed October 10 snapshot; not official MPA rankings.'),
            dict(name='MPA 2026 soccer bulletin', url='https://www.mpa.cc/resources/Tournament%20Info/Soccer%20Boys/Bulletin%202026-27.pdf', use='Official 2026 rules, classifications and tournament dates; latest checked October 11.'),
        ])

def version_asset_links(root=ROOT):
    """Keep a fresh page from mixing cached scripts with newly reviewed data."""
    page = root / 'index.html'
    html = page.read_text()
    for asset in ('css/style.css', 'js/data.js', 'js/report.js', 'js/app.js'):
        version = hashlib.sha256((root / asset).read_bytes()).hexdigest()[:12]
        pattern = r'((?:src|href)=")' + re.escape(asset) + r'(?:\?v=[a-f0-9]+)?(")'
        html, count = re.subn(pattern, lambda m: m[1] + asset + '?v=' + version + m[2], html)
        require(count == 1, f'Expected one page reference for {asset}')
    page.write_text(html)

def main():
    data = build_data()
    (ROOT / 'js/data.js').write_text('/* Reviewed sports snapshot; see linked sources and verification notes. */\nwindow.WM_DATA = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n')
    version_asset_links()
    print(len(data['schedule']), 'entries;', sum(verified_final(g, data['meta']['reviewedOn']) for g in data['schedule']), 'confirmed finals; MPA capture', data['standings']['lastUpdated'])

if __name__ == '__main__':
    main()

