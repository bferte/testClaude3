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
    carte.querySelector(".choisir").addEventListener("click", () => choisir(v));
    carte.querySelector(".copier").addEventListener("click", (e) => copier(v.voice_id, e.currentTarget));
    return carte;
  }));
  $("#vide").hidden = voix.length > 0;
  marquerCarteChoisie();
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

// ------------------------------------------------------- synthèse vocale
// Modèles qui parlent français (vérifié via /v1/models). Utilisés si la clé ne peut pas lire la liste.
const MODELES_FR = [
  { id: "eleven_multilingual_v2", nom: "Multilingual v2", limite: 10000 },
  { id: "eleven_v4", nom: "Eleven v4", limite: 10000 },
  { id: "eleven_v4_turbo", nom: "Eleven v4 Turbo", limite: 10000 },
  { id: "eleven_v3", nom: "Eleven v3", limite: 5000 },
  { id: "eleven_v3_conversational", nom: "Eleven v3 Conversational", limite: 5000 },
  { id: "eleven_flash_v2_5", nom: "Flash v2.5", limite: 40000 },
  { id: "eleven_turbo_v2_5", nom: "Turbo v2.5", limite: 40000 },
];
const NOTES_MODELES = {
  eleven_multilingual_v2: "Le plus stable pour de longs textes, très naturel en français. Choix par défaut.",
  eleven_v4: "Dernière génération, la plus expressive.",
  eleven_v4_turbo: "Version rapide d'Eleven v4.",
  eleven_v3: "Très expressif ; comprend les balises d'émotion comme [rire] ou [chuchote].",
  eleven_v3_conversational: "Variante d'Eleven v3 réglée pour le dialogue.",
  eleven_flash_v2_5: "Latence la plus faible, moitié moins de crédits par caractère.",
  eleven_turbo_v2_5: "Bon compromis entre qualité et vitesse, moitié moins de crédits.",
};
const ORDRE_MODELES = MODELES_FR.map((m) => m.id);
let modeles = MODELES_FR;

async function chargerModeles() {
  try {
    const liste = await (await appel("/v1/models")).json();
    const fr = liste.filter((m) => m.can_do_text_to_speech && (m.languages || []).some((l) => l.language_id === "fr"))
      .map((m) => ({ id: m.model_id, nom: m.name.replace(/^Eleven (?=Multilingual|Flash|Turbo)/, ""),
        limite: m.max_characters_request_free_user || 5000 }));
    if (fr.length) modeles = fr.sort((a, b) => rang(a.id) - rang(b.id));
  } catch { modeles = MODELES_FR; } // clé sans « Models : read » : liste connue
  const sel = $("#modele"), actuel = sel.value;
  sel.replaceChildren(...modeles.map((m) => new Option(m.nom, m.id)));
  sel.value = modeles.some((m) => m.id === actuel) ? actuel : "eleven_multilingual_v2";
  majModele();
}
function rang(id) { const i = ORDRE_MODELES.indexOf(id); return i < 0 ? 99 : i; }
function modeleChoisi() { return modeles.find((m) => m.id === $("#modele").value) || modeles[0]; }

function majModele() {
  const m = modeleChoisi();
  $("#info-modele").textContent = `${NOTES_MODELES[m.id] || ""} Jusqu'à ${m.limite.toLocaleString("fr-FR")} caractères par requête.`.trim();
  majCompteur();
}
function majCompteur() {
  const n = $("#texte").value.trim().length, max = modeleChoisi().limite;
  const c = $("#compteur");
  c.textContent = `${n.toLocaleString("fr-FR")} / ${max.toLocaleString("fr-FR")} caractères`;
  c.classList.toggle("trop", n > max);
  $("#generer").disabled = n === 0 || n > max;
}

function remplirVoix() {
  const sel = $("#voix"), actuel = sel.value;
  const groupe = (libelle, liste) => {
    const g = document.createElement("optgroup"); g.label = libelle;
    liste.forEach((v) => g.append(new Option(decouperNom(v.name)[0] + " · " + (LANGUES[v.labels?.language] || "?") +
      (v.labels?.gender ? " · " + (GENRES[v.labels.gender] || v.labels.gender) : ""), v.voice_id)));
    return g;
  };
  const ok = etat.voix.filter((v) => statutApi(v) === "ok"), payant = etat.voix.filter((v) => statutApi(v) !== "ok");
  sel.replaceChildren(groupe("Utilisables via l'API", ok), ...(payant.length ? [groupe("Abonnement requis", payant)] : []));
  const parDefaut = ok.find((v) => v.name.startsWith("George")) || ok[0] || etat.voix[0];
  sel.value = etat.voix.some((v) => v.voice_id === actuel) ? actuel : parDefaut?.voice_id || "";
  marquerCarteChoisie();
}

