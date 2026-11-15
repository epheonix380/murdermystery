# Murder mystery

A Django app for running murder mystery parties. Anyone can host a game of a case, players get a private link to their character before the party, and on the night the GM runs rounds, puzzles and voting from their phone.

This branch holds the app. `main` still holds the original one-off static site for "The Last Chapter at Hollowpine Lodge", served by GitHub Pages; a copy is kept in `legacy/` because the Hollowpine case files are generated from it.

## Run it locally

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_case
.venv/bin/python manage.py createsuperuser   # for /admin/
.venv/bin/python manage.py runserver
```

With no environment variables it runs in debug mode on SQLite. On the server, settings come from `.env` (see `.env.example`), including `DATABASE_URL` for Postgres.

Run the tests with `.venv/bin/python manage.py test`.

## Layout

| Path | What |
| --- | --- |
| `mystery/` | Django settings and URLs |
| `catalog/` | Cases: the `Case` table, the case-file loader and checker, `import_case` |
| `catalog/schemas/` | JSON schemas for every case file |
| `games/` | Games, players, puzzle solves and votes |
| `cases/<slug>/` | One folder per case |
| `scripts/convert_hollowpine.js` | One-off conversion of `legacy/data.js` into `cases/hollowpine/` |
| `legacy/` | The original static site |

## Cases

Each case is a folder in `cases/`:

| File | Holds | Who sees it |
| --- | --- | --- |
| `case.json` | Slug, title, premise, rules, min and max players, victim, map, and the names of the files below | Everyone browsing cases |
| `roles.json` | Each character: costume, attitude, timeline, secret, goal, starting props | A player sees only their own |
| `clues.json` | Number of rounds, body hotspots, location cards, sealed locations and what unlocks them | Players, once unlocked |
| `puzzles.json` | Prompts and answers | Prompts to players; answers never leave the server |
| `props.json` | Physical objects the GM prepares | GM |
| `solution.json` | The killer, the reveal text and the true timeline | GM, until the reveal |
| `extras.json` | Anything unique to the case, such as Hollowpine's cipher and floor plan | Depends on the field |
| `public/` | Files browsers may load, such as the map image | Everyone |

Only `public/` is ever served. The JSON files are read by the server and never sent as files.

To add or change a case, edit its files and run:

```
.venv/bin/python manage.py import_case <slug>    # or no slug for every case
```

This checks every file against its schema in `catalog/schemas/`, checks the files against each other (the killer is a core role, puzzles unlock real sealed locations, clue rounds exist, and so on), and lists every problem it finds. Only a case with no problems is loaded. It then saves the title, player range, map link and the clue, puzzle and prop counts to the `Case` table for the case browser. Add `--draft` to hide a case from the browser or `--publish` to show it.
