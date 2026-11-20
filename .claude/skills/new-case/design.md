# Designing a case

A good case lets a group of friends, who have read their sheets once, work out who did it in about two hours by talking, searching and solving, with every player suspicious at some point and every player with something to do.

## Defaults when the user doesn't say

| | Default |
| --- | --- |
| Players | 4 core roles, plus 2 or 3 optional ones (so 4 to 7) |
| Length | About 2 hours: 2 rounds |
| Puzzles | 2 or 3 |
| Clues | 6 to 8 body clues, 25 to 40 cards |
| Props | 2 or 3 physical objects |
| Tone | Spooky or cosy, PG-13: a death, no gore |

## 1. The truth first

Write what really happened before any character exists:

- **Victim**: who they were and why several people had reason to hate them.
- **Killer**: a core role. Motive (one the others don't know), method, and the weapon or means.
- **The true timeline**: the half hour around the murder, minute by minute: where the killer was, what they did, and what they did to cover it (a false time of death, a moved body, a borrowed costume). The cover-up is what makes it a puzzle: the killer's alibi should look solid until the group finds the trick.
- **The crime scene**: where it happened and how the killer got there and away unseen. This often becomes a route puzzle.

## 2. The characters

Each role needs:

- **A reason to be suspected**: a motive, an opportunity, or something they lied about. Every innocent character should look guilty at some point.
- **A secret that isn't the murder**: debt, an affair, a theft, a hidden identity. Secrets give innocent players something to hide, which keeps the talk going.
- **A secret goal** that's checkable at the end and makes them act: hold a prop when the game ends, make sure someone gets at least two votes, never let a secret come out, learn a fact. The killer's goal is "Don't get the most votes."
- **A timeline** that agrees with everyone else's. Shared moments ("Marcus left for a smoke at 10:40") should appear on several sheets from different angles. Mark guilty-looking moments `hide: true`.
- **Things they know about others** (`others`): at least two, including something true that points toward the killer, so the solution is spread across the table.
- **Tips** for playing: what to push, what to protect.

Core roles (always cast) carry the story. Optional roles add colour and red herrings: everything needed to solve the case must work without them, and their cards use `requires_role`.

The killer gets a `story` (the lie they tell) and tips on deflecting. Give their alibi a witness who was fooled.

## 3. The clue chain

List the facts the group must establish (the killer's real movements, the cover-up, the motive). For each, plan **at least two independent clues**, so missing one doesn't sink the game. Spread them:

- Round 1: the obvious scene, a broad set of suspects, the first hints that the official story is wrong.
- Puzzles open sealed locations holding the strongest evidence.
- Round 2: the clues that break the alibi and confirm the motive.

Mix in red herrings that point at innocent characters and can be explained by their secrets. Each card is one to three sentences describing something physical. Write `key_proof` in solution.json as this chain, with clue ids.

## 4. Puzzles

Each puzzle should be solved from clues the players have found, and unlock a sealed location:

- `digits`: a code from a date or number spread across cards ("the night it all began" plus a book cover's publication date).
- `word`: a cipher (a Caesar shift with the shift hidden in a clue) or a riddle; the answer is one distinctive word.
- `route`: "how did they get there unseen?" on the map; the answer is the killer's real path, ending at the crime scene.

Give each a hint and a GM `explanation`.

## 5. Writing it

| Text | Length |
| --- | --- |
| Premise | 3 to 5 paragraphs, under 150 words |
| `who`, `attitude`, `costume` | One line each |
| `secret` | 2 to 4 sentences |
| Timeline | 6 to 15 entries, one sentence each |
| `others`, `tips` | 2 to 4 entries |
| Body clue, card | 1 to 3 sentences |
| Reveal | 120 to 200 words, read aloud, ends by naming the killer |

Costumes should be easy to put together at home.

Run of show for 2 rounds: premise read aloud (10 min), players reread sheets (10), search round 1 (20), discussion (15), puzzles (20), round 2 search and discussion (25), final statements, vote, reveal and goals (15).

## 6. Consistency pass

After the checks pass, read the case once as each character:

- Every time and place in every timeline agrees with the true timeline and with every other timeline. The only differences are lies the liar knows they're telling.
- Every clue is consistent with what really happened, and no clue makes an innocent character's guilt certain.
- The killer can be identified with any one optional role missing, and from core-role clues alone.
- Each puzzle can be solved from clues that exist before it's needed, and its answer appears nowhere players can see.
- Each secret goal can be achieved and checked by the GM at the end.
- Names, places and objects are spelled the same everywhere (the map, cards, timelines).
- Nothing public (premise, cast lines, map info, body clues, prompts, hints) gives away the killer.
