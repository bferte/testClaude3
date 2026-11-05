// Tests du moteur : node --test epaisseur_verres/
const test = require("node:test");
const assert = require("node:assert/strict");
const E = require("./calcul.js");

function verre(o = {}) {
  const A = o.A ?? 50, B = o.B ?? 50, DBL = o.DBL ?? 18;
  const contour = o.contour ?? E.contourForme(o.forme ?? "ronde", A, B);
  return E.calculerVerre({
    oeil: "OD", sph: 0, cyl: 0, axe: 0, materiau: "1.50", geometrie: "spherique", eMin: 1,
    A, B, DBL, demiEcart: (A + DBL) / 2, hauteur: B / 2, ...o, contour,
  });
}

test("le contour généré respecte exactement le calibre A x B", () => {
  for (const f of Object.keys(E.FORMES)) {
    const b = E.boite(E.contourForme(f, 54, 38));
    assert.ok(Math.abs(b.A - 54) < 1e-9 && Math.abs(b.B - 38) < 1e-9, f);
  }
});

test("verre plan : épaisseur quasi constante", () => {
  const r = verre({ sph: 0 });
  assert.ok(r.bordMax.e - r.bordMin.e < 0.05);
  assert.ok(Math.abs(r.centre - 2) < 1e-9);
});

test("négatif sphérique centré : bord conforme à la formule exacte des flèches", () => {
  const r = verre({ sph: -4 });
  const n = 1.5, base = r.base, R = 25;
  const c1 = base / 530;
  const F1 = (n - 1) * 1000 * c1;
  const F1eff = F1 / (1 - (2 / 1000 / n) * F1);
  const c2 = -(-4 - F1eff) / ((n - 1) * 1000);
  const fl = (c) => (c * R * R) / (1 + Math.sqrt(1 - c * c * R * R));
  const attendu = 2 + fl(c2) - fl(c1);
  assert.ok(Math.abs(r.bordMax.e - attendu) < 0.01, `${r.bordMax.e} vs ${attendu}`);
  assert.ok(r.bordMax.e > 4.4 && r.bordMax.e < 5, "ordre de grandeur -4 D, Ø50, 1.5");
});

test("positif : bord mini respecté, centre plus épais", () => {
  const r = verre({ sph: 4, eMin: 1.2 });
  assert.ok(Math.abs(r.bordMin.e - 1.2) < 1e-6);
  assert.ok(r.centre > 3 && r.centre < 4.5);
});

test("un indice plus élevé amincit le verre", () => {
  const e = ["1.50", "1.60", "1.67", "1.74"].map((m) => verre({ sph: -5, materiau: m, tcMin: 1.5 }).bordMax.e);
  for (let i = 1; i < e.length; i++) assert.ok(e[i] < e[i - 1], e.join(" > "));
});

test("cylindre : le méridien perpendiculaire à l'axe est le plus épais", () => {
  const axe180 = verre({ sph: -2, cyl: -2, axe: 180 });
  assert.match(axe180.bordMax.zone, /^(haut|bas)$/);
  const axe90 = verre({ sph: -2, cyl: -2, axe: 90 });
  assert.match(axe90.bordMax.zone, /nasal|temporal/);
  assert.ok(Math.abs(axe180.bordMax.e - axe90.bordMax.e) < 1e-6);
});

test("décentrement : un écart réduit épaissit le bord temporal d'un négatif", () => {
  const r = verre({ sph: -4, A: 52, B: 40, forme: "rectangle", demiEcart: 30 });
  assert.match(r.bordMax.zone, /temporal/);
  assert.ok(Math.abs(r.decentrement.horizontal - 5) < 1e-9);
  const centre = verre({ sph: -4, A: 52, B: 40, forme: "rectangle" });
  assert.ok(r.bordMax.e > centre.bordMax.e + 1);
});

test("OD et OG symétriques donnent les mêmes épaisseurs", () => {
  const p = { sph: -3, cyl: -1, A: 52, B: 40, forme: "aviateur", demiEcart: 31, hauteur: 22 };
  const od = verre({ ...p, axe: 20 });
  const og = verre({ ...p, oeil: "OG", axe: 160 }); // axe miroir
  assert.ok(Math.abs(od.bordMax.e - og.bordMax.e) < 1e-6);
  assert.equal(od.bordMax.zone, og.bordMax.zone);
});

test("l'asphérique amincit un positif", () => {
  const sph = verre({ sph: 4 }), asph = verre({ sph: 4, geometrie: "aspherique" });
  assert.ok(asph.centre < sph.centre);
  assert.ok(asph.poids < sph.poids);
});

test("poids : ordre de grandeur réaliste", () => {
  const r = verre({ sph: -2, A: 52, B: 40, forme: "rectangle" });
  assert.ok(r.poids > 4 && r.poids < 12, String(r.poids));
});

