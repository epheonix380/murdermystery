// Draws a case's floor plan from extras.json's map data, with rooms you can tap.
window.drawMap = function (map, prefix) {
  var rooms = map.rooms, doors = map.doors || [];
  var minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
  rooms.forEach(function (r) {
    minX = Math.min(minX, r.x); minY = Math.min(minY, r.y);
    maxX = Math.max(maxX, r.x + r.w); maxY = Math.max(maxY, r.y + r.h);
  });
  var vb = [minX - 8, minY - 8, maxX - minX + 16, maxY - minY + 16];
  var s = '<div class="mapscroll"><svg viewBox="' + vb.join(" ") + '" role="img" aria-label="Floor plan">';
  rooms.forEach(function (r) {
    var k = r.kind === "outdoor" ? "out" : r.kind === "upstairs" ? "up" : "";
    s += '<rect class="room ' + k + '" data-room="' + esc(r.id) + '" id="' + prefix + esc(r.id) + '" x="' + r.x + '" y="' + r.y +
      '" width="' + r.w + '" height="' + r.h + '" rx="' + (k === "out" ? 8 : 0) + '"/>';
  });
  (map.walls || []).forEach(function (w) { s += '<rect class="wall" x="' + w[0] + '" y="' + w[1] + '" width="' + w[2] + '" height="' + w[3] + '"/>'; });
  doors.forEach(function (d) { s += '<line class="door" x1="' + d[0] + '" y1="' + d[1] + '" x2="' + d[2] + '" y2="' + d[3] + '"/>'; });
  rooms.forEach(function (r) {
    if (r.center) { s += '<text class="nm" x="' + (r.x + r.w / 2) + '" y="' + (r.y + r.h / 2 + 5) + '" text-anchor="middle">' + esc(r.name) + '</text>'; return; }
    var y = r.y + 22;
    s += '<text class="nm" x="' + (r.x + 12) + '" y="' + y + '">' + esc(r.name) + '</text>';
    (r.lines || []).forEach(function (line) { y += 18; s += '<text class="q" x="' + (r.x + 12) + '" y="' + y + '">' + esc(line) + '</text>'; });
    if (r.sealed) { y += 18; s += '<circle class="seal" cx="' + (r.x + 16) + '" cy="' + (y - 4) + '" r="5"/><text class="q" x="' + (r.x + 26) + '" y="' + y + '">' + esc(r.sealed) + '</text>'; }
  });
  (map.labels || []).forEach(function (l) { s += '<text class="q" x="' + l.x + '" y="' + l.y + '" text-anchor="middle">' + esc(l.text) + "</text>"; });
  s += '</svg></div><div class="swipe">Swipe sideways to see the whole map</div>';
  return s;
};
