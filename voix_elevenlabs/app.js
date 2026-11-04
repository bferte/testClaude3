// Liste des voix ElevenLabs, appelée directement depuis le navigateur (l'API autorise le CORS).
// Authentification : en-tête xi-api-key (https://elevenlabs.io/docs/api-reference/authentication).
const API = "https://api.elevenlabs.io";
const CLE_STOCKAGE = "elevenlabs-cle";
const LANGUES = { fr: "Français", en: "Anglais", es: "Espagnol", de: "Allemand", it: "Italien",
  pt: "Portugais", nl: "Néerlandais", pl: "Polonais", ja: "Japonais", zh: "Chinois", ar: "Arabe" };
const GENRES = { male: "Homme", female: "Femme", neutral: "Neutre" };
const AGES = { young: "Jeune", middle_aged: "Âge moyen", middle_age: "Âge moyen", old: "Âgé" };

const $ = (s) => document.querySelector(s);
const etat = { cle: "", voix: [], verifications: {} }; // verifications[id] = "ok" | "payant"
let audioEnCours = null;

// ------------------------------------------------------------------- API
async function appel(chemin, options = {}) {
  const reponse = await fetch(API + chemin, {
    ...options, headers: { "xi-api-key": etat.cle, ...(options.headers || {}) } });
  if (!reponse.ok) {
    let detail = "";
    try { const j = await reponse.json(); detail = j.detail?.message || JSON.stringify(j.detail || j); }
    catch { detail = await reponse.text().catch(() => ""); }
    const erreur = new Error(detail || reponse.statusText);
    erreur.statut = reponse.status;
    throw erreur;
  }
  return reponse;
}

async function toutesLesVoix() {
  const resultat = [];
  let jeton = "";
  do {
    const params = new URLSearchParams({ page_size: "100" });
    if (jeton) params.set("next_page_token", jeton);
    const page = await (await appel("/v2/voices?" + params)).json();
    resultat.push(...page.voices);
    jeton = page.has_more ? page.next_page_token : "";
  } while (jeton);
  return resultat;
}

// Une voix copiée depuis la Voice Library n'est utilisable via l'API qu'avec un abonnement payant
// (erreur 402 en compte gratuit). Les voix premade et vos propres clones le sont toujours.
function estLibrary(v) { return v.sharing?.status === "copied"; }
function statutApi(v) { return etat.verifications[v.voice_id] || (estLibrary(v) ? "payant" : "ok"); }

// ------------------------------------------------------------- affichage
function decouperNom(nom) {
  const m = nom.match(/^(.+?)\s+[-–—]\s+(.+)$/);
  return m ? [m[1], m[2]] : [nom, ""];
}

function etiquettes(v) {
  const l = v.labels || {};
  return [
    LANGUES[l.language] || l.language,
    GENRES[l.gender] || l.gender,
    AGES[l.age] || l.age,
    l.accent && l.accent !== "standard" ? "Accent " + l.accent : "",
    estLibrary(v) ? "Library" : v.category === "premade" ? "Premade" : v.category,
  ].filter(Boolean);
}

function remplirFiltres() {
  const remplir = (select, valeurs, libelles) => {
    const actuel = select.value;
    select.length = 1;
    [...new Set(valeurs.filter(Boolean))].sort().forEach((val) =>
      select.add(new Option(libelles[val] || val, val)));
    select.value = actuel;
  };
  remplir($("#filtre-langue"), etat.voix.map((v) => v.labels?.language), LANGUES);
  remplir($("#filtre-genre"), etat.voix.map((v) => v.labels?.gender), GENRES);
}

function voixFiltrees() {
  const q = $("#recherche").value.trim().toLowerCase();
  const langue = $("#filtre-langue").value, genre = $("#filtre-genre").value;
  const apiSeulement = $("#filtre-api").checked;
  return etat.voix.filter((v) =>
    (!q || [v.name, v.description, v.voice_id].join(" ").toLowerCase().includes(q)) &&
    (!langue || v.labels?.language === langue) &&
    (!genre || v.labels?.gender === genre) &&
    (!apiSeulement || statutApi(v) === "ok"));
}

function afficher() {
  const liste = $("#liste"), modele = $("#modele-carte");
  const voix = voixFiltrees();
  const utilisables = etat.voix.filter((v) => statutApi(v) === "ok").length;
  $("#resume").textContent = `${etat.voix.length} voix sur le compte · ${utilisables} utilisables via l'API · ${voix.length} affichées`;
  liste.replaceChildren(...voix.map((v) => {
    const carte = modele.content.firstElementChild.cloneNode(true);
    const [nom, accroche] = decouperNom(v.name);
    const statut = statutApi(v);
    carte.dataset.id = v.voice_id;
    carte.classList.toggle("indisponible", statut !== "ok");
    carte.querySelector(".nom").textContent = nom;
    carte.querySelector(".accroche").textContent = accroche;
    carte.querySelector(".description").textContent = v.description || "";
    const pastille = carte.querySelector(".statut");
    pastille.className = "statut " + statut;
    pastille.textContent = statut === "ok"
      ? (etat.verifications[v.voice_id] ? "✓ API vérifiée" : "✓ API") : "Abonnement requis";
    pastille.title = statut === "ok" ? "Utilisable via l'API avec votre offre"
      : "Voix de la Voice Library : l'API la refuse en compte gratuit (erreur 402)";
    carte.querySelector(".etiquettes").replaceChildren(...etiquettes(v).map((t) => {
      const li = document.createElement("li"); li.textContent = t; return li; }));
    carte.querySelector(".id").textContent = v.voice_id;
    const ecouter = carte.querySelector(".ecouter");
    if (!v.preview_url) ecouter.hidden = true;
    ecouter.addEventListener("click", () => jouer(v.preview_url, ecouter));
    carte.querySelector(".tester").addEventListener("click", (e) => tester(v, e.currentTarget, carte));
    carte.querySelector(".copier").addEventListener("click", (e) => copier(v.voice_id, e.currentTarget));
    return carte;
  }));
  $("#vide").hidden = voix.length > 0;
}

