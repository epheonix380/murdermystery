// One-off conversion of the original static site (legacy/data.js and the map
// data in legacy/index.html) into the case-file format in cases/hollowpine/.
//
//   node scripts/convert_hollowpine.js
//   python manage.py render_map hollowpine      # draws public/map.svg
//
// Re-running overwrites the generated files. Hand edits belong in the JSON
// files afterwards, not here.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const out = path.join(root, "cases", "hollowpine");

const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, "legacy", "data.js"), "utf8"), sandbox);
const C = sandbox.window.CASE;

// ROOMS and DOORS live in index.html's script, not data.js.
const html = fs.readFileSync(path.join(root, "legacy", "index.html"), "utf8");
const grab = (name) => {
  const m = html.match(new RegExp("var " + name + " = (\\[[\\s\\S]*?\\]);\\n"));
  if (!m) throw new Error("could not find " + name + " in index.html");
  return vm.runInNewContext(m[1]);
};
const ROOMS = grab("ROOMS");
const DOORS = grab("DOORS");

const write = (name, data) => {
  fs.mkdirSync(path.dirname(path.join(out, name)), { recursive: true });
  fs.writeFileSync(path.join(out, name), JSON.stringify(data, null, 2) + "\n");
};

// ---------- roles ----------
let killer = null;
const roles = Object.entries(C.roles).map(([id, r]) => {
  if (r.killer) killer = id;
  const role = {
    id,
    name: r.name,
    core: !!r.core,
    costume: r.costume,
    who: r.who,
    attitude: r.attitude,
    cornered: r.cornered,
    goal: r.goal,
    secret: r.secret,
    timeline: r.timeline.map(([time, place, text, flag]) => ({ time, place, text, hide: flag === "hide" })),
  };
  if (r.story) role.story = r.story;
  if (r.others) role.others = r.others.map(([name, text]) => ({ name, text }));
  if (r.tips) role.tips = r.tips;
  return role;
});

// ---------- clues ----------
const sealedByLoc = {
  "Edgar's Safe": "safe",
  "Guest Rooms": "page",
  "Umbrella Stand": "route",
  "Ruth's Cabin": null,
};
const clues = {
  rounds: 2,
  body: C.body.map((b) => ({ id: b.id, round: b.round, label: b.label, text: b.text })),
  cards: C.cards.map((c) => {
    const card = { id: c.id, location: c.loc, round: c.round, text: c.text };
    if (c.cipher) card.shows = "cipher";
    if (c.opt) card.requires_role = c.opt;
    return card;
  }),
  sealed: C.envelopes.map((e) => {
    const s = { location: e.loc, instructions: e.how };
    if (sealedByLoc[e.loc]) s.unlocked_by_puzzle = sealedByLoc[e.loc];
    else s.unlocked_by_round = 2;
    return s;
  }),
};

// ---------- puzzles ----------
// The originals checked answers with JavaScript functions; these are the
// same rules written as data the server can check.
const answers = {
  safe: { type: "digits", accept: ["103198", "10311998"] },
  page: { type: "word", accept: ["SIGHT"] },
  route: { type: "route", start: "great", sequence: C.puzzles[2].route },
};
// For the GM's answer sheet (from the old GM page).
const explanations = {
  safe: "103198: 10/31/98, the day The Hollowpine Girl was first published (card C10). Edgar's note says \"Safe = the night it all began.\"",
  page: "SIGHT. Shift each letter back 3 (three ravens in the painting): \"The werewolf counted the gold twice and kept it once. He never let his bag out of his sight.\"",
  route: "Kitchen, Mudroom, Back Porch, Study: out the back door and in through the French doors, so nobody in the Great Room or Hallway saw.",
};
const puzzles = C.puzzles.map((p) => {
  const puzzle = { id: p.id, title: p.title, prompt: p.prompt, hint: p.hint, unlocks: sealedLocation(p.id), answer: answers[p.id], explanation: explanations[p.id] };
  if (p.id === "page") puzzle.shows = "cipher";
  if (p.route) puzzle.shows = "map";
  return puzzle;
});
function sealedLocation(puzzleId) {
  return Object.keys(sealedByLoc).find((loc) => sealedByLoc[loc] === puzzleId);
}

// ---------- props (physical objects) ----------
const props = C.cards
  .filter((c) => c.item)
  .map((c) => ({
    id: c.id === "C24" ? "manuscript" : "photo-1998",
    name: c.id === "C24" ? "The Manuscript" : "The 1998 Photo",
    description: c.text.replace(/^[A-Z0-9 ']+\. /, ""), // drop the card's "THE MANUSCRIPT. " heading
    placed_at: c.loc,
    clue: c.id,
  }));

// ---------- solution ----------
const solution = {
  killer,
  summary: "Marcus Reed killed Edgar at 10:50 with the Golden Raven award, then faked an 11:20 time of death with Edgar's sound-effects recorder and a re-wound watch.",
  key_proof: [
    "Recorder timer set for 11:20 (C01)",
    "Watch crown pulled out (B6)",
    "Last text sent 10:44, everything from 10:55 unread (B3)",
    "Ruth saw him leave at 10:42",
    "Paw prints porch to study (C20, C04)",
    "Only one cigarette in the ashtray (C19)",
    "Muddy paw feet in his bag (C29)",
    "Award with gray fur (C25)",
    "Audit letter (C26)",
  ],
  reveal: C.reveal,
  timeline: C.roles[killer].timeline.map(([time, place, text]) => ({ time, place, text })),
};

// ---------- extras ----------
const extras = {
  cipher: C.cipher,
  seance: C.seance,
  map: {
    rooms: ROOMS.map((r) => {
      const room = { id: r.id, name: r.n, x: r.x, y: r.y, w: r.w, h: r.h, lines: r.l, info: r.info };
      if (r.k) room.kind = r.k === "out" ? "outdoor" : "upstairs";
      if (r.seal) room.sealed = r.seal;
      if (r.center) room.center = true;
      return room;
    }),
    doors: DOORS,
    walls: [[180, 116, 556, 336]],
    labels: [
      { x: 235, y: 102, text: "Back door" },
      { x: 650, y: 102, text: "French doors" },
    ],
  },
};

// ---------- manifest ----------
const coreCount = roles.filter((r) => r.core).length;
const manifest = {
  slug: "hollowpine",
  title: C.title,
  premise: C.premise,
  rules: C.rules,
  min_players: coreCount,
  max_players: roles.length,
  victim: { name: "Edgar Thorne", text: "The victim. Famous horror novelist, host of the party." },
  map: "public/map.svg",
  body_viewer: "public/body.js",
  run_of_show: [
    "Briefing as the Deputy: read the premise, show the map and the body (10 min)",
    "Players reread their sheets (10 min)",
    "Search round 1, free-for-all (20 min)",
    "Discussion (15 min)",
    "Puzzle round (20 min)",
    "Start Round 2 from your dashboard, open Ruth's Cabin, search round 2 and discussion (25 min)",
    "Final statements, open voting, reveal, then secret goals and prizes (15 min)",
  ],
  files: {
    roles: "roles.json",
    clues: "clues.json",
    puzzles: "puzzles.json",
    props: "props.json",
    solution: "solution.json",
    extras: "extras.json",
  },
};

write("case.json", manifest);
write("roles.json", roles);
write("clues.json", clues);
write("puzzles.json", puzzles);
write("props.json", props);
write("solution.json", solution);
write("extras.json", extras);
console.log(`wrote ${out}: ${roles.length} roles, ${clues.body.length + clues.cards.length} clues, ${puzzles.length} puzzles, ${props.length} props`);
