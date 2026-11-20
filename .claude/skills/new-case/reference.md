# Case file reference

Every file is checked against its JSON schema in `catalog/schemas/`. This page says what each field is for and where it shows up. "Phone" means a player's phone; "GM" means the host's dashboard.

## Who sees what

| Content | Before the party | On the night | After the reveal |
| --- | --- | --- | --- |
| Premise, rules, victim, map (with room `info`) | Every player | Every player | Every player |
| Cast list: each cast role's `name`, `costume`, `who`, and who plays it | Every player | Every player | Every player |
| One role's sheet (everything else in `roles.json`) | That player only | That player only | That player only |
| Body clues | Nobody | Phones, once their round starts | Phones, all of them |
| Clue cards | Printed by the GM and hidden in rooms | Found by players | |
| Puzzle prompts, hints, and the extras field a puzzle `shows` | Nobody | Phones | |
| Puzzle answers and explanations | GM only, never phones | | |
| Which sealed locations are open | | Phones and GM | |
| Every cast role's secret goal | | | Phones (reveal page) |
| `solution.json` | GM (behind a spoiler toggle) | GM | Phones: summary, reveal text, true timeline, killer |
| Props, run of show, other extras text | GM | GM | GM |

## case.json

```json
{
  "slug": "briar-hall",
  "title": "The Last Toast at Briar Hall",
  "premise": ["Paragraph one.", "Paragraph two."],
  "rules": ["One rule per line."],
  "min_players": 3,
  "max_players": 4,
  "victim": { "name": "Lord Edmund Voss", "text": "One line about them." },
  "map": "public/map.svg",
  "run_of_show": ["Step (minutes)", "..."],
  "files": { "roles": "roles.json", "clues": "clues.json", "puzzles": "puzzles.json",
             "props": "props.json", "solution": "solution.json", "extras": "extras.json" }
}
```

- `slug`: lowercase letters, digits and dashes; must equal the folder name.
- `premise`: read aloud by the GM at the start and shown on every phone. 3 to 5 short paragraphs. Ends with why nobody can leave.
- `rules`: 3 to 6 lines. Always include that the secret goal must stay hidden, that props change hands only when handed over, and how voting works.
- `min_players` must be at least the number of core roles; `max_players` at most the number of roles. Usually min = core roles and max = all roles.
- `map`: `public/map.svg` from `render_map`, another image under `public/`, an `https://` link, or leave it out.
- `run_of_show`: the GM's running order with minutes; see design.md.
- `body_viewer`: leave out. It names a hand-written three.js script (see `cases/hollowpine/public/body.js`); without it, body clues show as buttons, which works well.
- `files`: keep the names as shown. `extras` may be left out if you have no extras.

## roles.json

A list of characters. Every field below except `id`, `name`, `core`, `costume`, `who`, `goal`, `secret` and `timeline` is optional.

```json
{
  "id": "BUTLER",
  "name": "Hollis Grey",
  "core": true,
  "costume": "Black tailcoat, white gloves",
  "who": "Butler at Briar Hall for thirty years.",
  "attitude": "Calm, formal, never raises his voice.",
  "cornered": "\"A line to say when accused.\"",
  "goal": "Don't get the most votes.",
  "secret": "You are the killer. ...",
  "timeline": [
    { "time": "8:40", "place": "Wine Cellar", "text": "What you did.", "hide": true }
  ],
  "story": ["What you tell everyone instead (only for characters who lie)."],
  "others": [{ "name": "Clara", "text": "What you know or think about her." }],
  "tips": ["How to play this character well."],
  "starting_props": ["sealed-will"]
}
```

- `id`: letters, digits, `_` or `-`; short uppercase words read well (`BUTLER`, `HEIR`). Unique.
- `core: true` roles are always cast. `false` roles are optional: they fill extra places and must not be needed to solve the case.
- `costume` and `who` are public (cast list). Don't put secrets there.
- `goal`: the secret goal, hidden behind a "tap to peek" box. Must be checkable at the end (see design.md). Identical goal text for two roles is fine.
- `secret`: shown on that player's sheet only. The killer's secret starts with "You are the killer." and says what they did and why. The phone also shows "YOU ARE THE KILLER" to whoever has `solution.json`'s killer role.
- `timeline`: the character's evening, in order. `hide: true` marks a moment they'd rather nobody found out (shown with a "Keep quiet" tag).
- `story`: the lie a character tells, if any. Shown as "What you tell everyone (it's a lie)".
- `starting_props`: ids from `props.json` the GM hands this character at the start. Shown on their sheet and on the GM's prop list.

## clues.json

```json
{
  "rounds": 2,
  "body": [{ "id": "B1", "round": 1, "label": "Lips", "text": "..." }],
  "cards": [
    { "id": "C01", "location": "Ballroom", "round": 1, "text": "...", "shows": "port_label" },
    { "id": "C09", "location": "Garden", "round": 1, "text": "...", "requires_role": "GUEST" }
  ],
  "sealed": [
    { "location": "Wine Cellar", "instructions": "Open after the group solves The Cellar Lock", "unlocked_by_puzzle": "cellar" },
    { "location": "Butler's Room", "instructions": "Open when Round 2 starts", "unlocked_by_round": 2 }
  ]
}
```

