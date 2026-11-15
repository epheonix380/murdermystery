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

`runserver` uses Daphne, so WebSockets work locally too. With no environment variables it runs in debug mode on SQLite. On the server, settings come from `.env` (see `.env.example`), including `DATABASE_URL` for Postgres.

Run the tests with `.venv/bin/python manage.py test`.

`e2e/full_game.js` plays a whole game in real browsers (one GM, four players) against a running server:

```
.venv/bin/python manage.py runserver 8765
node e2e/full_game.js http://127.0.0.1:8765
```

## Pages

| URL | Who | What |
| --- | --- | --- |
| `/` | Anyone | Case browser: map, player range, clue, puzzle and prop counts |
| `/host/new/<slug>/` | Anyone | Start a game: party date and number of players |
| `/host/` | The host | Their active game: players, props to prepare, GM link, end game |
| `/host/players/` | The host | Names and characters; chosen roles are kept, the rest are cast at random |
| `/host/links/` | The host | Copy-paste page with every player's private link |
| `/gm/<token>/` | The host | Private GM link: makes any browser the host of that game |
| `/host/print/` | The host | Printable clue cards (only for characters in this game) and location labels |
| `/p/<token>/` | One player | Their character sheet, then on the night the case, map, body, puzzles, voting and reveal |

On game night the host's dashboard starts the game, moves rounds on, opens voting and reveals the killer. Players' phones update straight away: each page keeps a WebSocket open (`/ws/p/<token>/` or `/ws/gm/<token>/`), the server sends a bare "changed" when the game changes, and the page fetches its own state from `/p/<token>/state/` or `/host/state/`. All the rules about who sees what are in `games/engine.py`. Puzzle answers are checked on the server and never sent to players, and each player gets 8 wrong guesses a minute.

Hosts don't sign up. Starting a game creates an anonymous visitor id, kept in a cookie; each visitor can host one active game at a time. Games end when the host ends them, or a week after the party date.

## Deploying

See [DEPLOY.md](DEPLOY.md). In short: one Docker container (`Dockerfile`, `docker-compose.yml`) running Daphne on `127.0.0.1:8100` with a 300 MB memory cap, Postgres on the host, nginx in front (`deploy/nginx-murdermystery.conf`) and HTTPS from certbot. Static files are served by whitenoise. GitHub Actions runs the tests against Postgres on every push.

## Layout

| Path | What |
| --- | --- |
| `mystery/` | Django settings and URLs |
| `catalog/` | Cases: the `Case` table, the case-file loader and checker, `import_case` |
| `catalog/schemas/` | JSON schemas for every case file |
| `games/` | Games, players, puzzle solves and votes |
| `cases/<slug>/` | One folder per case |
| `scripts/convert_hollowpine.js` | One-off conversion of `legacy/data.js` into `cases/hollowpine/` |
| `deploy/` | Container entrypoint, nginx site, systemd unit |
| `e2e/` | Browser test of a whole game |
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
| `extras.json` | Anything unique to the case, such as Hollowpine's cipher, séance line and floor plan | The floor plan to everyone; a field a puzzle or card `shows` with that puzzle; the rest to the GM |
| `public/` | Files browsers may load, such as the map image | Everyone |

`case.json` can also name a `body_viewer`: a script in `public/` that draws the body in 3D with three.js. It must define `window.CaseBody(wrap, onPick)` returning `{show(hotspots), highlight(id), resize()}`; see `cases/hollowpine/public/body.js`. Without one, players get the body clues as buttons.

Only `public/` is ever served. The JSON files are read by the server and never sent as files.

To add or change a case, edit its files and run:

```
.venv/bin/python manage.py import_case <slug>    # or no slug for every case
```

This checks every file against its schema in `catalog/schemas/`, checks the files against each other (the killer is a core role, puzzles unlock real sealed locations, clue rounds exist, and so on), and lists every problem it finds. Only a case with no problems is loaded. It then saves the title, player range, map link and the clue, puzzle and prop counts to the `Case` table for the case browser. Add `--draft` to hide a case from the browser or `--publish` to show it.
