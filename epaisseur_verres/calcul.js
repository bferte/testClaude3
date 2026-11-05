/*
 * Moteur de calcul d'épaisseur de verres unifocaux taillés.
 *
 * Modèle : verre ménisque, face avant sphérique (ou asphérique : conique),
 * face arrière torique (biconique) portant la correction, épaisseur centre
 * ajustée pour respecter une épaisseur minimale au centre ET au bord sur la
 * forme réelle de la monture (surfaçage « optimisé forme »).
 *
 * Repère « vue de face » (observateur face au porteur) : X vers la droite de
 * l'observateur, Y vers le haut, angles d'axe TABO (0° à droite, sens trigo).
 * Pour l'OD le côté nasal est donc en +X, pour l'OG en -X.
 *
 * Utilisable dans le navigateur (window.Epaisseur) et sous Node (require).
 */
(function (racine, fabrique) {
  if (typeof module === "object" && module.exports) module.exports = fabrique();
  else racine.Epaisseur = fabrique();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Valeurs usuelles du marché ; épaisseur centre mini des verres négatifs modifiable.
  const MATERIAUX = [
    { id: "1.50", nom: "Organique 1.50", n: 1.5, abbe: 58, densite: 1.32, tcMin: 2.0 },
    { id: "1.53", nom: "Trivex 1.53", n: 1.53, abbe: 45, densite: 1.11, tcMin: 1.5 },
    { id: "1.59", nom: "Polycarbonate 1.59", n: 1.586, abbe: 30, densite: 1.2, tcMin: 1.2 },
    { id: "1.60", nom: "Organique 1.60", n: 1.6, abbe: 42, densite: 1.3, tcMin: 1.5 },
    { id: "1.67", nom: "Organique 1.67", n: 1.67, abbe: 32, densite: 1.35, tcMin: 1.3 },
    { id: "1.74", nom: "Organique 1.74", n: 1.74, abbe: 33, densite: 1.46, tcMin: 1.2 },
  ];

  // Épaisseur minimale au bord selon le montage (rainure nylor, perçage).
  const MONTAGES = {
    cercle: { nom: "Cerclé", eMin: 1.0 },
    nylor: { nom: "Nylor (rainuré)", eMin: 1.8 },
    perce: { nom: "Percé", eMin: 2.0 },
  };

  // Profondeur usuelle d'un cercle (épaisseur de la monture d'avant en arrière).
  const CERCLAGES = {
    plastique: { nom: "Plastique (acétate)", profondeur: 4.5 },
    metal: { nom: "Métal", profondeur: 2.5 },
  };

  const FORMES = {
    ronde: "Ronde / ovale",
    rectangle: "Rectangle",
    carree: "Carrée arrondie",
    pantos: "Pantos",
    aviateur: "Aviateur",
    papillon: "Papillon (cat-eye)",
  };

  const N_REF_BASE = 1.53;

  // Diamètres de palets usuels (mm), pour le surfaçage sans précalibrage.
  const DIAMETRES_PALET = [55, 60, 65, 70, 75, 80];

  /** Plus petit palet usuel qui couvre la forme décentrée. */
  function diametrePaletStandard(diametreMini) {
    return DIAMETRES_PALET.find((d) => d >= diametreMini) || Math.ceil(diametreMini / 5) * 5;
  } // les bases sont exprimées à l'indice d'outil 1.53

  function materiau(id) {
    const m = MATERIAUX.find((x) => x.id === String(id));
    if (!m) throw new Error("Matériau inconnu : " + id);
    return m;
  }

  // ------------------------------------------------------------------ Formes
  /**
   * Contour d'un verre droit, repère local centré sur le centre boxing,
   * u > 0 côté nasal, v > 0 vers le haut. Calibré exactement sur A x B.
   */
  function contourForme(forme, A, B, nPts = 360) {
    const pts = [];
    for (let i = 0; i < nPts; i++) {
      const t = (2 * Math.PI * i) / nPts;
      const c = Math.cos(t), s = Math.sin(t);
      let p = 2;
      if (forme === "rectangle") p = 5;
      else if (forme === "carree") p = 3.4;
      else if (forme === "pantos") p = s > 0 ? 3.6 : 2.1;
      else if (forme === "aviateur") p = 2.6;
      else if (forme === "papillon") p = 3;
      let u = Math.sign(c) * Math.pow(Math.abs(c), 2 / p);
      let v = Math.sign(s) * Math.pow(Math.abs(s), 2 / p);
      if (forme === "aviateur" && v < 0) v *= 1 + 0.45 * (-u); // goutte : plus bas côté temporal
      if (forme === "aviateur" && v > 0) v *= 1 + 0.1 * u;
      if (forme === "papillon" && v > 0) v *= 1 + 0.5 * (-u); // relevé côté temporal
      if (forme === "papillon" && v < 0) v *= 1 - 0.15 * (-u);
      pts.push([u, v]);
    }
    return calerBoxing(pts, A, B);
  }

  /** Recentre et met à l'échelle un contour pour qu'il occupe exactement A x B. */
  function calerBoxing(pts, A, B) {
    const { minU, maxU, minV, maxV } = boite(pts);
    const cu = (minU + maxU) / 2, cv = (minV + maxV) / 2;
    const ku = A ? A / (maxU - minU) : 1, kv = B ? B / (maxV - minV) : 1;
    return pts.map(([u, v]) => [(u - cu) * ku, (v - cv) * kv]);
  }

  function boite(pts) {
    let minU = Infinity, maxU = -Infinity, minV = Infinity, maxV = -Infinity;
    for (const [u, v] of pts) {
      if (u < minU) minU = u;
      if (u > maxU) maxU = u;
      if (v < minV) minV = v;
      if (v > maxV) maxV = v;
    }
    return { minU, maxU, minV, maxV, A: maxU - minU, B: maxV - minV };
  }

  /**
   * Lit un tracé de monture au format OMA / VCA (fichier .oma, .vca, .dat) :
   * TRCFMT=1;N;E;R;F puis R=r1;r2;... (rayons en 1/100 mm, angles réguliers,
   * 0° à 3 h vu de face, sens trigonométrique). Renvoie le contour du verre
   * droit en repère local (nasal > 0), A, B et DBL s'ils sont présents.
   */
  function lireOMA(texte) {
    const lignes = String(texte).split(/\r?\n/);
    const traces = [];
    let courant = null, dbl = null;
    for (const brut of lignes) {
      const ligne = brut.trim();
      const eg = ligne.indexOf("=");
      if (eg < 0) continue;
      const cle = ligne.slice(0, eg).trim().toUpperCase();
      const val = ligne.slice(eg + 1).trim();
      if (cle === "TRCFMT") {
        const f = val.split(";");
        courant = { n: parseInt(f[1], 10), cote: (f[3] || "R").toUpperCase(), r: [] };
        traces.push(courant);
      } else if (cle === "R" && courant) {
        for (const x of val.split(";")) if (x.trim() !== "") courant.r.push(parseFloat(x) / 100);
      } else if (cle === "DBL") {
        dbl = parseFloat(val.split(";")[0]);
      }
    }
    const trace = traces.find((t) => t.cote === "R" || t.cote === "B") || traces[0];
    if (!trace || trace.r.length < 16) throw new Error("Aucun tracé R= exploitable dans le fichier.");
    const n = trace.r.length;
    let pts = trace.r.map((r, i) => {
      const a = (2 * Math.PI * i) / n;
      return [r * Math.cos(a), r * Math.sin(a)];
    });
    if (trace.cote === "L") pts = pts.map(([u, v]) => [-u, v]); // ramené en verre droit
    const b = boite(pts);
    return { contour: calerBoxing(pts, 0, 0), A: b.A, B: b.B, DBL: dbl };
  }

  // ------------------------------------------------------------------ Optique
  /** Base conseillée (D à 1.53) d'après la règle de Vogel, aplanie en asphérique. */
  function baseConseillee(sph, cyl, geometrie) {
    const es = sph + cyl / 2;
    let base = es >= 0 ? es + 6 : es / 2 + 6;
    if (geometrie === "aspherique") base -= es >= 0 ? 2 : 1;
    return Math.min(10, Math.max(0.5, Math.round(base * 4) / 4));
  }

  // Constante conique de la face avant asphérique : aplatit vers le bord pour un
  // positif, cambre vers le bord pour un négatif (ordre de grandeur des designs du marché).
  function coniqueAvant(es, geometrie) {
    if (geometrie !== "aspherique") return 0;
    return es >= 0 ? -1.2 : 2;
  }

  /** Flèche d'une surface de révolution conique (mm), c en 1/mm. */
  function flecheConique(c, r2, k) {
    const d = 1 - (1 + k) * c * c * r2;
    if (d <= 0) return NaN;
    return (c * r2) / (1 + Math.sqrt(d));
  }

  /** Flèche d'une surface biconique (torique approchée), cx, cy en 1/mm. */
  function flecheBiconique(cx, cy, x, y) {
    const d = 1 - cx * cx * x * x - cy * cy * y * y;
    if (d <= 0) return NaN;
    return (cx * x * x + cy * y * y) / (1 + Math.sqrt(d));
  }

  /**
   * Prépare la géométrie d'un verre : renvoie une fonction g(X, Y) donnant
   * l'écart d'épaisseur par rapport au centre optique (t = tc + g).
   */
  function geometrieVerre({ sph, cyl, axe, n, base, conique, tc }) {
    const c1 = base / ((N_REF_BASE - 1) * 1000); // courbure avant (1/mm)
    const F1 = (n - 1) * 1000 * c1; // puissance de la face avant à l'indice du verre
    const F1eff = F1 / (1 - (tc / 1000 / n) * F1); // contribution en puissance frontale arrière
    const cAxe = -(sph - F1eff) / ((n - 1) * 1000); // courbure arrière (concave > 0)
    const cPerp = -(sph + cyl - F1eff) / ((n - 1) * 1000);
    const th = (axe * Math.PI) / 180, co = Math.cos(th), si = Math.sin(th);
    return {
      F1,
      c1,
      g(X, Y) {
        const x = X * co + Y * si, y = -X * si + Y * co;
        return flecheBiconique(cAxe, cPerp, x, y) - flecheConique(c1, X * X + Y * Y, conique);
      },
      faces(X, Y) {
        const x = X * co + Y * si, y = -X * si + Y * co;
        return { avant: flecheConique(c1, X * X + Y * Y, conique), arriere: flecheBiconique(cAxe, cPerp, x, y) };
      },
    };
  }

  function dansPolygone(x, y, poly) {
    let dedans = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xi, yi] = poly[i], [xj, yj] = poly[j];
      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dedans = !dedans;
    }
    return dedans;
  }

  function zone(u, v, A, B) {
    // Libellé lisible d'un point du contour (u > 0 nasal).
    const a = (Math.atan2(v / B, u / A) * 180) / Math.PI;
    if (a > -22.5 && a <= 22.5) return "nasal";
    if (a > 22.5 && a <= 67.5) return "haut nasal";
    if (a > 67.5 && a <= 112.5) return "haut";
    if (a > 112.5 && a <= 157.5) return "haut temporal";
    if (a > 157.5 || a <= -157.5) return "temporal";
    if (a > -157.5 && a <= -112.5) return "bas temporal";
    if (a > -112.5 && a <= -67.5) return "bas";
    return "bas nasal";
  }

  /**
   * Calcule un verre taillé.
   * p = { oeil: 'OD'|'OG', sph, cyl, axe, materiau (id), geometrie: 'spherique'|'aspherique',
   *       base (facultatif, D à 1.53), tcMin (facultatif), eMin,
   *       contour (verre droit, repère local), A, B, DBL, demiEcart, hauteur }
   */
  function calculerVerre(p) {
    const mat = materiau(p.materiau);
    const sph = +p.sph || 0, cyl = +p.cyl || 0, axe = +p.axe || 0;
    const es = sph + cyl / 2;
    const geometrie = p.geometrie || "spherique";
    const base = p.base > 0 ? +p.base : baseConseillee(sph, cyl, geometrie);
    const conique = coniqueAvant(es, geometrie);
    const tcMin = p.tcMin > 0 ? +p.tcMin : mat.tcMin;
    const eMin = p.eMin > 0 ? +p.eMin : 1.0;
    const sens = p.oeil === "OG" ? -1 : 1; // nasal -> X vue de face

    // Centre optique dans le repère boxing (nasal > 0, haut > 0).
    const ocU = (p.A + p.DBL) / 2 - p.demiEcart;
    const ocV = p.hauteur - p.B / 2;
    const versOC = ([u, v]) => [sens * (u - ocU), v - ocV];

    // Points du contour vus du centre optique + diamètre minimal du palet.
    const rel = p.contour.map(versOC);
    let rMax = 0;
    for (const [X, Y] of rel) rMax = Math.max(rMax, Math.hypot(X, Y));
    const diametreMini = 2 * rMax + 2; // marge de taillage 1 mm

    // Précalibrage (par défaut) : le bord mini est garanti sur la forme taillée.
    // Sans précalibrage : il doit aussi l'être sur tout le pourtour du palet rond,
    // centré sur le centre optique, ce qui épaissit le centre des verres positifs.
    const precalibrage = p.precalibrage !== false;
    // Diamètre commandé : imposé, ou plus petit diamètre usuel couvrant la forme décentrée.
    const diametreImpose = p.diametrePalet > 0;
    const diametrePalet = diametreImpose ? +p.diametrePalet : diametrePaletStandard(diametreMini);
    const eMinPalet = p.eMinPalet > 0 ? +p.eMinPalet : 0.8;
    const cerclePalet = precalibrage ? [] : Array.from({ length: 72 }, (_, i) => {
      const a = (2 * Math.PI * i) / 72;
      return [(diametrePalet / 2) * Math.cos(a), (diametrePalet / 2) * Math.sin(a)];
    });

    let tc = tcMin, geo, gs, bordPalet = null;
    for (let it = 0; it < 4; it++) {
      geo = geometrieVerre({ sph, cyl, axe, n: mat.n, base, conique, tc });
      gs = rel.map(([X, Y]) => geo.g(X, Y));
      if (gs.some((x) => !Number.isFinite(x)))
        throw new Error("Courbure impossible pour cette taille de verre : diminuer la base ou le calibre.");
      tc = Math.max(tcMin, eMin - Math.min(...gs));
      if (!precalibrage) {
        const gp = cerclePalet.map(([X, Y]) => geo.g(X, Y));
        if (gp.some((x) => !Number.isFinite(x)))
          throw new Error(`Courbure impossible sur un palet de Ø${diametrePalet} mm : diminuer la base ou le diamètre.`);
        const gpMin = Math.min(...gp);
        tc = Math.max(tc, eMinPalet - gpMin);
        bordPalet = { min: tc + gpMin, max: tc + Math.max(...gp) };
      }
    }
    const bords = gs.map((g) => tc + g);
    let iMax = 0, iMin = 0;
    bords.forEach((e, i) => {
      if (e > bords[iMax]) iMax = i;
      if (e < bords[iMin]) iMin = i;
    });

    // Volume par intégration sur une grille de 0,5 mm à l'intérieur de la forme.
    const pas = 0.5;
    const b = boite(p.contour);
    let volume = 0;
    for (let u = b.minU + pas / 2; u < b.maxU; u += pas)
      for (let v = b.minV + pas / 2; v < b.maxV; v += pas)
        if (dansPolygone(u, v, p.contour)) {
          const [X, Y] = versOC([u, v]);
          volume += (tc + geo.g(X, Y)) * pas * pas;
        }

    const pt = (i) => ({ e: bords[i], zone: zone(p.contour[i][0], p.contour[i][1], p.A, p.B) });
    return {
      oeil: p.oeil || "OD",
      materiau: mat,
      geometrie,
      base,
      conique,
      equivalentSpherique: es,
      centre: tc,
      bordMax: pt(iMax),
      bordMin: pt(iMin),
      bordMoyen: bords.reduce((a, x) => a + x, 0) / bords.length,
      bords,
      poids: (volume / 1000) * mat.densite,
      volume,
      decentrement: { horizontal: ocU, vertical: ocV },
      diametreMini,
      palet: {
        precalibrage, diametre: diametrePalet, impose: diametreImpose, eMin: eMinPalet, bord: bordPalet,
        tropPetit: diametrePalet < diametreMini, // le palet ne couvre pas la forme décentrée
      },
      calibre: { A: p.A, B: p.B },
      _geo: geo,
      _versOC: versOC,
      _contour: p.contour,
    };
  }

  /**
   * Coupe horizontale passant par le centre optique : profils des faces avant et
   * arrière (en mm) le long de la largeur de la forme, pour le schéma.
   */
  function coupe(res, sens = "h", nPts = 80) {
    // sens 'h' : droite horizontale v = ocV (s = u, temporal -> nasal)
    // sens 'v' : droite verticale u = ocU (s = v, bas -> haut)
    const c = res._contour;
    const h = sens !== "v";
    const fixe = h ? res.decentrement.vertical : res.decentrement.horizontal;
    const [iF, iS] = h ? [1, 0] : [0, 1];
    const xs = [];
    for (let i = 0, j = c.length - 1; i < c.length; j = i++) {
      const fi = c[i][iF], fj = c[j][iF], si = c[i][iS], sj = c[j][iS];
      if (fi > fixe !== fj > fixe) xs.push(si + ((fixe - fi) * (sj - si)) / (fj - fi));
    }
    if (xs.length < 2) return [];
    const s0 = Math.min(...xs), s1 = Math.max(...xs);
    const out = [];
    for (let k = 0; k <= nPts; k++) {
      const sc = s0 + ((s1 - s0) * k) / nPts;
      const [X, Y] = res._versOC(h ? [sc, fixe] : [fixe, sc]);
      const f = res._geo.faces(X, Y);
      out.push({ s: sc, u: h ? sc : fixe, avant: f.avant, arriere: res.centre + f.arriere });
    }
    return out;
  }

  /** Coupe horizontale par le centre optique (compatibilité). */
  function coupeHorizontale(res, nPts = 80) {
    return coupe(res, "h", nPts);
  }

  /**
   * Bords du verre aux quatre extrémités des coupes passant par le centre optique
   * (haut, bas, nasal, temporal), avec le débord dans le cercle si opts est fourni.
   */
  function quatreBords(res, opts) {
    const h = coupe(res, "h", 2), v = coupe(res, "v", 2);
    const bord = (nom, p) => {
      const e = p.arriere - p.avant;
      const o = { nom, e };
      if (opts) {
        const D = Math.max(0, +opts.profondeur || 0), b = positionBiseau(e, opts);
        Object.assign(o, { biseau: b, profondeur: D, devant: b - D / 2, derriere: e - b - D / 2 });
      }
      return o;
    };
    if (!h.length || !v.length) return [];
    return [bord("haut", v[v.length - 1]), bord("bas", v[0]), bord("nasal", h[h.length - 1]), bord("temporal", h[0])];
  }

  /**
   * Position du sommet du biseau, en mm depuis la face avant du bord du verre.
   * opts = { biseauMode: 'pct' | 'mm', biseau } : pourcentage de l'épaisseur du bord
   * (33 = un tiers avant / deux tiers arrière) ou distance fixe depuis la face avant.
   */
  function positionBiseau(e, opts) {
    const v = Math.max(0, +opts.biseau || 0);
    return opts.biseauMode === "mm" ? Math.min(v, e) : (e * Math.min(v, 100)) / 100;
  }

  /**
   * Débord du verre devant et derrière le cercle d'une monture cerclée.
   * Le sommet du biseau est logé dans la rainure, supposée au milieu de la profondeur
   * du cercle. opts = { profondeur (mm), biseauMode, biseau }.
   * Valeurs positives = le verre dépasse ; négatives = il est en retrait du cercle.
   */
  function debordCerclage(res, opts) {
    const D = Math.max(0, +opts.profondeur || 0);
    const { A, B } = res.calibre;
    const points = res.bords.map((e, i) => {
      const b = positionBiseau(e, opts);
      const [u, v] = res._contour[i];
      return { e, biseau: b, devant: b - D / 2, derriere: e - b - D / 2, zone: zone(u, v, A, B) };
    });
    const pire = (cle) => points.reduce((m, p) => (p[cle] > m[cle] ? p : m), points[0]);
    const devant = pire("devant"), derriere = pire("derriere");
    // Biseau qui aligne partout la face avant du verre sur l'avant du cercle (rien ne dépasse devant).
    const biseauAligneAvant = D / 2;
    const emax = Math.max(...res.bords);
    return {
      profondeur: D,
      points,
      devantMax: { mm: devant.devant, zone: devant.zone },
      derriereMax: { mm: derriere.derriere, zone: derriere.zone },
      suggestion: { biseauMm: biseauAligneAvant, derriereMax: emax - Math.min(biseauAligneAvant, emax) - D / 2 },
    };
  }

  /** Épaisseur (mm) en un point (u, v) du repère boxing du verre calculé. */
  function epaisseurEn(res, u, v) {
    const [X, Y] = res._versOC([u, v]);
    return res.centre + res._geo.g(X, Y);
  }

  /** Compare tous les matériaux pour une même ordonnance et une même monture. */
  function comparerMateriaux(p, ids) {
    return (ids || MATERIAUX.map((m) => m.id)).map((id) => {
      try {
        return calculerVerre({ ...p, materiau: id, tcMin: undefined, base: p.baseImposee ? p.base : undefined });
      } catch (e) {
        return { materiau: materiau(id), erreur: e.message };
      }
    });
  }

  return {
    MATERIAUX,
    MONTAGES,
    CERCLAGES,
    FORMES,
    materiau,
    contourForme,
    lireOMA,
    baseConseillee,
    DIAMETRES_PALET,
    diametrePaletStandard,
    calculerVerre,
    coupe,
    coupeHorizontale,
    quatreBords,
    epaisseurEn,
    positionBiseau,
    debordCerclage,
    dansPolygone,
    comparerMateriaux,
    boite,
    _interne: { flecheConique, flecheBiconique, geometrieVerre },
  };
});