function choisir(v) {
  $("#voix").value = v.voice_id;
  $("#retour-tts").hidden = true;
  marquerCarteChoisie();
  $(".tts").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  $("#texte").focus({ preventScroll: true });
}
function marquerCarteChoisie() {
  document.querySelectorAll(".carte").forEach((c) => c.classList.toggle("choisie", c.dataset.id === $("#voix").value));
}

async function generer() {
  const bouton = $("#generer"), retour = $("#retour-tts");
  const texte = $("#texte").value.trim();
  const v = etat.voix.find((x) => x.voice_id === $("#voix").value);
  const m = modeleChoisi();
  if (!texte || !v) return;
  bouton.disabled = true; bouton.textContent = "Synthèse en cours…"; retour.hidden = true;
  try {
    const reponse = await appel(`/v1/text-to-speech/${v.voice_id}?output_format=mp3_44100_128`, {
      method: "POST", headers: { "Content-Type": "application/json", Accept: "audio/mpeg" },
      body: JSON.stringify({ text: texte, model_id: m.id, voice_settings: {
        stability: +$("#stabilite").value, similarity_boost: +$("#similarite").value,
        style: +$("#style").value, speed: +$("#vitesse").value } }) });
    const url = URL.createObjectURL(await reponse.blob());
    if (!etat.verifications[v.voice_id]) { etat.verifications[v.voice_id] = "ok"; afficher(); }
    ajouterHistorique({ url, texte, voix: decouperNom(v.name)[0], modele: m.nom });
  } catch (e) {
    if (e.statut === 402) {
      etat.verifications[v.voice_id] = "payant"; afficher(); remplirVoix();
      afficherRetour(retour, `${decouperNom(v.name)[0]} est une voix de la Voice Library : l'API la refuse avec l'offre gratuite. Choisissez une voix « ✓ API ».`, true);
    } else afficherRetour(retour, messageErreur(e), true);
  } finally {
    bouton.textContent = "Générer l'audio"; majCompteur();
  }
}

function ajouterHistorique({ url, texte, voix, modele }) {
  const heure = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const li = document.createElement("li");
  const meta = Object.assign(document.createElement("span"), { className: "meta", textContent: `${heure} · ${voix} · ${modele}` });
  const lien = Object.assign(document.createElement("a"), { href: url, textContent: "Télécharger le MP3",
    download: `tts_${voix.toLowerCase().replace(/[^a-z0-9]+/g, "-")}_${heure.replace(/:/g, "")}.mp3` });
  const extrait = Object.assign(document.createElement("p"), { className: "extrait",
    textContent: texte.length > 160 ? texte.slice(0, 160) + "…" : texte });
  const audio = Object.assign(document.createElement("audio"), { controls: true, src: url });
  li.append(meta, lien, extrait, audio);
  $("#historique").prepend(li);
  audio.addEventListener("play", () => document.querySelectorAll("#historique audio").forEach((a) => a !== audio && a.pause()));
  audio.play().catch(() => {});
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
    remplirVoix();
    await chargerModeles();
  } catch (e) {
    message(e.statut === 401 && /voices_read/.test(e.message)
      ? "Cette clé n'a pas la permission « Voices : read ». Ajoutez-la dans ElevenLabs > API Keys."
      : messageErreur(e), true);
  } finally {
    bouton.disabled = false; bouton.textContent = "Charger les voix";
  }
}

$("#form-cle").addEventListener("submit", charger);
$("#generer").addEventListener("click", generer);
$("#modele").addEventListener("change", majModele);
$("#texte").addEventListener("input", majCompteur);
$("#voix").addEventListener("change", () => { marquerCarteChoisie(); $("#retour-tts").hidden = true; });
["stabilite", "similarite", "style", "vitesse"].forEach((id) => $("#" + id).addEventListener("input", (e) =>
  ($("#v-" + id).textContent = (+e.target.value).toFixed(2))));
["#recherche", "#filtre-langue", "#filtre-genre", "#filtre-api"].forEach((s) =>
  $(s).addEventListener("input", afficher));

try {
  const memorisee = localStorage.getItem(CLE_STOCKAGE);
  if (memorisee) { $("#cle").value = memorisee; $("#memoriser").checked = true; charger(); }
} catch { /* rien */ }
