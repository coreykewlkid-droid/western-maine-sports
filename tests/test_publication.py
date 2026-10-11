"""Publication checks run entirely offline; fixtures are never written to the site."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from publish_data import ROOT, build_data
from refresh_data import parse_page
from sports_data import COVERAGE, source_url_valid, verified_final

class PublicationTests(unittest.TestCase):
    def test_rebuild_matches_published_data(self):
        published = json.loads((ROOT / 'js/data.js').read_text().split('window.WM_DATA = ', 1)[1].rsplit(';', 1)[0])
        self.assertEqual(build_data(), published)

    def test_reject_duplicate_games_unapproved_finals_future_reviews_and_invalid_sources(self):
        original = json.loads((ROOT / 'verified_schedule.json').read_text())
        for kind in ('duplicate', 'unapproved', 'future_review', 'invalid_source', 'outside_coverage'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                data = copy.deepcopy(original)
                row = next(r for r in data['schedule'] if r['verification'] == 'verified')
                if kind == 'duplicate': data['schedule'].append(copy.deepcopy(row))
                elif kind == 'unapproved': row.pop('resultVerifiedOn')
                elif kind == 'future_review': row['resultVerifiedOn'] = '2026-12-01'
                elif kind == 'invalid_source': row['sourceUrl'] = 'javascript:alert(1)'
                else: row.update(away='Hebron Academy', home='Hyde School')
                (root / 'verified_schedule.json').write_text(json.dumps(data))
                for name in ('reference-september.json', 'standings_verified.json'):
                    (root / name).write_bytes((ROOT / name).read_bytes())
                with self.assertRaises(ValueError): build_data(root)

    def test_candidates_are_not_approved_and_source_result_order_does_not_imply_venue(self):
        import datetime
        page='2026-2027 Schedules<tr class="sport-title"><td>Soccer - Boys</td></tr><tr class="line-single"><td>3:30 pm 10.5.2026 – Telstar 3, Gould Academy 2</td></tr>'
        rows=parse_page(page, 'Telstar', 'https://school.example/scores', datetime.date(2026,10,10))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['verification'], 'pending')
        self.assertFalse(rows[0]['venueKnown'])
        self.assertFalse(verified_final(rows[0], '2026-10-11'))

    def test_mpa_sources_require_exact_official_hostname(self):
        self.assertTrue(source_url_valid('https://www.mpa.cc/TournamentCentralRankings.aspx', official=True))
        self.assertFalse(source_url_valid('https://www.mpa.cc.evil.example/', official=True))
        self.assertFalse(source_url_valid('https://secret@www.mpa.cc/', official=True))

    def test_scope_is_exactly_nine_and_standings_are_not_computed_from_partial_scores(self):
        data = build_data()
        self.assertEqual({t['name'] for t in data['teams']}, set(COVERAGE))
        for s in data['standings']['rows']:
            if s['team'] == 'Gould Academy':
                self.assertEqual(s['rank'], 'N/A')
                self.assertEqual(s['record'], 'Not verified')
            self.assertNotIn('playoff', s)

if __name__ == '__main__':
    unittest.main()
