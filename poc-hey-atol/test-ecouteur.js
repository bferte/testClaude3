// Simulation du comportement de Chrome / Edge sans micro : node test-ecouteur.js
// Chrome découpe la phrase en plusieurs résultats et coupe la session sur un silence ;
// Edge renvoie la phrase entière. Le réveil doit marcher dans tous les cas.
let instance;
globalThis.webkitSpeechRecognition = function () {
  instance = this;
  this.start = () => setTimeout(() => this.onstart && this.onstart());
  this.abort = this.stop = () => setTimeout(() => this.onend && this.onend());
};
const W = require("./wake-word.js");

const res = (texte, isFinal = false) => Object.assign([{ transcript: texte, confidence: 0.9 }], { isFinal });
const emettre = (resultIndex, results) => instance.onresult({ resultIndex, results });
const pause = (ms = 5) => new Promise((r) => setTimeout(r, ms));

async function scenario(nom, jouer, attendu) {
  const vu = { reveil: 0, questions: [] };
  const e = W.creerEcouteur({
    onReveil: () => vu.reveil++,
    onQuestion: (q) => vu.questions.push(q),
  });
  e.demarrer();
  await pause();
  await jouer();
  await pause(20);
  e.arreter();
  const ok = vu.reveil === 1 && (attendu === undefined || vu.questions[0] === attendu);
  console.log(ok ? "ok    " : "RATÉ  ", nom, JSON.stringify(vu));
  return ok;
}

(async () => {
  const r = [];
  r.push(await scenario("Edge : phrase entière", async () => {
    emettre(0, [res("Hey Atol quels sont vos horaires", true)]);
  }, "quels sont vos horaires"));

  r.push(await scenario("Chrome : provisoire découpé stable/instable", async () => {
    emettre(0, [res("hey"), res(" atol")]);
    emettre(0, [res("hey atol quels"), res(" sont vos horaires")]);
    emettre(0, [res("Hey Atol quels sont vos horaires", true)]);
  }, "quels sont vos horaires"));

  r.push(await scenario("Chrome : deux résultats finaux séparés", async () => {
    emettre(0, [res("Hey", true)]);
    emettre(1, [res("Hey", true), res(" à tôle", true)]);
    emettre(2, [res("Hey", true), res(" à tôle", true), res(" quels sont vos horaires", true)]);
  }, "quels sont vos horaires"));

  r.push(await scenario("Chrome : session coupée entre « hey » et « atol »", async () => {
    emettre(0, [res("hey", true)]);
    instance.onend();
    await pause();
    emettre(0, [res("Atoll vos horaires", true)]);
  }, "vos horaires"));

  r.push(await scenario("Pas de déclenchement double", async () => {
    emettre(0, [res("hey atol")]);
    emettre(0, [res("hey atol"), res(" bonjour")]);
    emettre(0, [res("hey atol bonjour", true)]);
  }, "bonjour"));

  const faux = { reveil: 0 };
  const e = W.creerEcouteur({ onReveil: () => faux.reveil++ });
  e.demarrer();
  await pause();
  emettre(0, [res("et", true)]);
  emettre(1, [res("et", true), res(" à tout à l'heure", true)]);
  instance.onend();
  await pause();
  emettre(0, [res("à toi", true)]);
  e.arreter();
  const okFaux = faux.reveil === 0;
  console.log(okFaux ? "ok non" : "FAUX+ ", "« et » / « à tout à l'heure » / « à toi » découpés");
  r.push(okFaux);

  process.exit(r.every(Boolean) ? 0 : 1);
})();
