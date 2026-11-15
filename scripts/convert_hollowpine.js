// One-off conversion of the original static site (legacy/data.js and the map
// data in legacy/index.html) into the case-file format in cases/hollowpine/.
//
//   node scripts/convert_hollowpine.js
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
const puzzles = C.puzzles.map((p) => {
  const puzzle = { id: p.id, title: p.title, prompt: p.prompt, hint: p.hint, unlocks: sealedLocation(p.id), answer: answers[p.id] };
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
    description: c.text,
    placed_at: c.loc,
    clue: c.id,
  }));

// ---------- solution ----------
const solution = {
  killer,
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
fs.mkdirSync(path.join(out, "public"), { recursive: true });
fs.writeFileSync(path.join(out, "public", "map.svg"), mapSVG());

// A standalone version of the site's floor plan, with colours inlined so it
// renders anywhere (the case browser, a link, a printout).
function mapSVG() {
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fill = { out: "#2c2636", up: "#1d1924" };
  let s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 56 760 456" width="760" height="456" role="img" aria-label="Floor plan of Hollowpine Lodge" font-family="Inter, system-ui, sans-serif">\n';
  s += '<rect x="0" y="56" width="760" height="456" fill="#121016"/>\n';
  ROOMS.forEach((r) => {
    const dash = r.k === "up" ? ' stroke-dasharray="6 4"' : "";
    s += `<rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" rx="${r.k === "out" ? 8 : 0}" fill="${fill[r.k] || "#1d1924"}" stroke="#5b5168"${dash}/>\n`;
  });
  s += '<rect x="180" y="116" width="556" height="336" fill="none" stroke="#a89cb8" stroke-width="3"/>\n';
  DOORS.forEach((d) => {
    s += `<line x1="${d[0]}" y1="${d[1]}" x2="${d[2]}" y2="${d[3]}" stroke="#f07a2e" stroke-width="5" stroke-linecap="round"/>\n`;
  });
  ROOMS.forEach((r) => {
    if (r.center) {
      s += `<text x="${r.x + r.w / 2}" y="${r.y + r.h / 2 + 5}" text-anchor="middle" fill="#ece6f2" font-size="14" font-weight="600">${esc(r.n)}</text>\n`;
      return;
    }
    let y = r.y + 22;
    s += `<text x="${r.x + 12}" y="${y}" fill="#ece6f2" font-size="14" font-weight="600">${esc(r.n)}</text>\n`;
    r.l.forEach((line) => {
      y += 18;
      s += `<text x="${r.x + 12}" y="${y}" fill="#a89cb8" font-size="12">${esc(line)}</text>\n`;
    });
    if (r.seal) {
      y += 18;
      s += `<circle cx="${r.x + 16}" cy="${y - 4}" r="5" fill="#9a7bff"/><text x="${r.x + 26}" y="${y}" fill="#a89cb8" font-size="12">${esc(r.seal)}</text>\n`;
    }
  });
  s += '<text x="235" y="102" text-anchor="middle" fill="#a89cb8" font-size="12">Back door</text>\n';
  s += '<text x="650" y="102" text-anchor="middle" fill="#a89cb8" font-size="12">French doors</text>\n';
  s += "</svg>\n";
  return s;
}

console.log(`wrote ${out}: ${roles.length} roles, ${clues.body.length + clues.cards.length} clues, ${puzzles.length} puzzles, ${props.length} props`);
