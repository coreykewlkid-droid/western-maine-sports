# Western Maine Fall 2026 Sports Dashboard

A source-linked sports resource for Western Maine Report’s nine coverage schools: Mountain Valley, Dirigo, Telstar, Buckfield, Oxford Hills Comprehensive (stored as Oxford Hills), Gould Academy, Fryeburg Academy, Sacopee Valley and Poland Regional. Other schools appear in current game listings only as opponents. Cooperative teams remain associated with their coverage schools.

[Open the dashboard](https://coreykewlkid-droid.github.io/western-maine-sports/).

## Dated snapshot and standings

The game and MPA source snapshot is **October 10, 2026**, not a live feed. The October 11 integrity review retains the October 10 capture date. There are 321 source-linked entries and 250 confirmed finals after withholding the conflicting Gould–Hyde result.

`standings_verified.json` preserves all 32 supplied school/sport rows and their original ranks, season records, official source links and October 10 capture dates. The overview and standings table display **31 distinct MPA tournament entries** because Oxford Hills/Buckfield football is one cooperative team. Its supplied MPA record remains 4–1; a discrepancy with the score listings is explicitly flagged, not resolved by guessing.

Filter standings by sport or coverage school. Rank links open the **current** [MPA rankings page](https://www.mpa.cc/TournamentCentralRankings.aspx), which can differ from this historical snapshot. The copied standings brief includes every matching captured entry and its date. No season record is inferred from incomplete score listings.

In-season tournament rank does not confirm playoff qualification or a seed. The tracker shows “Not confirmed” unless a reviewed `playoff` object includes `confirmed: true`, a `status`, ISO `checked` date and official MPA `sourceUrl`; an optional `seed` must be a positive integer. The confirmation date is displayed. Gould’s prep-school standings remain separate and unverified.

The September Classification Archive is retained as historical reference and has not been reverified. Cross-country meets and volleyball game listings still need a fresh source check. The Sacopee cooperative volleyball ranking is available independently of those missing game listings.

## Weekly report generator

Open **Update Center → Weekly Sports Report Generator**:

1. Select inclusive start and end dates, with optional sport and school filters.
2. Select **Generate reports**.
3. Review the included-source list and the omitted-game list.
4. Use **Copy written report** for Phil or **Copy narration** for Scot.

The default range is the last seven days of the source snapshot. Both versions list games in date order and group each day by sport. The narration repeats the day and sport, uses spoken score separators, and identifies the Oxford Hills/Buckfield cooperative team. Routine reports contain no athlete names, quotations or inferred statistics.

Only explicitly reviewed, source-linked finals with complete numeric scores are eligible. Missing, disputed, unreviewed, future, exhibition, non-varsity and unsupported meet entries are excluded. Reversed duplicate listings count once; conflicting scores are withheld even if one row was previously marked verified. A tie remains a tie. Changing the selections clears the previous report and disables copying until regeneration. Selecting newer dates does not fetch results.

Copy buttons use the browser clipboard and a selection fallback. If permission is unavailable, use the indicated keyboard or device Copy command.

## Run and check

Open `index.html` or serve this static repository. The dashboard needs no build step or runtime dependencies.

Run the offline publication and reporting checks:

```sh
python publish_data.py
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/report.test.js
node --check js/app.js
```

The tests cover publication consistency, source and date validation, standings preservation, local coverage, reversed duplicates, score conflicts, losses, ties, narration, name exclusion and confirmed playoff evidence. Synthetic test fixtures are never published.

For a browser layout check, open `tests/responsive.html` through the same static server. It embeds the actual dashboard at 375, 768 and 1280 pixel viewport widths without altering the main page. Tables should scroll within their wrappers; report controls and text should fit their viewport.

## Fetch, verify, then publish

`refresh_data.py` uses Python’s standard library to fetch local schedule listings. It writes **`schedule_candidates.json`**, never the reviewed publication file or `js/data.js`. Every fetched result is `verification: "pending"`. Score disagreements retain the competing reports and source URLs. Possible rescheduled duplicates and start-time differences are flagged. `--cached` can inspect the ignored `source_cache/` files.

`varsitymaine_updater.py` is a secondary candidate collector restricted to the same nine schools. It writes the ignored `varsitymaine_schedule.json`; its additional dependencies are listed in `requirements-updater.txt`. Neither collector publishes or approves results.

Before moving a candidate into **`verified_schedule.json`**:

- Check the correct season, date, opponent and varsity status against official MPA results, school athletic pages, or trustworthy final-score reports.
- Resolve duplicate dates and conflicting scores. A scheduled listing alone does not verify completion.
- Preserve prior reviewed information and the sources behind any correction. Keep unresolved disagreements pending or disputed.
- Set `verification: "verified"` and a dated `resultVerifiedOn` only after checking the final. Retain `sourceUrl`, `checked`, numeric `awayScore`/`homeScore`, and matching ISO/raw game dates. Result-order fields do not imply venue; use `venueKnown: true` only when the source establishes home and away.
- Record the source snapshot’s `checked` date and the publication review’s `reviewedOn` separately. Capture new MPA standings deliberately; do not relabel the October 10 rows as live.

Run `publish_data.py` after review. It rebuilds `js/data.js` **offline** from the reviewed schedule, standings and classification archive, validating coverage, duplicate games, sources, dates, score approvals, ranks and records. It does not scrape sources, infer records, replace disagreements or require private cached pages. Commit the reviewed inputs and generated data together.

The publisher also versions local script and stylesheet links in `index.html` by their contents, so a newly deployed page does not mix cached scripts with newer data. Run it after changing those assets, and commit the updated page with them.

The older `generate_data.py` now writes an unpublished historical candidate instead of overwriting the dashboard. `build_xc.py`, `js/xc_meets.json` and `teams_watched.txt` are historical resources and are not used by the current dashboard. Their broader scope and dates need review before reuse.

The update-log form is an in-session scratchpad. Download its JSON to retain notes; logging or copying a template does not change the published data.

## Integrity review — October 11

- **Gould–Hyde, October 7 boys’ soccer:** [Hyde’s official page](https://www.hyde.edu/athletics/our-teams/boys-varsity-soccer) lists an 8–1 win; [Gould’s official page](https://www.gouldacademy.org/athleticsfsel-3707/boys-varsity-soccer) lists a 1–9 loss. The original 1–8 row is retained as `disputed`, with both source reports. It is withheld from confirmed finals, latest-result summaries and weekly reports until the schools resolve it.
- **Mountain Valley’s October 10 football opponent:** the truncated “John Bapst/Bangor Christian/Ce” label was expanded to “John Bapst/Bangor Christian/Central Coop” using the [official MPA football page](https://www.mpa.cc/SportPages/SportPageInfo.aspx?TournamentID=3). The original label and dated verification source are retained; no score was added.
- The five prior schedule-review flags remain. No guessed scores, inferred records, new athlete names or unconfirmed playoff seeds were published.

