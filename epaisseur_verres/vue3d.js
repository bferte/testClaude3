/*
 * Vue 3D des deux verres taillés (et du cercle de la monture) avec three.js.
 * Repère en mm : X vers la droite de l'observateur, Y vers le haut, Z vers l'observateur
 * (la face avant des verres regarde vers +Z). Rotation à la souris / au doigt, zoom molette / pincement.
 */
(function (racine) {
  "use strict";
  const E = racine.Epaisseur;

  function creer(canvas) {
    const THREE = racine.THREE;
    if (!THREE) throw new Error("La bibliothèque 3D n'a pas pu être chargée (connexion internet requise).");
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, racine.devicePixelRatio || 1));
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(28, 2, 1, 2000);
    scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const l1 = new THREE.DirectionalLight(0xffffff, 0.75); l1.position.set(-60, 80, 120); scene.add(l1);
    const l2 = new THREE.DirectionalLight(0xffffff, 0.35); l2.position.set(80, -40, -100); scene.add(l2);
    const pivot = new THREE.Group();
    scene.add(pivot);

    const etat = { rx: 0.35, ry: -0.6, dist: 300, largeur: 150, hauteur: 60 };
    function cadrer() {
      const w = canvas.clientWidth, h = canvas.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      const t = 2 * Math.tan((camera.fov * Math.PI) / 360);
      const ajust = Math.max(etat.largeur / (t * camera.aspect), etat.hauteur / t);
      camera.position.set(0, 0, ajust * 1.4 * (etat.dist / 300));
      camera.lookAt(0, 0, 0);
      pivot.rotation.set(etat.rx, etat.ry, 0);
      renderer.render(scene, camera);
    }

    // Interaction : glisser pour tourner, molette ou pincement pour zoomer.
    const pointeurs = new Map();
    let ecart0 = 0, dist0 = 300;
    canvas.style.touchAction = "none";
    canvas.addEventListener("pointerdown", (e) => {
      canvas.setPointerCapture(e.pointerId);
      pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 2) {
        const [a, b] = [...pointeurs.values()];
        ecart0 = Math.hypot(a[0] - b[0], a[1] - b[1]); dist0 = etat.dist;
      }
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!pointeurs.has(e.pointerId)) return;
      const [x0, y0] = pointeurs.get(e.pointerId);
      pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 1) {
        etat.ry += (e.clientX - x0) * 0.01;
        etat.rx = Math.max(-1.5, Math.min(1.5, etat.rx + (e.clientY - y0) * 0.01));
      } else if (pointeurs.size === 2) {
        const [a, b] = [...pointeurs.values()];
        const ecart = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (ecart0 > 0) etat.dist = Math.max(60, Math.min(600, (dist0 * ecart0) / ecart));
      }
      cadrer();
    });
    const fin = (e) => pointeurs.delete(e.pointerId);
    canvas.addEventListener("pointerup", fin);
    canvas.addEventListener("pointercancel", fin);
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      etat.dist = Math.max(60, Math.min(600, etat.dist * (1 + Math.sign(e.deltaY) * 0.1)));
      cadrer();
    }, { passive: false });

    function vider() {
      while (pivot.children.length) {
        const o = pivot.children.pop();
        o.traverse((x) => { x.geometry?.dispose(); x.material?.dispose(); });
      }
    }

    /**
     * res : résultat du calcul ({ od, og, p: {A, B, DBL}, cercl }).
     * opts : { rampe(t) -> "rgb(...)", cadre (couleur CSS), exag, voirCercle }
     */
    function maj(res, opts) {
      vider();
      const exag = opts.exag || 1;
      const { A, DBL } = res.p;
      const tMin = Math.min(res.od.centre, res.og.centre, res.od.bordMin.e, res.og.bordMin.e);
      const tMax = Math.max(res.od.bordMax.e, res.og.bordMax.e, res.od.centre, res.og.centre);
      const couleur = (t) => new THREE.Color(opts.rampe((t - tMin) / Math.max(0.01, tMax - tMin)));
      for (const r of [res.od, res.og]) {
        const xc = ((A + DBL) / 2) * (r.oeil === "OD" ? -1 : 1);
        const sens = r.oeil === "OD" ? 1 : -1; // u (nasal > 0) -> X monde
        pivot.add(verre(THREE, r, xc, sens, exag, couleur));
        if (res.cercl && opts.voirCercle) pivot.add(cercle(THREE, r, res.cercl, xc, sens, exag, opts.cadre));
      }
      // Recentrage en profondeur sur le milieu des verres.
      const boite = new THREE.Box3().setFromObject(pivot);
      const centreZ = (boite.min.z + boite.max.z) / 2;
      pivot.children.forEach((o) => { o.position.z -= centreZ; });
      etat.largeur = 2 * A + DBL + 10;
      etat.hauteur = res.p.B + 16;
      cadrer();
    }

    function vue(nom) {
      const vues = { face: [0, 0], profil: [0, -Math.PI / 2], dessus: [Math.PI / 2, 0], troisQuarts: [0.35, -0.6], arriere: [0, Math.PI] };
      [etat.rx, etat.ry] = vues[nom] || vues.troisQuarts;
      cadrer();
    }

    return { maj, vue, redimensionner: cadrer };
  }

  // Sous-échantillonne le contour pour un maillage léger.
  function echantillon(contour, n) {
    const pas = contour.length / n;
    return Array.from({ length: n }, (_, i) => contour[Math.floor(i * pas)]);
  }

  function verre(THREE, r, xc, sens, exag, couleur) {
    const N = 144, R = 22;
    const contour = echantillon(r._contour, N);
    const pos = [], col = [], idx = [];
    const ajout = (u, v, avant) => {
      const [X, Y] = r._versOC([u, v]);
      const f = r._geo.faces(X, Y);
      const t = r.centre + f.arriere - f.avant;
      const zAvant = -f.avant;
      pos.push(xc + sens * u, v, avant ? zAvant : zAvant - exag * t);
      const c = couleur(t);
      col.push(c.r, c.g, c.b);
      return pos.length / 3 - 1;
    };
    for (const face of [true, false]) {
      const centre = ajout(0, 0, face);
      const anneaux = [];
      for (let j = 1; j <= R; j++) anneaux.push(contour.map(([u, v]) => ajout((u * j) / R, (v * j) / R, face)));
      for (let i = 0; i < N; i++) {
        const i2 = (i + 1) % N;
        tri(idx, face, centre, anneaux[0][i], anneaux[0][i2]);
        for (let j = 1; j < R; j++) {
          const a = anneaux[j - 1][i], b = anneaux[j - 1][i2], c = anneaux[j][i], d = anneaux[j][i2];
          tri(idx, face, a, c, d); tri(idx, face, a, d, b);
        }
      }
    }
    // Tranche : quadrilatères entre le dernier anneau avant et arrière.
    const debutArriere = 1 + N * R;
    for (let i = 0; i < N; i++) {
      const i2 = (i + 1) % N;
      const a = 1 + N * (R - 1) + i, b = 1 + N * (R - 1) + i2;
      const c = debutArriere + 1 + N * (R - 1) + i, d = debutArriere + 1 + N * (R - 1) + i2;
      tri(idx, true, a, c, d); tri(idx, true, a, d, b);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    const m = new THREE.MeshPhongMaterial({
      vertexColors: true, transparent: true, opacity: 0.82, shininess: 90,
      specular: 0x333333, side: THREE.DoubleSide, depthWrite: false,
    });
    const mesh = new THREE.Mesh(g, m);
    mesh.renderOrder = 2;
    return mesh;
  }

  function tri(idx, direct, a, b, c) {
    if (direct) idx.push(a, b, c); else idx.push(a, c, b);
  }

  // Cercle de la monture : tube à section rectangulaire centré sur le biseau du verre.
  function cercle(THREE, r, cercl, xc, sens, exag, couleurCadre) {
    const N = 144, larg = 2.2, recouvrement = 0.6;
    const contour = echantillon(r._contour, N);
    const D = cercl.profondeur;
    const pos = [], idx = [];
    contour.forEach(([u, v], i) => {
      const [up, vp] = contour[(i + N - 1) % N], [un, vn] = contour[(i + 1) % N];
      let nx = vn - vp, ny = -(un - up); // normale sortante (contour parcouru dans le sens trigo)
      const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      const [X, Y] = r._versOC([u, v]);
      const f = r._geo.faces(X, Y);
      const e = r.centre + f.arriere - f.avant;
      const b = E.positionBiseau(e, cercl);
      const zB = -f.avant - exag * b;
      const zAv = zB + (exag * D) / 2, zAr = zB - (exag * D) / 2;
      for (const [d, z] of [[-recouvrement, zAv], [larg, zAv], [larg, zAr], [-recouvrement, zAr]])
        pos.push(xc + sens * (u + nx * d), v + ny * d, z);
    });
    for (let i = 0; i < N; i++) {
      const i2 = (i + 1) % N;
      for (let k = 0; k < 4; k++) {
        const k2 = (k + 1) % 4;
        const a = i * 4 + k, b = i * 4 + k2, c = i2 * 4 + k, d = i2 * 4 + k2;
        idx.push(a, c, d, a, d, b);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    const m = new THREE.MeshPhongMaterial({ color: new THREE.Color(couleurCadre), shininess: 40, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(g, m);
    mesh.renderOrder = 1;
    return mesh;
  }

  racine.Vue3D = { creer };
})(typeof self !== "undefined" ? self : this);
