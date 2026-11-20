---
name: new-case
description: Write a new murder mystery case for this app (characters, timelines, clues, puzzles, solution, map) as a checked, playtested case folder in cases/. Use when the user wants to create, generate, draft or add a mystery, case or scenario, or turn a story or theme into one.
---

# Writing a new case

A case is one folder, `cases/<slug>/`, holding `case.json` and the JSON files it links to. The app reads nothing else: no code changes are needed to add a case. You are done when the folder passes both checks below, the story holds together for every character, and the work is committed.

Read these as you go:
- [design.md](design.md) before you plan: how to build a mystery that is fair and fun.
- [reference.md](reference.md) before you write files: every file and field, and who sees what.
- `catalog/tests/fixtures/minicase/` is a small complete case that passes every check. Copy its shape.
- `cases/hollowpine/` is a full-size case that has been played at a real party. Use it for tone and length.

## Steps

1. **Get the brief.** You need: setting and tone, player range, rough length, how much the GM is willing to prepare (printed cards are easy; physical props take effort), and anything to avoid (gore, adult themes, an audience of kids). Use what the user already said. Ask once, with AskUserQuestion, only for gaps that change the story; fill the rest from the defaults in design.md and say which you assumed.

2. **Design it on paper first.** Follow design.md: the true events first, then the characters, then the clue chain, then puzzles. Show the user a short outline (victim, killer, motive, method, each character in one line, how the group can prove it, the puzzles) and wait for their go-ahead before writing JSON. The user may want to play, not GM: ask before showing the solution if it's unclear.

3. **Write the files** in `cases/<slug>/`, following reference.md. The slug is lowercase letters, digits and dashes, and must equal the folder name.

4. **Draw the map** (optional but recommended): put the floor plan in `extras.json`, then
   ```
   .venv/bin/python manage.py render_map <slug>
   ```
   and look at `cases/<slug>/public/map.svg` (screenshot it, see reference.md) to fix overlapping text or misplaced doors.

5. **Check it** until both pass. Fix the case, never the checks.
   ```
   .venv/bin/python manage.py migrate            # first time only
   .venv/bin/python manage.py import_case <slug> --draft
   .venv/bin/python manage.py playtest_case <slug>
   ```
   `import_case` checks every file's format and the cross-references between files. `playtest_case` plays a whole game with the smallest and largest cast, solves each puzzle with its own answer, and fails if any player's phone is sent another character's secret, a puzzle answer or the solution before the reveal.

6. **Read it as each player.** The checks can't judge the story. Do the consistency pass at the end of design.md: every character's timeline against the true timeline, every clue against every timeline, every secret goal achievable.

7. **Preview** (if the user wants): `.venv/bin/python manage.py runserver`, open `http://127.0.0.1:8000`, host a game, and open a player link.

8. **Finish.** Commit the folder on a new branch (for example `case/<slug>`) unless the user says otherwise. Don't push to `production` without asking: the server deploys from it, and on deploy every case folder is loaded and published. Tell the user how to deploy (DEPLOY.md, "Updating") and that `import_case <slug> --draft` on the server hides a case.

## Rules

- **Only write inside `cases/<slug>/`.** Don't change app code, schemas or other cases. If the story needs something the app can't do (another puzzle type, a 3D body), say so and use what exists: a `word` or `digits` puzzle, body clues as buttons.
- **Plain text only.** Everything is shown as typed: no HTML, no Markdown. Escape double quotes inside JSON strings (`\"`).
- **Keep secrets where they belong.** A player's phone shows only their own role, the premise, rules, cast list (names, costumes, `who`), the map with room `info`, body clues of open rounds, puzzle prompts and hints, and any extras field a puzzle `shows`. Never put the killer, a motive that gives it away, an answer, or the reveal in any of those. The playtest catches exact copies, not paraphrases: that part is on you.
- **Write for phones and for reading aloud.** Short sentences. Follow the lengths in design.md.
- **Don't reuse Hollowpine's text or puzzles.** Each case should stand on its own.