// --------------------------------------------------------------- actions
function jouer(source, bouton) {
  if (audioEnCours) {
    audioEnCours.audio.pause();
    audioEnCours.bouton.textContent = "▶ Extrait";
    const memeBouton = audioEnCours.bouton === bouton;
    audioEnCours = null;
    if (memeBouton) return;
  }
  const audio = new Audio(source);
  audioEnCours = { audio, bouton };
  bouton.textContent = "■ Stop";
  audio.addEventListener("ended", () => { bouton.textContent = "▶ Extrait"; audioEnCours = null; });
  audio.play().catch(() => { bouton.textContent = "▶ Extrait"; audioEnCours = null; });
}

async function tester(v, bouton, carte) {
  const retour = carte.querySelector(".retour");
  const texte = $("#texte-test").value.trim() || "Bonjour.";
  bouton.disabled = true; bouton.textContent = "Synthèse…";
  retour.hidden = true;
  try {
    const reponse = await appel(`/v1/text-to-speech/${v.voice_id}?output_format=mp3_44100_128`, {
      method: "POST", headers: { "Content-Type": "application/json", Accept: "audio/mpeg" },
      body: JSON.stringify({ text: texte, model_id: $("#modele").value }) });
    const url = URL.createObjectURL(await reponse.blob());
    etat.verifications[v.voice_id] = "ok";
    afficher();
    const nouvelleCarte = document.querySelector(`.carte[data-id="${v.voice_id}"]`);
    if (nouvelleCarte) jouer(url, nouvelleCarte.querySelector(".ecouter"));
    else new Audio(url).play();
  } catch (e) {
    if (e.statut === 402) {
      etat.verifications[v.voice_id] = "payant";
      afficher(); // la carte est redessinée : le message va sur la nouvelle
      const nouvelle = document.querySelector(`.carte[data-id="${v.voice_id}"] .retour`);
      if (nouvelle) afficherRetour(nouvelle, "Refusée par l'API : cette voix demande un abonnement payant.", true);
      return;
    }
    afficherRetour(retour, messageErreur(e), true);
  } finally {
    bouton.disabled = false; bouton.textContent = "Tester";
  }
}

async function copier(id, bouton) {
  try { await navigator.clipboard.writeText(id); bouton.textContent = "Copié ✓"; }
  catch { bouton.textContent = "Copie impossible"; }
  setTimeout(() => (bouton.textContent = "Copier l'ID"), 1500);
}

function afficherRetour(el, texte, erreur) {
  el.textContent = texte; el.className = "retour " + (erreur ? "erreur" : "ok"); el.hidden = false;
}

function messageErreur(e) {
  if (e.statut === 401) return "Clé refusée : " + e.message;
  if (e.statut === 429) return "Trop de requêtes ou quota atteint.";
  if (e.statut === undefined) return "Impossible de joindre ElevenLabs (connexion ?).";
  return `Erreur ${e.statut} : ${e.message}`;
}

function message(texte, erreur = false) {
  const el = $("#message");
  el.textContent = texte; el.classList.toggle("erreur", erreur); el.hidden = !texte;
}

// ------------------------------------------------------------ démarrage
async function charger(evt) {
  evt?.preventDefault();
  etat.cle = $("#cle").value.trim();
  if (!etat.cle) return;
  try {
    if ($("#memoriser").checked) localStorage.setItem(CLE_STOCKAGE, etat.cle);
    else localStorage.removeItem(CLE_STOCKAGE);
  } catch { /* stockage indisponible : sans importance */ }
  const bouton = $("#bouton-charger");
  bouton.disabled = true; bouton.textContent = "Chargement…";
  message("");
  try {
    etat.voix = (await toutesLesVoix()).sort((a, b) => a.name.localeCompare(b.name, "fr"));
    etat.verifications = {};
    remplirFiltres();
    $("#contenu").hidden = false;
    afficher();
  } catch (e) {
    message(e.statut === 401 && /voices_read/.test(e.message)
      ? "Cette clé n'a pas la permission « Voices : read ». Ajoutez-la dans ElevenLabs > API Keys."
      : messageErreur(e), true);
  } finally {
    bouton.disabled = false; bouton.textContent = "Charger les voix";
  }
}

$("#form-cle").addEventListener("submit", charger);
["#recherche", "#filtre-langue", "#filtre-genre", "#filtre-api"].forEach((s) =>
  $(s).addEventListener("input", afficher));

try {
  const memorisee = localStorage.getItem(CLE_STOCKAGE);
  if (memorisee) { $("#cle").value = memorisee; $("#memoriser").checked = true; charger(); }
} catch { /* rien */ }