- `rounds`: usually 2. The GM starts each round from the dashboard.
- `body`: examining the body, on every phone. A clue appears when its round starts. Short `label` (the button), one to three sentences of `text`. Never depend on optional roles.
- `cards`: printed by the GM and hidden at their `location` before the game. `round` is printed on the card; a card of a later round should be in a sealed location or handed out by the GM when that round starts.
- `shows` (cards and puzzles): the name of an `extras.json` string field printed under the card (for example a cipher). That field becomes public.
- `requires_role`: an optional role's id. The card is left out of printing when that role isn't cast.
- `sealed`: places whose cards go in a sealed envelope. Each is opened by exactly one of `unlocked_by_puzzle` (a puzzle id) or `unlocked_by_round`. The GM's dashboard shows "Open it" when the time comes; players see the envelope's name when they solve its puzzle. Put the decisive evidence here.
- Ids: `B1`, `B2`... for body clues and `C01`, `C02`... for cards, unique across both.

## puzzles.json

```json
{
  "id": "cellar",
  "title": "The Cellar Lock",
  "prompt": "What players see.",
  "hint": "A nudge, hidden behind a tap.",
  "unlocks": "Wine Cellar",
  "shows": "cipher",
  "answer": { "type": "digits", "accept": ["1887"] },
  "explanation": "For the GM: why that's the answer and which clues lead there."
}
```

Answers are checked on the server; players get 8 wrong guesses a minute. Three types:

- `digits`: only the digits typed are compared, so `10/31/98` matches `103198`. List every form you'll accept.
- `word`: correct if any accepted word appears as a whole word, ignoring case (`"his sight."` matches `SIGHT`; `insight` doesn't). Choose a distinctive word; a common one like "the" would match almost anything.
- `route`: players tap rooms on the map, starting from `start` (which they don't tap), and the rooms tapped must equal `sequence` exactly. Needs a map in `extras.json`, and every room id must be on it. A wrong route whose last room differs from the sequence's last room gets the hint "The route has to end where the crime happened", so end the sequence at the crime scene.

`unlocks` (optional) must be a `location` from `clues.json`'s `sealed`. `explanation` is shown only to the GM. Two or three puzzles is plenty.

## props.json

Physical objects the GM prepares. The app lists them for the GM and shows starting props on sheets; it doesn't track who holds what during the game.

```json
[
  { "id": "ledger", "name": "The Cellar Ledger", "description": "...", "placed_at": "Wine Cellar", "clue": "C04" },
  { "id": "sealed-will", "name": "The Sealed Will", "description": "..." }
]
```

- `placed_at`: where the GM hides it. Leave it out when a character starts with it (`starting_props` in roles.json).
- `clue`: the card that goes with it, which prints in bold as an item card.
- Ids: lowercase with dashes.

## solution.json

```json
{
  "killer": "BUTLER",
  "summary": "One or two sentences: who, how, when, why.",
  "key_proof": ["Each piece of decisive evidence with its clue ids (C01, B3)"],
  "reveal": "The script the GM reads aloud at the end. Ends by naming the killer.",
  "timeline": [{ "time": "8:40", "place": "Wine Cellar", "text": "What really happened." }]
}
```

`killer` must be a core role. Everything here is GM-only until the reveal; then phones show the summary, the reveal text, the true timeline and the killer.

## extras.json

Anything else. String fields are GM notes on the dashboard (behind a spoiler toggle, titled by the field name), unless a puzzle or card `shows` them, in which case they're public. Name fields plainly: `cipher`, `seance`, `port_label`.

### The map

```json
"map": {
  "rooms": [
    { "id": "ballroom", "name": "Ballroom", "x": 24, "y": 80, "w": 240, "h": 140,
      "lines": ["The toast"], "info": "Shown when a player taps the room.",
      "kind": "outdoor", "sealed": "Locked", "center": true }
  ],
  "doors": [[264, 100, 264, 130]],
  "walls": [[24, 80, 456, 140]],
  "labels": [{ "x": 380, "y": 232, "text": "Stair down" }]
}
```

- Coordinates are pixels; keep the whole plan under about 760 wide. The image is cropped to the rooms, so keep `walls` and `labels` inside the area the rooms cover. On narrow phones the map scrolls sideways.
- Rooms are rectangles that share edges where they touch. `id`: lowercase with dashes (used by route puzzles). `name` is drawn at the top left, then each of `lines` below it. Size a room to fit: width at least 24 + 8 × (longest line's characters); height at least 30 + 18 × (number of lines, plus one if `sealed`).
- `kind`: `outdoor` (tinted, rounded) or `upstairs` (dashed edge). `sealed`: short text drawn with a purple dot, for sealed locations. `center: true` centres the name, for long thin rooms with no lines.
- `doors`: short lines `[x1, y1, x2, y2]` on a shared wall, about 30 px long.
- `walls`: thick outlines `[x, y, width, height]`, usually around the main building.
- `labels`: free text, centred on `x`, such as "Back door".
- Every room in a `route` answer must be here. Every clue `location` should be a room.
- `info` is public: never put clues or answers in it.

To look at the map, open `cases/<slug>/public/map.svg` in a browser, or if Playwright is installed (it is in Claude Code cloud sessions):

```
.venv/bin/python manage.py render_map <slug>
node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:780,height:560}});await p.goto('file://'+process.cwd()+'/cases/<slug>/public/map.svg');await p.screenshot({path:'map.png'});await b.close();})()"
```

Then read `map.png`, and delete it afterwards. If you can't see the image, ask the user to open the SVG and describe any overlaps.