test("lecture d'un tracé OMA", () => {
  const n = 100;
  const r = Array.from({ length: n }, (_, i) => {
    const a = (2 * Math.PI * i) / n;
    return Math.round(100 / Math.sqrt((Math.cos(a) / 26) ** 2 + (Math.sin(a) / 20) ** 2));
  });
  const txt = `REQ=FIL\nDBL=18.5\nTRCFMT=1;${n};E;R;F\nR=${r.slice(0, 50).join(";")}\nR=${r.slice(50).join(";")}\n`;
  const t = E.lireOMA(txt);
  assert.ok(Math.abs(t.A - 52) < 0.1 && Math.abs(t.B - 40) < 0.1);
  assert.equal(t.DBL, 18.5);
  assert.equal(t.contour.length, n);
});

test("comparaison des matériaux", () => {
  const c = E.contourForme("rectangle", 52, 40);
  const res = E.comparerMateriaux({ oeil: "OD", sph: -6, cyl: 0, axe: 0, eMin: 1, contour: c, A: 52, B: 40, DBL: 18, demiEcart: 31, hauteur: 21 });
  assert.equal(res.length, E.MATERIAUX.length);
  assert.ok(res.every((r) => !r.erreur));
});

test("cerclage : biseau en % et en mm, débords devant/derrière", () => {
  const r = verre({ sph: -6, A: 52, B: 40, forme: "rectangle", demiEcart: 30 });
  const emax = r.bordMax.e;
  // Biseau à 50 % dans un cercle de 4 mm : débord symétrique (e - 4) / 2.
  const mi = E.debordCerclage(r, { profondeur: 4, biseauMode: "pct", biseau: 50 });
  assert.ok(Math.abs(mi.devantMax.mm - (emax - 4) / 2) < 1e-9);
  assert.ok(Math.abs(mi.derriereMax.mm - (emax - 4) / 2) < 1e-9);
  assert.equal(mi.devantMax.zone, r.bordMax.zone);
  // Biseau à 1 mm de l'avant : rien devant (1 - 2 < 0), tout l'excédent derrière.
  const av = E.debordCerclage(r, { profondeur: 4, biseauMode: "mm", biseau: 1 });
  assert.ok(Math.abs(av.devantMax.mm - -1) < 1e-9);
  assert.ok(Math.abs(av.derriereMax.mm - (emax - 1 - 2)) < 1e-9);
  // Suggestion : biseau à D/2 de l'avant -> face avant alignée sur le cercle.
  const sug = E.debordCerclage(r, { profondeur: 4, biseauMode: "mm", biseau: av.suggestion.biseauMm });
  assert.ok(Math.abs(sug.devantMax.mm) < 1e-9);
  assert.ok(Math.abs(sug.derriereMax.mm - av.suggestion.derriereMax) < 1e-9);
});

test("cerclage : verre fin entièrement logé dans un cercle épais", () => {
  const r = verre({ sph: -1, materiau: "1.67" });
  const d = E.debordCerclage(r, { profondeur: 5, biseauMode: "pct", biseau: 33 });
  assert.ok(d.devantMax.mm < 0 && d.derriereMax.mm < 0);
});

test("quatre bords : haut/bas/nasal/temporal cohérents avec les coupes", () => {
  // Négatif décentré en nasal et vers le haut : temporal plus épais que nasal, bas plus épais que haut.
  const r = verre({ sph: -5, A: 52, B: 40, forme: "rectangle", demiEcart: 30, hauteur: 23 });
  const b = Object.fromEntries(E.quatreBords(r).map((x) => [x.nom, x]));
  assert.ok(b.temporal.e > b.nasal.e);
  assert.ok(b.bas.e > b.haut.e);
  const v = E.coupe(r, "v");
  assert.ok(Math.abs(v[0].arriere - v[0].avant - b.bas.e) < 1e-9);
  // avec cerclage : débords calculés à chaque bord
  const c = E.quatreBords(r, { profondeur: 4, biseauMode: "pct", biseau: 50 });
  for (const x of c) assert.ok(Math.abs(x.devant - (x.e - 4) / 2) < 1e-9);
});

test("précalibrage : sans lui, un positif est plus épais au centre ; un négatif ne change pas", () => {
  const p = { sph: 4, A: 50, B: 36, forme: "rectangle", demiEcart: 31, hauteur: 18 };
  const avec = verre(p), sans = verre({ ...p, precalibrage: false });
  assert.ok(sans.centre > avec.centre + 0.5, `${sans.centre} vs ${avec.centre}`);
  assert.equal(sans.palet.diametre, E.diametrePaletStandard(avec.diametreMini));
  assert.ok(Math.abs(sans.palet.bord.min - 0.8) < 1e-6); // bord mini atteint sur le palet
  assert.ok(sans.bordMin.e > avec.bordMin.e); // le bord taillé s'épaissit aussi
  // palet imposé plus grand -> encore plus épais
  const grand = verre({ ...p, precalibrage: false, diametrePalet: 75 });
  assert.ok(grand.centre > sans.centre);
  const neg = { sph: -4, A: 50, B: 36, forme: "rectangle" };
  assert.ok(Math.abs(verre({ ...neg, precalibrage: false }).bordMax.e - verre(neg).bordMax.e) < 1e-9);
});
