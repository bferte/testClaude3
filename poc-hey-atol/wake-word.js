/*
 * Détection du mot d'éveil « Hey Atol » avec la reconnaissance vocale du navigateur
 * (Web Speech API). Utilisable dans le navigateur (window.WakeWord) et dans Node
 * (require) pour tester la partie « reconnaissance du texte » sans micro.
 */
(function (racine) {
  "use strict";

  // ---------------------------------------------------------------------------
  // 1. Reconnaissance tolérante de la phrase dans une transcription
  // ---------------------------------------------------------------------------

  // Façons dont le moteur transcrit réellement « hey » et « atol » en français.
  var INTERJECTIONS = ["hey", "hei", "hay", "he", "hee", "eh", "e", "et", "ey", "ay", "ai", "haie", "hai", "o", "oh"];
  var ATOL = ["atol", "atoll", "atolle", "atole", "atolls", "atols", "atoles", "atoll's", "attol", "attoll", "atoal", "atall"];
  // « Atol » coupé en deux mots : « a tôle », « à tol », « ha toll »…
  var ATOL_EN_DEUX = {
    premier: ["a", "ha", "ah"],
    second: ["tol", "toll", "tole", "tolle", "taule", "tolls", "tôle"],
  };
  // Formes « collées » de référence pour la comparaison approximative.
  var CIBLES_COLLEES = ["heyatol", "heatol", "eatol", "etatol", "eyatol"];

  function normaliser(texte) {
    return String(texte || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "") // accents
      .replace(/[’']/g, " ")
      .replace(/[^a-z0-9 ]+/g, " ") // ponctuation, tirets…
      .replace(/\s+/g, " ")
      .trim();
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    var prec = [];
    for (var j = 0; j <= b.length; j++) prec[j] = j;
    for (var i = 1; i <= a.length; i++) {
      var cour = [i];
      for (j = 1; j <= b.length; j++) {
        var cout = a[i - 1] === b[j - 1] ? 0 : 1;
        cour[j] = Math.min(prec[j] + 1, cour[j - 1] + 1, prec[j - 1] + cout);
      }
      prec = cour;
    }
    return prec[b.length];
  }

  function estAtol(mots, i) {
    var normA = ATOL_EN_DEUX.premier.map(normaliser);
    var normB = ATOL_EN_DEUX.second.map(normaliser);
    if (ATOL.indexOf(mots[i]) !== -1) return 1;
    if (normA.indexOf(mots[i]) !== -1 && normB.indexOf(mots[i + 1]) !== -1) return 2;
    return 0;
  }

  /**
   * Cherche « hey atol » dans un texte.
   * options.tolerance : 0 = variantes connues uniquement, 1 (défaut) ou 2 = accepte
   * aussi des transcriptions proches (distance d'édition), 2 étant plus permissif.
   * options.atolSeulEnDebut : accepte « Atol, … » sans interjection en début de phrase.
   * Retourne null ou { indexFin, methode, extrait } ; indexFin = nombre de mots
   * consommés, ce qui suit est la question éventuelle (« hey atol quels sont vos horaires »).
   */
  function detecter(texte, options) {
    options = options || {};
    var tolerance = options.tolerance == null ? 1 : options.tolerance;
    var mots = normaliser(texte).split(" ").filter(Boolean);

    for (var i = 0; i < mots.length; i++) {
      // a) « hey » + « atol » (en un ou deux mots)
      if (INTERJECTIONS.indexOf(mots[i]) !== -1) {
        var n = estAtol(mots, i + 1);
        if (n) return resultat(mots, i, i + 1 + n, "variante");
      }
      // b) tout collé : « heyatol », « hayatoll »
      if (/^(hey|hay|he|hei|ey|e|eh)a?t+o(l+|ll)e?s?$/.test(mots[i])) {
        return resultat(mots, i, i + 1, "variante");
      }
      // c) approximatif : on recolle 1 à 3 mots et on compare aux formes de référence
      if (tolerance > 0) {
        for (var taille = 1; taille <= 3 && i + taille <= mots.length; taille++) {
          var colle = mots.slice(i, i + taille).join("");
          if (colle.length < 5 || colle.length > 9) continue;
          // Le mot doit contenir « t » et se terminer par un son en « ol/oll/ole » ou « al »,
          // pour éviter « et à tout », « hé à toi », etc.
          if (!/t+(o|au)l+e?s?$/.test(colle)) continue;
          for (var c = 0; c < CIBLES_COLLEES.length; c++) {
            if (levenshtein(colle, CIBLES_COLLEES[c]) <= tolerance) {
              return resultat(mots, i, i + taille, "approx");
            }
          }
        }
      }
    }
    // d) « Atol, … » seul en début de phrase
    if (options.atolSeulEnDebut && mots.length && estAtol(mots, 0)) {
      return resultat(mots, 0, estAtol(mots, 0), "atol-seul");
    }
    return null;
  }

  function resultat(mots, debut, fin, methode) {
    return {
      indexFin: fin,
      methode: methode,
      extrait: mots.slice(debut, fin).join(" "),
      suite: mots.slice(fin).join(" "),
    };
  }

  // ---------------------------------------------------------------------------
  // 2. Écoute continue robuste
  // ---------------------------------------------------------------------------

  /**
   * Crée un écouteur qui reste actif en permanence et appelle onReveil quand
   * « hey atol » est entendu.
   *
   * Corrige les problèmes classiques :
   *  - langue forcée en fr-FR ;
   *  - lecture des résultats PROVISOIRES (détection immédiate, sans attendre la fin de phrase) ;
   *  - lecture de toutes les ALTERNATIVES proposées par le moteur, pas seulement la première ;
   *  - redémarrage automatique quand Chrome coupe l'écoute (silence, ~60 s, erreur réseau) ;
   *  - pas de double déclenchement sur la même phrase.
   */
  function creerEcouteur(cfg) {
    cfg = cfg || {};
    var Reco = racine.SpeechRecognition || racine.webkitSpeechRecognition;
    var log = cfg.onLog || function () {};
    if (!Reco) {
      return { supporte: false, demarrer: function () {}, arreter: function () {} };
    }

    var reco = new Reco();
    reco.lang = cfg.lang || "fr-FR";
    reco.continuous = true;
    reco.interimResults = true;
    reco.maxAlternatives = 5;

    var actif = false;
    // Après « hey atol », on capte la question qui suit, dans la même session (sans la
    // couper, pour ne rien perdre). question = { reveil: index du résultat contenant
    // « hey atol » (-1 si aucun), debut: index du premier résultat appartenant à la question }
    var question = null;
    var questionTimer = null;
    var nbResultats = 0;
    var dernierReveil = 0;
    var dejaDeclenche = {}; // index de résultat déjà utilisé pour un réveil
    var echecsRapides = 0;
    var debutSession = 0;
    var optionsDetection = { tolerance: cfg.tolerance, atolSeulEnDebut: cfg.atolSeulEnDebut };

    reco.onstart = function () {
      debutSession = Date.now();
      dejaDeclenche = {};
      nbResultats = 0;
      if (question) question = { reveil: -1, debut: 0 }; // nouvelle session : tout est question
      if (cfg.onEtat) cfg.onEtat(question ? "question" : "veille");
    };

    reco.onresult = function (ev) {
      nbResultats = ev.results.length;
      for (var i = ev.resultIndex; i < ev.results.length; i++) {
        var res = ev.results[i];
        var alternatives = [];
        for (var k = 0; k < res.length; k++) alternatives.push(res[k].transcript);
        log({ type: "transcription", final: res.isFinal, alternatives: alternatives, confiance: res[0].confidence });

        if (question || dejaDeclenche[i]) continue;
        for (k = 0; k < alternatives.length; k++) {
          var trouve = detecter(alternatives[k], optionsDetection);
          if (!trouve) continue;
          dejaDeclenche[i] = true;
          if (Date.now() - dernierReveil < 2500) break; // anti-rebond
          dernierReveil = Date.now();
          log({ type: "reveil", texte: alternatives[k], detail: trouve, alternative: k });
          if (cfg.onReveil) cfg.onReveil(trouve);
          ecouterQuestion({ reveil: i, debut: i + 1 });
          break;
        }
      }
      if (question) suivreQuestion(ev.results);
    };

    // Reconstitue la question : la fin du résultat « hey atol … » + les résultats suivants.
    function suivreQuestion(resultats) {
      var morceaux = [];
      var toutFinal = true;
      if (question.reveil >= 0 && question.reveil < resultats.length) {
        var r = resultats[question.reveil];
        var trouve = detecter(r[0].transcript, optionsDetection);
        if (trouve && trouve.suite) morceaux.push(trouve.suite);
        toutFinal = r.isFinal;
      }
      for (var j = question.debut; j < resultats.length; j++) {
        morceaux.push(resultats[j][0].transcript.trim());
        toutFinal = resultats[j].isFinal;
      }
      var texte = morceaux.join(" ").replace(/\s+/g, " ").trim();
      if (!texte) return;
      if (cfg.onQuestionPartielle) cfg.onQuestionPartielle(texte);
      if (toutFinal) terminerQuestion(texte);
      else armerDelai(); // l'utilisateur parle encore : on prolonge
    }

    function ecouterQuestion(depart) {
      question = depart || { reveil: -1, debut: nbResultats };
      if (cfg.onEtat) cfg.onEtat("question");
      armerDelai();
    }

    function armerDelai() {
      clearTimeout(questionTimer);
      questionTimer = setTimeout(function () {
        if (question) terminerQuestion(null);
      }, cfg.delaiQuestionMs || 8000);
    }

    function terminerQuestion(texte) {
      clearTimeout(questionTimer);
      question = null;
      if (cfg.onEtat) cfg.onEtat("veille");
      if (texte && cfg.onQuestion) cfg.onQuestion(texte);
      if (!texte && cfg.onSilence) cfg.onSilence();
      // Repart d'une session vierge (Chrome accumule sinon tous les résultats)
      redemarrer();
    }

    reco.onerror = function (ev) {
      log({ type: "erreur", erreur: ev.error, message: ev.message });
      if (ev.error === "not-allowed" || ev.error === "service-not-allowed") {
        actif = false;
        if (cfg.onEtat) cfg.onEtat("refuse");
      }
      // no-speech, aborted, network, audio-capture : on laisse onend relancer
    };

    reco.onend = function () {
      if (!actif) {
        if (cfg.onEtat) cfg.onEtat("arrete");
        return;
      }
      // Évite de boucler à toute vitesse si le moteur échoue en permanence
      echecsRapides = Date.now() - debutSession < 1000 ? echecsRapides + 1 : 0;
      var attente = Math.min(250 * Math.pow(2, echecsRapides), 10000);
      log({ type: "relance", attenteMs: attente });
      setTimeout(lancer, echecsRapides ? attente : 0);
    };

    function lancer() {
      if (!actif) return;
      try {
        reco.start();
      } catch (e) {
        // InvalidStateError : déjà démarrée
      }
    }

    function redemarrer() {
      try {
        reco.abort(); // onend relancera
      } catch (e) {}
    }

    return {
      supporte: true,
      demarrer: function () {
        actif = true;
        lancer();
      },
      arreter: function () {
        actif = false;
        question = null;
        clearTimeout(questionTimer);
        try {
          reco.stop();
        } catch (e) {}
      },
      // Pour forcer le passage en écoute de question (bouton micro du chat, par ex.)
      ecouterQuestion: function () {
        ecouterQuestion();
      },
    };
  }

  var api = { normaliser: normaliser, detecter: detecter, levenshtein: levenshtein, creerEcouteur: creerEcouteur };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else racine.WakeWord = api;
})(typeof window !== "undefined" ? window : globalThis);
