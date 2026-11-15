// A player's phone on game night: their sheet, the case, the body, puzzles,
// and voting. Everything here comes from /p/<token>/state/, which only holds
// what this player may see.
(function () {
  var cfg = JSON.parse(document.getElementById("cfg").textContent);
  var $ = function (s) { return document.querySelector(s); };
  var S = null, current = "me", activeHot = null, body3d = null, routes = {};

  /* ---------- tabs ---------- */
  function show(view) {
    current = view;
    document.querySelectorAll("section.view").forEach(function (s) { s.hidden = s.id !== "v-" + view; });
    document.querySelectorAll("nav.tabs button").forEach(function (b) { b.classList.toggle("active", b.dataset.v === view); });
    if (view === "body") initBody();
    window.scrollTo(0, 0);
  }
  document.querySelectorAll("nav.tabs button").forEach(function (b) { b.onclick = function () { show(b.dataset.v); }; });
  document.addEventListener("click", function (e) {
    var go = e.target.closest("[data-go]");
    if (go) show(go.dataset.go);
  });

  /* ---------- case map ---------- */
  if (cfg.map) {
    $("#mapMain").innerHTML = drawMap(cfg.map, "m-");
    $("#mapMain").addEventListener("click", function (e) {
      var id = e.target.getAttribute && e.target.getAttribute("data-room");
      if (!id) return;
      var r = cfg.map.rooms.filter(function (x) { return x.id === id; })[0];
      document.querySelectorAll("#mapMain .room").forEach(function (el) { el.classList.toggle("sel", el.getAttribute("data-room") === id); });
      $("#roomInfo").innerHTML = "<b>" + esc(r.name) + "</b><p class='small' style='margin:4px 0 0'>" + esc(r.info || "") + "</p>";
    });
  }

  /* ---------- state ---------- */
  var playing = function () { return S && ["live", "voting", "revealed"].indexOf(S.status) >= 0; };

  function render(state) {
    var before = S;
    S = state;
    var labels = { invited: "Before the party", live: "Round " + S.round, voting: "Voting", revealed: "Solved" };
    $("#badge").textContent = labels[S.status] || "";
    $("#badge").classList.toggle("hot", S.status !== "invited");
    if (S.status === "archived") { location.reload(); return; }

    var ending = S.status === "voting" || S.status === "revealed";
    $("#tab-vote").hidden = !ending;
    $("#tab-vote span").textContent = S.status === "revealed" ? "Reveal" : "Vote";
    $("#tab-vote .dot").hidden = !(S.status === "voting" && !S.voting.your_vote) && S.status !== "revealed";
    if (!ending && current === "vote") show("me");

    var banner = "";
    if (S.status === "voting" && !S.voting.your_vote) banner = '<div class="card notice row" style="justify-content:space-between"><b>Voting is open.</b><button class="btn small primary" data-go="vote">Vote now</button></div>';
    if (S.status === "revealed") banner = '<div class="card notice row" style="justify-content:space-between"><b>The killer has been revealed.</b><button class="btn small primary" data-go="vote">See the reveal</button></div>';
    if (before && before.round !== S.round && S.status === "live") banner = '<div class="card notice row" style="justify-content:space-between"><b>Round ' + S.round + ' has started. New clues on the body.</b><button class="btn small" data-go="body">Look</button></div>';
    $("#banner").innerHTML = banner;

    renderBody();
    renderPuzzles();
    renderVote();
  }

  /* ---------- body ---------- */
  function renderBody() {
    if (!playing()) { $("#bodyLive").hidden = true; $("#bodyLocked").hidden = false; return; }
    $("#bodyLive").hidden = false; $("#bodyLocked").hidden = true;
    $("#hotChips").innerHTML = S.body.map(function (h) {
      return '<button class="chip ' + (h.round > 1 ? "r2" : "") + (activeHot === h.id ? " on" : "") + '" data-hot="' + esc(h.id) + '"><span class="dot"></span>' + esc(h.label) + "</button>";
    }).join("");
    if (body3d) body3d.show(S.body);
    else if (current === "body") initBody(); // the game started while this tab was open
  }
  $("#hotChips").addEventListener("click", function (e) {
    var b = e.target.closest("[data-hot]");
    if (b) selectHot(b.dataset.hot);
  });
  function selectHot(id) {
    var h = S.body.filter(function (x) { return x.id === id; })[0];
    if (!h) return;
    activeHot = id;
    $("#hotDetail").innerHTML = '<div style="font-weight:700;margin-bottom:4px">' + esc(h.label) + (h.round > 1 ? ' <span class="badge hot" style="font-size:11px;padding:2px 8px">Round ' + h.round + "</span>" : "") + "</div><div>" + esc(h.text) + "</div>";
    renderBody();
    if (body3d) body3d.highlight(id);
  }
  var bodyLoading = false;
  function initBody() {
    if (!cfg.bodyViewer || body3d || bodyLoading || !playing()) { if (body3d) body3d.resize(); return; }
    bodyLoading = true;
    var wrap = $("#bodyWrap");
    wrap.hidden = false;
    var fail = function () { wrap.querySelector(".hint").textContent = "3D view couldn't load. Use the buttons below."; };
    load("https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js", function () {
      load(cfg.bodyViewer, function () {
        try { body3d = window.CaseBody(wrap, selectHot); body3d.show(S.body); } catch (e) { fail(); }
      }, fail);
    }, fail);
  }
  function load(src, ok, bad) {
    var s = document.createElement("script");
    s.src = src; s.onload = ok; s.onerror = bad;
    document.head.appendChild(s);
  }

  /* ---------- puzzles ---------- */
  // Each puzzle's card is drawn once, then redrawn only when it gets solved,
  // so typing isn't wiped out by updates from other phones.
  var drawn = {};
  function renderPuzzles() {
    var box = $("#puzzleList");
    if (!playing()) { box.innerHTML = ""; drawn = {}; $("#puzzlesLocked").hidden = false; return; }
    $("#puzzlesLocked").hidden = true;
    S.puzzles.forEach(function (p, i) {
      var key = p.id + ":" + p.solved;
      if (drawn[p.id] === key) return;
      drawn[p.id] = key;
      var card = document.getElementById("pz-" + p.id);
      if (!card) { card = document.createElement("div"); card.className = "card"; card.id = "pz-" + p.id; box.appendChild(card); }
      card.innerHTML = puzzleHTML(p, i);
      if (p.type === "route" && !p.solved) paintRoute(p);
    });
  }
  function puzzleHTML(p, i) {
    var h = '<h3 style="margin-top:0">Puzzle ' + (i + 1) + " · " + esc(p.title) + "</h3><p>" + esc(p.prompt) + "</p>";
    if (p.shows_text) h += '<div class="cipher">' + esc(p.shows_text) + "</div>";
    if (p.solved) {
      return h + '<div class="unlock"><strong>Solved' + (p.solved_by ? " by " + esc(p.solved_by) : "") + "!</strong>" +
        (p.unlocks ? " Show the GM, then open the envelope: <b>" + esc(p.unlocks) + "</b>" : "") + "</div>";
    }
    if (p.type === "route") {
      h += '<div class="map" data-route="' + esc(p.id) + '">' + (cfg.map ? drawMap(cfg.map, "r-" + p.id + "-") : "") + "</div>" +
        '<div class="pathchips" id="path-' + esc(p.id) + '"></div>' +
        '<div class="row"><button class="btn small" data-undo="' + esc(p.id) + '">Undo</button><button class="btn small" data-clear="' + esc(p.id) + '">Clear</button>' +
        '<button class="btn small primary" data-check="' + esc(p.id) + '">Check route</button></div>';
    } else {
      h += '<div class="row"><input class="answer" id="in-' + esc(p.id) + '" autocomplete="off" ' +
        (p.type === "digits" ? 'inputmode="numeric" placeholder="Code"' : 'placeholder="Answer"') + '>' +
        '<button class="btn primary" data-check="' + esc(p.id) + '">Check</button></div>';
    }
    h += '<div class="msg" id="msg-' + esc(p.id) + '"></div>';
    if (p.hint) h += '<details class="hint"><summary>Hint</summary><p class="small" style="margin-top:6px">' + esc(p.hint) + "</p></details>";
    return h;
  }
  function paintRoute(p) {
    var path = routes[p.id] || (routes[p.id] = []);
    document.querySelectorAll('[data-route="' + p.id + '"] .room').forEach(function (el) {
      var id = el.getAttribute("data-room");
      el.classList.toggle("start", id === p.start);
      el.classList.toggle("path", path.indexOf(id) >= 0);
    });
    var name = function (id) { var r = cfg.map.rooms.filter(function (x) { return x.id === id; })[0]; return r ? r.name : id; };
    $("#path-" + p.id).innerHTML = [name(p.start) + " (start)"].concat(path.map(name)).map(function (n) { return "<span>" + esc(n) + "</span>"; }).join(" → ");
  }
  $("#puzzleList").addEventListener("click", function (e) {
    var t = e.target;
    var room = t.getAttribute && t.getAttribute("data-room");
    var routeBox = t.closest("[data-route]");
    var puzzle = function (id) { return S.puzzles.filter(function (p) { return p.id === id; })[0]; };
    if (room && routeBox) {
      var p = puzzle(routeBox.dataset.route);
      if (room !== p.start) { routes[p.id].push(room); paintRoute(p); }
      return;
    }
    var b = t.closest("button");
    if (!b) return;
    if (b.dataset.undo) { routes[b.dataset.undo].pop(); paintRoute(puzzle(b.dataset.undo)); }
    if (b.dataset.clear) { routes[b.dataset.clear] = []; paintRoute(puzzle(b.dataset.clear)); }
    if (b.dataset.check) check(puzzle(b.dataset.check), b);
  });
  $("#puzzleList").addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target.id && e.target.id.indexOf("in-") === 0) {
      var id = e.target.id.slice(3);
      check(S.puzzles.filter(function (p) { return p.id === id; })[0], null);
    }
  });
  function check(p, button) {
    var answer = p.type === "route" ? routes[p.id] : $("#in-" + p.id).value;
    if (button) button.disabled = true;
    postJSON(cfg.solveUrl, { puzzle: p.id, answer: answer }).then(function (r) {
      if (button) button.disabled = false;
      var m = $("#msg-" + p.id);
      if (!m) return;
      m.className = "msg " + (r.correct ? "ok" : "bad");
      m.textContent = r.message;
      if (r.correct) live.refresh();
    });
  }

  /* ---------- vote and reveal ---------- */
  var voteKey = "";
  function renderVote() {
    var box = $("#voteBox");
    if (S.status === "voting") {
      var v = S.voting;
      var key = "v:" + v.your_vote + ":" + v.votes_in;
      if (key === voteKey) return;
      voteKey = key;
      if (v.your_vote) {
        var who = v.suspects.filter(function (s) { return s.role_id === v.your_vote; })[0];
        box.innerHTML = '<div class="card"><h3>Your vote</h3><p>You voted for <b>' + esc(who ? who.name : v.your_vote) + "</b>.</p>" +
          '<p class="small muted">' + v.votes_in + " of " + v.players + " votes in. The GM reveals the killer when everyone has voted.</p></div>";
        return;
      }
      box.innerHTML = '<div class="card"><h3>Who killed them?</h3><p class="small muted">Tap a suspect, then confirm. Your vote is secret and can\'t be changed.</p>' +
        v.suspects.map(function (s) {
          return '<button class="suspect" data-suspect="' + esc(s.role_id) + '"><span><b>' + esc(s.name) + '</b><br><span class="small muted">' + esc(s.player) + "</span></span></button>";
        }).join("") +
        '<button class="btn primary" id="castVote" disabled>Confirm vote</button><div class="msg bad" id="voteMsg"></div></div>';
      return;
    }
    if (S.status === "revealed") {
      if (voteKey === "revealed:" + JSON.stringify(S.reveal.goals)) return;
      voteKey = "revealed:" + JSON.stringify(S.reveal.goals);
      var r = S.reveal;
      var verdict = { yes: "You caught the killer!", tie: "A tie! The killer slipped away.", no: "The killer got away." }[r.caught];
      var max = Math.max.apply(null, r.tally.map(function (t) { return t.votes; }).concat([1]));
      box.innerHTML = '<div class="card"><div class="verdict">' + esc(verdict) + "</div>" +
        (r.killer ? "<p>The killer was <b>" + esc(r.killer.name) + "</b>, played by " + esc(r.killer.player) + ".</p>" : "") +
        (r.summary ? '<p class="small">' + esc(r.summary) + "</p>" : "") + "</div>" +
        '<div class="card tally"><h3>The votes</h3>' + r.tally.map(function (t) {
          return '<div><div class="row" style="justify-content:space-between"><span><b>' + esc(t.name) + '</b> <span class="small muted">' + esc(t.player) + "</span></span><span>" + t.votes + "</span></div>" +
            '<div class="bar" style="width:' + Math.max(2, (t.votes / max) * 100) + '%;margin-bottom:10px"></div></div>';
        }).join("") + "</div>" +
        '<div class="card"><h3>What really happened</h3><blockquote>' + esc(r.text) + "</blockquote></div>" +
        (r.timeline.length ? '<div class="card"><h3>The true timeline</h3><ul class="tl">' + r.timeline.map(function (row) {
          return '<li><span class="t">' + esc(row.time) + '</span><span class="w">' + esc(row.place) + '</span><span class="d">' + esc(row.text) + "</span></li>";
        }).join("") + "</ul></div>" : "") +
        '<div class="card"><h3>Secret goals</h3><div class="kv">' + r.goals.map(function (g) {
          var met = g.met === true ? '<span class="met yes">Met</span>' : g.met === false ? '<span class="met no">Missed</span>' : "";
          return "<div><b>" + esc(g.name) + ' <span class="small muted">' + esc(g.player) + "</span> " + met + '</b><span class="small">' + esc(g.goal) + "</span></div>";
        }).join("") + "</div></div>";
      return;
    }
    voteKey = "";
    box.innerHTML = "";
  }
  var picked = null;
  $("#voteBox").addEventListener("click", function (e) {
    var s = e.target.closest("[data-suspect]");
    if (s) {
      picked = s.dataset.suspect;
      document.querySelectorAll("[data-suspect]").forEach(function (x) { x.classList.toggle("on", x === s); });
      $("#castVote").disabled = false;
      return;
    }
    if (e.target.id === "castVote" && picked) {
      e.target.disabled = true;
      postJSON(cfg.voteUrl, { suspect: picked }).then(function (r) {
        if (r.error) { $("#voteMsg").textContent = r.error; e.target.disabled = false; return; }
        live.refresh();
      });
    }
  });

  /* ---------- secret goal + sheet tabs ---------- */
  var goal = $("#goalBox");
  if (goal) {
    $("#goalShow").onclick = function () { goal.classList.add("open"); };
    $("#goalHide").onclick = function () { goal.classList.remove("open"); };
    var subtabs = document.querySelectorAll("#subtabs button");
    subtabs.forEach(function (b) {
      b.onclick = function () {
        subtabs.forEach(function (x) { x.classList.toggle("on", x === b); });
        document.querySelectorAll(".st").forEach(function (s) { s.hidden = s.id !== "st-" + b.dataset.st; });
      };
    });
  }

  var live = Live(cfg.stateUrl, cfg.wsPath, render);
  if (location.hash && document.getElementById("v-" + location.hash.slice(1))) show(location.hash.slice(1));
})();
