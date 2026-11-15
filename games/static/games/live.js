// Keeps a page's game state fresh. The server pings a WebSocket when the
// game changes; the page then fetches its own state over HTTP. If the socket
// is down, it polls instead.
window.Live = function (stateUrl, wsPath, onState) {
  var ws = null, backoff = 1000, pollTimer = null, inflight = false, again = false;

  function refresh() {
    if (inflight) { again = true; return; }
    inflight = true;
    fetch(stateUrl, { credentials: "same-origin", cache: "no-store" })
      .then(function (r) {
        if (r.status === 404) { location.reload(); throw new Error("game over"); } // ended: show the ended page
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then(onState)
      .catch(function () {})
      .then(function () { inflight = false; if (again) { again = false; refresh(); } });
  }

  function connect() {
    if (!window.WebSocket) return;
    ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + wsPath);
    ws.onopen = function () { backoff = 1000; refresh(); };
    ws.onmessage = function () { refresh(); };
    ws.onclose = function (e) {
      ws = null;
      if (e.code === 4404) return; // game gone
      setTimeout(connect, backoff);
      backoff = Math.min(backoff * 2, 30000);
    };
  }

  // Fallback: poll while the socket is down, and catch up when the phone wakes.
  pollTimer = setInterval(function () { if (!ws || ws.readyState !== 1) refresh(); }, 15000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) refresh(); });

  refresh();
  connect();
  return { refresh: refresh };
};

window.esc = function (s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
};

window.postJSON = function (url, data) {
  var csrf = document.querySelector('meta[name="csrf-token"]').content;
  return fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
    body: JSON.stringify(data || {}),
  }).then(function (r) { return r.json(); });
};
