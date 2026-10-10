# Western Maine Fall 2026 Sports Dashboard

Source-linked schedules and reported scores for Mountain Valley, Dirigo, Telstar, Buckfield, Oxford Hills, Gould Academy, Fryeburg Academy, Sacopee Valley and Poland Regional.

## October 10 refresh

The reviewed snapshot contains 321 entries and 251 reported scores. Switch between upcoming games, reported finals, missing results and all entries. Search by school and filter by sport. Completed result listings do not imply home/away venue.

Preseason predictions were removed. Official ranks, season records and playoff qualification are pending MPA verification. Cross country and volleyball need a fresh source check. September classifications are preserved as an explicitly dated reference archive. This is a snapshot, not an automatic live feed.

## Run

Open `index.html` in a browser or serve the repository with a local static web server. No build or dependencies are required.

## Refresh and review

`python refresh_data.py` fetches the current local school listings with Python's standard library and writes `verified_schedule.json`. It does not overwrite the dashboard. It merges identical scheduled/result entries, withholds conflicting scores and flags possible rescheduled duplicates. Review all missing results and date/time conflicts against MPA and school sources before publication. The private `source_cache/` scratch directory is ignored by Git.

`publish_data.py` reproduces the October 10 reviewed edition from the reviewed JSON plus cached football source pages and dated, manually reviewed supplemental results. It deliberately refuses a newer date until those supplemental sources are reverified. `reference-september.json` preserves the original classification reference used by the builder.

The older `varsitymaine_updater.py`, `generate_data.py` and `build_xc.py` remain historical utilities. Their assumptions, coverage and sources need review before use. The current browser dashboard reads `js/data.js`.

The update log form is a temporary in-session scratchpad. Download its JSON to retain notes; it does not update the published data.
