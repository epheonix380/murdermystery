// Hollowpine's 3D body scene, ported from the original site.
//
// A case's body viewer is a script that defines
//   window.CaseBody(wrap, onPick) -> { show(hotspots), highlight(id), resize() }
// The page loads three.js first. `show` gets the hotspots the player can see
// right now ([{id, round}]); `onPick(id)` is called when one is tapped.
(function () {
  // Where each hotspot sits on the body.
  var POS = {
    B1: [0.01, 0.33, -0.46], B2: [-0.43, 0.2, -0.57], B3: [0.62, 0.09, 0.12], B4: [0.36, 0.1, 0.62],
    B5: [-0.36, 0.19, -0.44], B6: [-0.5, 0.24, -0.62], B7: [-0.62, 0.09, 0.42], B8: [0.14, 0.3, -0.12],
  };

  window.CaseBody = function (wrap, onPick) {
    var T = THREE;
    var renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    wrap.appendChild(renderer.domElement);
    var scene = new T.Scene();
    scene.fog = new T.Fog(0x0d0b10, 4, 9);
    var camera = new T.PerspectiveCamera(45, 1, 0.05, 50);
    var target = new T.Vector3(0, 0.1, 0.35);
    var theta = 0.9, phi = 0.95, radius = 2.6;

    scene.add(new T.HemisphereLight(0xc9bfff, 0x2a1a10, 0.75));
    var key = new T.DirectionalLight(0xffe2c0, 0.85); key.position.set(2, 4, 2); scene.add(key);
    var lamp = new T.PointLight(0xff8a3d, 0.7, 6); lamp.position.set(-1.2, 1.2, -1); scene.add(lamp);

    var mat = function (c, o) { var m = new T.MeshStandardMaterial({ color: c, roughness: 0.8, metalness: 0 }); if (o) Object.keys(o).forEach(function (k) { m[k] = o[k]; }); return m; };
    var add = function (geo, m, x, y, z) { var me = new T.Mesh(geo, m); me.position.set(x, y, z); scene.add(me); return me; };

    // floor + rug
    var floor = add(new T.PlaneGeometry(8, 8), mat(0x3a281e), 0, 0, 0); floor.rotation.x = -Math.PI / 2;
    var rug = add(new T.PlaneGeometry(2.2, 2.8), mat(0x4a2230), 0, 0.002, 0.35); rug.rotation.x = -Math.PI / 2;
    var rugB = add(new T.PlaneGeometry(2.0, 2.6), mat(0x5a2a3a), 0, 0.003, 0.35); rugB.rotation.x = -Math.PI / 2;

    // blood pool
    var blood = mat(0x4a0710, { roughness: 0.25, metalness: 0.1 });
    var b1 = add(new T.CircleGeometry(0.26, 32), blood, 0.02, 0.006, -0.5); b1.rotation.x = -Math.PI / 2;
    var b2 = add(new T.CircleGeometry(0.15, 24), blood, -0.16, 0.007, -0.66); b2.rotation.x = -Math.PI / 2;

    // body (face down), head toward -z
    var jacket = mat(0x6b1f2a), pants = mat(0x34343e), skin = mat(0xc99a7a), hair = mat(0x55525a), shoe = mat(0x111111);
    add(new T.BoxGeometry(0.44, 0.22, 0.62), jacket, 0, 0.12, -0.02);
    add(new T.BoxGeometry(0.38, 0.19, 0.3), pants, 0, 0.11, 0.42);
    var limb = function (a, b, r1, r2, m) {
      var A = new T.Vector3(a[0], a[1], a[2]), B = new T.Vector3(b[0], b[1], b[2]);
      var me = new T.Mesh(new T.CylinderGeometry(r1, r2, A.distanceTo(B), 14), m);
      me.position.copy(A).add(B).multiplyScalar(0.5);
      me.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), B.clone().sub(A).normalize());
      scene.add(me); return me;
    };
    limb([-0.11, 0.09, 0.52], [-0.14, 0.07, 1.36], 0.085, 0.065, pants);
    limb([0.11, 0.09, 0.52], [0.2, 0.07, 1.33], 0.085, 0.065, pants);
    add(new T.BoxGeometry(0.11, 0.09, 0.2), shoe, -0.15, 0.06, 1.46);
    add(new T.BoxGeometry(0.11, 0.09, 0.2), shoe, 0.21, 0.06, 1.43);
    // left arm reaching forward, right arm by side
    limb([-0.25, 0.13, -0.24], [-0.46, 0.06, -0.62], 0.06, 0.05, jacket);
    limb([0.25, 0.13, -0.2], [0.42, 0.06, 0.24], 0.06, 0.05, jacket);
    add(new T.SphereGeometry(0.055, 16, 12), skin, -0.5, 0.05, -0.68);
    add(new T.SphereGeometry(0.055, 16, 12), skin, 0.44, 0.05, 0.31);
    add(new T.SphereGeometry(0.03, 10, 8), mat(0x8f8a94), 0.27, 0.16, -0.18).scale.set(1.4, 0.6, 1);
    // head
    add(new T.CylinderGeometry(0.05, 0.06, 0.1, 12), skin, 0, 0.13, -0.36).rotation.x = Math.PI / 2;
    add(new T.SphereGeometry(0.125, 24, 18), skin, 0, 0.13, -0.47);
    add(new T.SphereGeometry(0.13, 24, 18, 0, Math.PI * 2, 0, Math.PI / 2), hair, 0, 0.14, -0.48).rotation.x = -0.35;
    var wound = add(new T.CircleGeometry(0.045, 16), mat(0x5a0a12, { roughness: 0.3 }), 0.01, 0.272, -0.46); wound.rotation.x = -Math.PI / 2;
    // smashed watch on left wrist
    add(new T.CylinderGeometry(0.035, 0.035, 0.02, 20), mat(0xc9a24a, { metalness: 0.7, roughness: 0.35 }), -0.43, 0.11, -0.57);
    var face = add(new T.CircleGeometry(0.028, 20), mat(0xd9d9e0, { roughness: 0.1 }), -0.43, 0.121, -0.57); face.rotation.x = -Math.PI / 2;
    // fur on left cuff
    var fur = mat(0x8a8a8a);
    [[-0.38, 0.11, -0.5], [-0.36, 0.1, -0.47], [-0.4, 0.12, -0.46]].forEach(function (p) { add(new T.SphereGeometry(0.018, 8, 6), fur, p[0], p[1], p[2]); });
    // phone near right hand
    add(new T.BoxGeometry(0.075, 0.012, 0.15), mat(0x16161c), 0.62, 0.007, 0.12);
    var scr = add(new T.PlaneGeometry(0.065, 0.13), new T.MeshBasicMaterial({ color: 0x6a8cff }), 0.62, 0.0141, 0.12); scr.rotation.x = -Math.PI / 2;
    // wallet
    add(new T.BoxGeometry(0.1, 0.022, 0.12), mat(0x5a3a20), 0.36, 0.012, 0.62).rotation.y = 0.5;
    // coroner note (paper)
    add(new T.BoxGeometry(0.16, 0.004, 0.22), mat(0xe8e2d0), -0.62, 0.004, 0.42).rotation.y = -0.3;

    // hotspots, created as the server reveals them
    var hots = {}, colliders = [], sel = null;
    function show(list) {
      Object.keys(hots).forEach(function (id) { hots[id].m.visible = hots[id].ring.visible = false; });
      colliders = [];
      list.forEach(function (h) {
        var p = POS[h.id];
        if (!p) return;
        if (!hots[h.id]) {
          var col = h.round > 1 ? 0x9a7bff : 0xf07a2e;
          var m = new T.Mesh(new T.SphereGeometry(0.035, 16, 12), new T.MeshBasicMaterial({ color: col }));
          var ring = new T.Mesh(new T.SphereGeometry(0.055, 16, 12), new T.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.28, depthWrite: false }));
          var hit = new T.Mesh(new T.SphereGeometry(0.11, 10, 8), new T.MeshBasicMaterial({ visible: false }));
          [m, ring, hit].forEach(function (o) { o.position.set(p[0], p[1], p[2]); scene.add(o); });
          hit.userData.id = h.id;
          hots[h.id] = { m: m, ring: ring, hit: hit, i: Object.keys(hots).length };
        }
        hots[h.id].m.visible = hots[h.id].ring.visible = true;
        colliders.push(hots[h.id].hit);
      });
    }

    function resize() {
      var w = wrap.clientWidth, h = wrap.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      radius = Math.max(radius, w < 420 ? 2.6 : 2.2);
      camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", resize);

    // controls: drag to orbit, pinch / wheel to zoom, tap to pick
    var el = renderer.domElement, pts = {}, moved = 0, lastPinch = 0;
    el.addEventListener("pointerdown", function (e) { el.setPointerCapture(e.pointerId); pts[e.pointerId] = { x: e.clientX, y: e.clientY }; moved = 0; lastPinch = 0; });
    el.addEventListener("pointermove", function (e) {
      var p = pts[e.pointerId]; if (!p) return;
      var ids = Object.keys(pts);
      if (ids.length === 2) {
        var a = pts[ids[0]], b = pts[ids[1]];
        p.x = e.clientX; p.y = e.clientY;
        var d = Math.hypot(a.x - b.x, a.y - b.y);
        if (lastPinch) radius = Math.min(5, Math.max(1.1, radius * lastPinch / d));
        lastPinch = d; moved += 10; return;
      }
      var dx = e.clientX - p.x, dy = e.clientY - p.y;
      moved += Math.abs(dx) + Math.abs(dy);
      theta -= dx * 0.008; phi = Math.min(1.45, Math.max(0.25, phi - dy * 0.006));
      p.x = e.clientX; p.y = e.clientY;
    });
    el.addEventListener("pointerup", function (e) {
      var wasTap = moved < 8 && Object.keys(pts).length === 1;
      delete pts[e.pointerId];
      if (!wasTap) return;
      var r = el.getBoundingClientRect();
      var v = new T.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      var ray = new T.Raycaster(); ray.setFromCamera(v, camera);
      var hit = ray.intersectObjects(colliders)[0];
      if (hit) onPick(hit.object.userData.id);
    });
    el.addEventListener("pointercancel", function (e) { delete pts[e.pointerId]; });
    el.addEventListener("wheel", function (e) { e.preventDefault(); radius = Math.min(5, Math.max(1.1, radius * (1 + e.deltaY * 0.001))); }, { passive: false });

    var t0 = performance.now();
    function loop(now) {
      requestAnimationFrame(loop);
      if (document.hidden || !wrap.offsetParent) return; // not on screen
      var t = (now - t0) / 1000;
      camera.position.set(target.x + radius * Math.sin(phi) * Math.sin(theta), target.y + radius * Math.cos(phi), target.z + radius * Math.sin(phi) * Math.cos(theta));
      camera.lookAt(target);
      Object.keys(hots).forEach(function (id) {
        var o = hots[id], s = 1 + 0.25 * Math.sin(t * 3 + o.i), big = id === sel ? 1.7 : 1;
        o.ring.scale.setScalar(s * big); o.m.scale.setScalar(big);
      });
      lamp.intensity = 0.6 + 0.08 * Math.sin(t * 7) + 0.05 * Math.sin(t * 13);
      renderer.render(scene, camera);
    }
    resize();
    requestAnimationFrame(loop);
    return { show: show, highlight: function (id) { sel = id; }, resize: resize };
  };
})();
