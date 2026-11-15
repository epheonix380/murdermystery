// The GM's live controls: start, rounds, voting, reveal, and who has done what.
(function () {
  var cfg = JSON.parse(document.getElementById("cfg").textContent);
  var box = document.getElementById("live");
  var S = null;

  var CONFIRM = {
    open_voting: "Open voting? Players' phones will ask them to vote.",
    reveal: "Reveal the killer to everyone?",
  };

  function ago(iso) {
    if (!iso) return "not yet";
    var m = Math.round((Date.now() - Date.parse(iso)) / 60000);
    return m < 1 ? "just now" : m < 60 ? m + " min ago" : m < 1440 ? Math.round(m / 60) + " h ago" : Math.round(m / 1440) + " d ago";
  }

  function controls() {
    var b = function (action, label, cls) { return '<button class="btn ' + (cls || "") + '" data-action="' + action + '">' + label + "</button>"; };
    switch (S.status) {
      case "draft": return "<p>Set up the cast first.</p>";
      case "invited":
        return "<p>Players can read their characters. Start when everyone has arrived: their phones unlock the body and puzzles.</p>" + b("start", "Start the game", "primary");
      case "live":
        var more = S.round < S.rounds;
        return "<p><b>Round " + S.round + " of " + S.rounds + "</b>. " + (more ? "Start the next round when the search is done." : "Last round. Open voting when final statements are done.") + "</p>" +
          '<div class="row">' + (more ? b("next_round", "Start round " + (S.round + 1), "primary") : "") + b("open_voting", "Open voting", more ? "" : "primary") + "</div>";
      case "voting":
        return "<p><b>Voting is open.</b> " + S.votes_in + " of " + S.players.length + " have voted. You see who has voted, not how.</p>" +
          '<div class="row">' + b("reveal", "Reveal the killer", "primary") + b("close_voting", "Back to the game") + "</div>";
      case "revealed":
        var r = S.reveal, verdict = { yes: "The group caught the killer.", tie: "A tie: the killer slipped away.", no: "The killer got away." }[r.caught];
        return '<p><b>' + esc(verdict) + "</b></p>" + r.tally.map(function (t) {
          return '<div class="row" style="justify-content:space-between"><span>' + esc(t.name) + ' <span class="small muted">' + esc(t.player) + "</span></span><b>" + t.votes + "</b></div>";
        }).join("") + '<p class="small muted" style="margin-top:8px">Players can see the reveal on their phones. Mark secret goals below; their phones update.</p>';
    }
    return "";
  }

  function render(state) {
    S = state;
    if (S.status === "archived") { location.href = "/"; return; }
    var badge = document.getElementById("statusBadge");
    if (badge) badge.textContent = { draft: "Draft", invited: "Before the party", live: "Round " + S.round, voting: "Voting", revealed: "Revealed" }[S.status];
    var ending = S.status === "voting" || S.status === "revealed";
    var playing = ["live", "voting", "revealed"].indexOf(S.status) >= 0;

    var h = '<div class="card"><h3>Run the game</h3>' + controls() + '<div class="msg bad" id="actionMsg"></div></div>';

    if (playing && S.sealed.length) {
      h += '<div class="card"><h3>Sealed envelopes</h3><table class="list">' + S.sealed.map(function (s) {
        return "<tr><td><b>" + esc(s.location) + '</b><div class="small muted">' + esc(s.instructions) + '</div></td><td style="text-align:right"><span class="pill ' + (s.open ? "open\">Open it" : "shut\">Sealed") + "</span></td></tr>";
      }).join("") + "</table></div>";
    }
    if (playing && S.puzzles.length) {
      h += '<div class="card"><h3>Puzzles</h3><table class="list">' + S.puzzles.map(function (p) {
        return "<tr><td>" + esc(p.title) + '</td><td class="' + (p.solved ? "" : "muted") + '">' + (p.solved ? "Solved by " + esc(p.solved_by || "someone") : "Not yet") + "</td></tr>";
      }).join("") + "</table></div>";
    }

    h += '<div class="card"><h3>Players</h3><table class="list"><tr><th>Player</th><th>Character</th><th>' + (ending ? (S.status === "voting" ? "Voted" : "Goal") : "Opened link") + "</th></tr>" +
      S.players.map(function (p) {
        var last;
        if (S.status === "voting") last = p.voted ? '<span class="met yes">Voted</span>' : '<span class="muted">Not yet</span>';
        else if (S.status === "revealed") last = goalButtons(p);
        else last = '<span class="muted">' + ago(p.seen) + "</span>";
        return "<tr><td>" + esc(p.name) + "</td><td>" + esc(p.character) + "</td><td>" + last + "</td></tr>";
      }).join("") + "</table>" +
      (S.status === "voting" ? '<p class="small muted" style="margin-top:8px">After the reveal, you can mark who met their secret goal.</p>' : "") + "</div>";
    box.innerHTML = h;
  }

  function goalButtons(p) {
    var on = function (v) { return p.goal_met === v ? " on" : ""; };
    return '<span class="seg"><button class="' + on(true).trim() + '" data-goal="' + p.id + '" data-met="true">Met</button>' +
      '<button class="' + on(false).trim() + '" data-goal="' + p.id + '" data-met="false">Missed</button></span>';
  }

  box.addEventListener("click", function (e) {
    var a = e.target.closest("[data-action]");
    if (a) {
      var action = a.dataset.action;
      if (CONFIRM[action] && !confirm(CONFIRM[action])) return;
      a.disabled = true;
      postJSON(cfg.actionUrl, { action: action }).then(function (r) {
        if (r.error) { document.getElementById("actionMsg").textContent = r.error; a.disabled = false; }
        live.refresh();
      });
      return;
    }
    var g = e.target.closest("[data-goal]");
    if (g) {
      var p = S.players.filter(function (x) { return String(x.id) === g.dataset.goal; })[0];
      var met = g.dataset.met === "true";
      postJSON(cfg.goalUrl, { player: p.id, met: p.goal_met === met ? null : met }).then(function () { live.refresh(); });
    }
  });

  var live = Live(cfg.stateUrl, cfg.wsPath, render);
})();
