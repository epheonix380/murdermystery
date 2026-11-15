// End-to-end: one GM and four players run a whole game in real browsers,
// with updates arriving over WebSockets (no page reloads).
//
//   .venv/bin/python manage.py runserver 8765   # in another terminal
//   node e2e/full_game.js [base-url] [screenshot-dir]
//
// Without internet access to the CDNs, set THREE_JS=<path to three.min.js
// 0.128.0> to serve it locally; Google Fonts are then skipped too.
const { chromium } = require("playwright");
const assert = require("assert");

const BASE = process.argv[2] || "http://127.0.0.1:8765";
const SHOTS = process.argv[3] || null;
const NAMES = ["Sam", "Alex", "Jo", "Kim"];

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const phone = async () => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    if (process.env.THREE_JS) {
      await ctx.route("https://cdn.jsdelivr.net/npm/three@0.128.0/**", (r) => r.fulfill({ path: process.env.THREE_JS, contentType: "text/javascript" }));
      await ctx.route("https://fonts.googleapis.com/**", (r) => r.fulfill({ body: "", contentType: "text/css" }));
    }
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    return page;
  };
  const shot = async (page, name) => { if (SHOTS) await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: true }); };

  // GM sets up
  const gm = await phone();
  await gm.goto(BASE + "/");
  await gm.click("text=Host this case");
  const date = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  await gm.fill("#id_party_date", date);
  await gm.selectOption("#id_player_count", "4");
  await gm.click("text=Create game");
  for (const [i, n] of NAMES.entries()) await gm.fill(`input[name=name_${i}]`, n);
  await gm.selectOption("select[name=role_0]", "WOLF");
  await gm.click("text=Save cast");
  const links = await gm.$$eval(".link-row", (rows) => rows.map((r) => [r.querySelector("b").textContent, r.querySelector(".url").textContent.trim()]));
  assert.strictEqual(links.length, 4);

  const players = {};
  for (const [name, url] of links) {
    players[name] = await phone();
    await players[name].goto(url);
  }
  const alex = players.Alex;
  await alex.click("nav.tabs button[data-v=body]");
  await alex.waitForSelector("#bodyLocked:not([hidden])");

  // Start: phones unlock without reloading
  await gm.goto(BASE + "/host/");
  await gm.waitForSelector("[data-action=start]");
  await shot(gm, "e2e-1-gm-before");
  await gm.click("[data-action=start]");
  await alex.waitForSelector("#hotChips .chip");
  assert.strictEqual(await alex.$$eval("#hotChips .chip", (c) => c.length), 5);
  await alex.click("#hotChips .chip >> nth=1");
  assert.match(await alex.textContent("#hotDetail"), /11:20/);
  await alex.waitForSelector("#bodyWrap canvas", { timeout: 15000 }).catch(() => errors.push("3D body did not load"));
  await shot(alex, "e2e-2-body");

  // Puzzles: Jo solves, Alex sees it
  const jo = players.Jo;
  await jo.click("nav.tabs button[data-v=puzzles]");
  await jo.fill("#in-safe", "1234");
  await jo.click("#pz-safe [data-check]");
  await jo.waitForSelector("#msg-safe.bad");
  await jo.fill("#in-safe", "10/31/98");
  await jo.click("#pz-safe [data-check]");
  await jo.waitForSelector("#pz-safe .unlock");
  await alex.click("nav.tabs button[data-v=puzzles]");
  await alex.waitForSelector("#pz-safe .unlock");
  assert.match(await alex.textContent("#pz-safe .unlock"), /Solved by Jo/);

  // Route puzzle by tapping rooms
  for (const room of ["kitchen", "mudroom", "porch", "study"]) await alex.click(`#r-route-${room}`, { force: true });
  await alex.click("#pz-route [data-check]");
  await alex.waitForSelector("#pz-route .unlock");
  await alex.fill("#in-page", "sight");
  await alex.press("#in-page", "Enter");
  await alex.waitForSelector("#pz-page .unlock");
  await shot(alex, "e2e-3-puzzles");
  await gm.waitForFunction(() => document.querySelectorAll("#live .pill.open").length === 3);

  // Round 2
  await gm.click("[data-action=next_round]");
  await alex.waitForFunction(() => document.getElementById("badge").textContent === "Round 2");
  await alex.click("nav.tabs button[data-v=body]");
  await alex.waitForFunction(() => document.querySelectorAll("#hotChips .chip").length === 8);
  await gm.waitForFunction(() => document.querySelectorAll("#live .pill.open").length === 4);
  await shot(gm, "e2e-4-gm-round2");

  // Voting
  gm.once("dialog", (d) => d.accept());
  await gm.click("[data-action=open_voting]");
  for (const [name, suspect] of [["Alex", "WOLF"], ["Jo", "WOLF"], ["Kim", "WOLF"], ["Sam", "BREW"]]) {
    const p = players[name];
    await p.waitForSelector("#tab-vote:not([hidden])");
    await p.click("#tab-vote");
    await p.click(`[data-suspect=${suspect}]`);
    if (name === "Alex") await shot(p, "e2e-5-vote");
    await p.click("#castVote");
    await p.waitForSelector("text=You voted for");
  }
  await gm.waitForFunction(() => /4 of 4 have voted/.test(document.getElementById("live").textContent));

  // Reveal
  gm.once("dialog", (d) => d.accept());
  await gm.click("[data-action=reveal]");
  await alex.waitForSelector(".verdict");
  assert.strictEqual(await alex.textContent(".verdict"), "You caught the killer!");
  await gm.waitForSelector("[data-goal]");
  await gm.click("[data-goal] >> nth=2"); // Alex met their goal
  await alex.waitForSelector(".met.yes");
  await shot(alex, "e2e-6-reveal");
  await shot(gm, "e2e-7-gm-revealed");

  // Ending the game sends open player pages to the "ended" page
  gm.once("dialog", (d) => d.accept());
  await gm.click("text=End game");
  await gm.waitForSelector("text=Pick a mystery");
  await alex.waitForSelector("text=This game has ended");

  assert.deepStrictEqual(errors.filter((e) => !/404/.test(e)), []);
  console.log("full game passed");
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
