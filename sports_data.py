"""Shared publication rules. Fetching a result never approves it for publication."""
from datetime import date
from urllib.parse import urlparse
import re

COVERAGE = (
    'Mountain Valley', 'Dirigo', 'Telstar', 'Buckfield', 'Oxford Hills',
    'Gould Academy', 'Fryeburg Academy', 'Sacopee Valley', 'Poland Regional',
)
ALIASES = {
    'oxford hills comprehensive': 'Oxford Hills', 'poland': 'Poland Regional',
    'telstar regional': 'Telstar', 'fryeburg': 'Fryeburg Academy',
    'gould': 'Gould Academy', 'oxford hills/buckfield coop': 'Oxford Hills/Buckfield',
    'oxford hills/buckfield cooperative': 'Oxford Hills/Buckfield',
}

def canonical_team(name):
    name = re.sub(r'\s+', ' ', str(name)).strip()
    return ALIASES.get(name.lower(), name)

def covered_teams(row):
    names = {canonical_team(row.get(k, '')) for k in ('away', 'home')}
    covered = [t for t in COVERAGE if t in names]
    if row.get('sport') == 'Football' and 'Oxford Hills/Buckfield' in names:
        covered += [t for t in ('Oxford Hills', 'Buckfield') if t not in covered]
    if row.get('sport') in ('Volleyball', 'Girls Volleyball') and 'Massabesic/Sacopee Coop' in names:
        covered += ['Sacopee Valley'] if 'Sacopee Valley' not in covered else []
    return covered

def game_key(row):
    return (row['sport'], row['dateISO'], *sorted(canonical_team(row[k]) for k in ('away', 'home')))

def source_url_valid(url, official=False):
    parsed = urlparse(str(url))
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        return False
    return not official or parsed.hostname.lower() in ('mpa.cc', 'www.mpa.cc')

def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Date must be YYYY-MM-DD')
    return date.fromisoformat(value)

def verified_final(row, as_of):
    if row.get('completed') is not True or row.get('verification') != 'verified' or row.get('reviewNote'):
        return False
    if row.get('eventType', 'game') != 'game' or row.get('exhibition') or row.get('level', 'Varsity') != 'Varsity':
        return False
    if row.get('sport') not in ('Football', 'Boys Soccer', 'Girls Soccer', 'Field Hockey', 'Volleyball', 'Girls Volleyball', 'Golf'):
        return False
    if re.search(r'cancel|postpon|suspend', row.get('status', ''), re.I):
        return False
    if not covered_teams(row) or not source_url_valid(row.get('sourceUrl')):
        return False
    if any(type(row.get(k)) is not int or row[k] < 0 for k in ('awayScore', 'homeScore')):
        return False
    try:
        played, reviewed, cutoff = iso_date(row['dateISO']), iso_date(row['resultVerifiedOn']), iso_date(as_of)
    except (KeyError, ValueError):
        return False
    return played <= reviewed <= cutoff
