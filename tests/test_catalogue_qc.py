import os
from pathlib import Path

import pytest

from catalogue_qc.analyse import analyser
from catalogue_qc.chargement import lire_classeur, lire_csv
from catalogue_qc.ia_locale import ClientOllama, contexte_anomalies
from catalogue_qc.modele import charger_config, charger_profils
from catalogue_qc.outils import cle_reference, ean_valide, signature
from catalogue_qc.rapport import vers_excel, vers_html

EXEMPLES = Path(__file__).resolve().parent.parent / "exemples"
ENTETE = "Référence;EAN;Marque;Libellé;Code couleur;Taille;Prix achat;PVC\n"


@pytest.fixture(scope="module")
def config():
    return charger_config()


def analyse(config, lignes: str, precedent: str | None = None):
    cat = lire_csv((ENTETE + lignes).encode("cp1252"), config, "test.csv")
    prec = lire_csv((ENTETE + precedent).encode("cp1252"), config, "prec.csv") if precedent else None
    return analyser(cat, config, prec)


def codes(res):
    return {a.code: a for a in res.anomalies}


def test_outils():
    assert ean_valide("4006381333931")
    assert not ean_valide("4006381333932")
    assert signature("rb-12a4") == "AA-99A9"
    assert cle_reference("Rb-1O2") == cle_reference("RB 102")


def test_chargement_et_correspondance_colonnes(config):
    cat = lire_csv((ENTETE + "RB-1;4006381333931;RAY-BAN;Lunette;001;52;10,5;25\n").encode("cp1252"), config)
    assert cat.separateur == ";"
    assert {"reference", "ean", "marque", "libelle", "couleur", "taille", "prix_achat", "prix_vente"} <= set(cat.df.columns)
    assert cat.colonnes_inattendues == []


def test_catalogue_propre(config):
    res = analyse(config, "RB-1;4006381333931;RAY-BAN;Lunette;001;52;10,5;25\n")
    assert res.score == 100
    assert res.verdict == "INTÉGRABLE"


def test_controles_de_base(config):
    res = analyse(config, (
        ";4006381333931;RAY-BAN;Lunette;001;52;10;25\n"          # référence manquante
        "RB-2;4006381333931;RAY-BAN;Lunette;001;52;10;25\n"      # EAN en doublon
        "RB-3;4,00638E+12;RAY-BAN;Lunette;001;52;10;25\n"        # EAN abîmé par Excel
        "RB-4;1234567890123;RAY-BAN;Lunette;001;52;10;25\n"      # clé EAN fausse
        "RB-5;;RAY-BAN;Lunette;001;52;30;25\n"                   # PV < PA + EAN vide
        "RB-6;;RAY-BAN;Lunette;001;52;10;25\n"
        "RB-6;;RAY-BAN;Lunette;001;52;10;29\n"                   # même article, prix différent
        "RB-7;;RAY-BAN;Lunette;001;52;abc;25\n"                  # prix non numérique
    ))
    c = codes(res)
    for code in ["VIDE_REFERENCE", "DOUBLON_EAN", "GTIN_SCIENTIFIQUE_EAN", "GTIN_INVALIDE_EAN", "PV_INF_PA",
                 "CLE_CONFLIT", "PRIX_NON_NUM_PRIX_ACHAT", "VIDE_EAN"]:
        assert code in c, code
    assert c["VIDE_REFERENCE"].exemples["ligne"].tolist() == [2]
    assert res.verdict.startswith("BLOQUANT")


def test_colonne_inattendue_et_absente(config):
    cat = lire_csv(b"Ref;Marque;Divers\nA1;X;y\n", config)
    res = analyser(cat, config)
    c = codes(res)
    assert "COL_INATTENDUE" in c and "Divers" in c["COL_INATTENDUE"].titre
    assert any(a.code == "COL_ABSENTE" and "ean" in a.titre for a in res.anomalies)


def test_marques_incoherentes(config):
    lignes = "".join(f"RB-{i};;{m};Lunette;001;52;10;25\n"
                     for i, m in enumerate(["RAY-BAN"] * 5 + ["RAY BAN", "Rayban", "RAY-BANN"]))
    res = analyse(config, lignes)
    a = codes(res)["MARQUE_VARIANTES"]
    assert a.nb == 1 and a.lignes_touchees == 3
    assert "RAY-BAN" in a.exemples["commentaire"].iloc[0]


def test_references_quasi_identiques(config):
    res = analyse(config, "CA-1020;;CARRERA;L;001;52;10;25\nCA-1O20;;CARRERA;L;002;52;10;25\n")
    assert "REF_QUASI_IDENTIQUES" in codes(res)


def test_prix_erreur_unite(config):
    lignes = "".join(f"RB-{i};;RAY-BAN;L{i};001;52;{40 + i % 7};{100 + i % 11}\n" for i in range(40))
    lignes += "RB-99;;RAY-BAN;L99;001;52;45;10999\n"
    a = codes(analyse(config, lignes))["ERREUR_UNITE_PRIX_VENTE"]
    assert a.exemples["ligne"].tolist() == [42]


def test_comparaison_versions(config):
    prec = ("RB-1;4006381333931;RAY-BAN;L;001;52;10;25\n"
            "RB-2;5901234123457;RAY-BAN;L;001;52;10;25\n"
            "RB-3;9780201379624;RAY-BAN;L;001;52;10;25\n")
    actuel = ("RB-1;4006381333931;RAY-BAN;L;001;52;10;40\n"   # +60 %
              "RB2;5901234123457;RAY-BAN;L;001;52;10;25\n")   # recodifié (même EAN) ; RB-3 supprimé
    c = codes(analyse(config, actuel, prec))
    assert "EVOL_PRIX_PRIX_VENTE" in c
    assert c["EVOL_RECODIFICATION"].nb == 1
    assert c["EVOL_SUPPRESSIONS"].nb == 1
    assert "EVOL_AJOUTS" not in c


def test_exemples_complets_et_exports(config):
    cat = lire_csv(EXEMPLES / "catalogue_actuel.csv", config)
    prec = lire_csv(EXEMPLES / "catalogue_precedent.csv", config)
    res = analyser(cat, config, prec)
    c = codes(res)
    for code in ["DOUBLON_EAN", "GTIN_SCIENTIFIQUE_EAN", "MARQUE_VARIANTES", "EVOL_FORMAT", "EVOL_RECODIFICATION",
                 "EVOL_SUPPRESSIONS", "COL_INATTENDUE", "REF_QUASI_IDENTIQUES", "ERREUR_UNITE_PRIX_VENTE"]:
        assert code in c, code
    assert 0 <= res.score < 60
    assert vers_excel(res)[:2] == b"PK"
    assert "Rapport de contrôle" in vers_html(res, "texte IA")
    assert "Score qualité" in contexte_anomalies(res)


def test_ia_refuse_url_distante(config):
    cfg = dict(config, ia=dict(config["ia"], url="https://api.exemple.com"))
    with pytest.raises(ValueError):
        ClientOllama(cfg)


def test_ia_appel_ollama(config, monkeypatch):
    envoye = {}

    class Reponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "Synthèse OK"}}

    client = ClientOllama(config)

    def post(url, json, timeout):
        envoye.update(url=url, corps=json)
        return Reponse()

    monkeypatch.setattr(client.session, "post", post)
    res = analyse(config, ";;RAY-BAN;L;001;52;10;25\n")
    assert client.resumer(res) == "Synthèse OK"
    assert envoye["url"].startswith("http://localhost")
    assert "sans référence" in envoye["corps"]["messages"][1]["content"]
    assert client.session.trust_env is False


@pytest.mark.parametrize("contenu", [
    ENTETE,                                   # aucune ligne
    ENTETE + ";;;;;;;\n;;;;;;;\n",            # lignes vides uniquement
    ENTETE + ";;RAY-BAN;L;001;52;10;25\n",    # aucune référence renseignée
])
def test_fichiers_degeneres(config, contenu):
    res = analyser(lire_csv(contenu.encode("cp1252"), config), config, lire_csv(contenu.encode(), config))
    assert 0 <= res.score <= 100


# ---------------------------------------------------------------------------
# Format Audition : classeur Excel multi-onglets, en-tête sur 2 lignes
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def audition():
    actuel, config = lire_classeur(EXEMPLES / "audition_actuel.xlsx")
    precedent, _ = lire_classeur(EXEMPLES / "audition_precedent.xlsx", config)
    return actuel, precedent, config


def test_audition_lecture_et_profil_automatique(audition):
    actuel, _, config = audition
    assert config["nom"].startswith("Audition")
    assert set(actuel.tableaux) == {"Audioprothèses", "Accessoires audio"}
    assert set(actuel.referentiels) == {"couleurs", "associations"}
    app = actuel.tableaux["Audioprothèses"]
    assert app.df.index[0] == 3  # n° de ligne Excel (2 lignes d'en-tête)
    assert app.enumerations["Bluetooth"] == {"0": "Non", "1": "Oui"}
    assert app.enumerations["type"]["RIC"] == "Récepteur dans le canal"
    assert "marque" in app.formats_code_libelle
    assert "associations" in actuel.referentiels
    assert "audioprothese_code_produit" in actuel.referentiels["associations"].columns


def test_audition_version_propre(audition):
    _, precedent, config = audition
    res = analyser(precedent, config)
    assert res.score == 100 and res.verdict == "INTÉGRABLE"


def test_audition_anomalies_injectees(audition):
    actuel, precedent, config = audition
    c = codes(analyser(actuel, config, precedent))
    attendus = [
        "VALEUR_HORS_LISTE_BLUETOOTH", "VALEUR_HORS_LISTE_TYPE", "VALEUR_HORS_LISTE_TVA",
        "FORMAT_CODE_LIBELLE_MARQUE", "COULEUR_INCONNUE", "COULEUR_LIBELLE", "DOUBLON_CODE_COMMANDE",
        "GTIN_INVALIDE_REFERENCE", "ERREUR_UNITE_PRIX_ACHAT", "REGLE_DATE_DEBUT_VALIDITE_DATE_FIN_VALIDITE",
        "VIDE_CLASSE_REMBOURSEMENT", "PV_INF_PA", "DOUBLON_INTER_ONGLETS_REFERENCE",
        "ASSOCIATION_ORPHELINE_ACCESSOIRE_AUDIO_CODE_PRODUIT", "ASSOCIATION_SUPPRIME_AUDIOPROTHESE_CODE_PRODUIT",
        "SUPPRESSIONS_DECLAREES", "EVOL_SUPPRESSIONS", "COL_INATTENDUE",
    ]
    manquants = [code for code in attendus if code not in c]
    assert not manquants
    assert "Bluetooth" in c["VALEUR_HORS_LISTE_BLUETOOTH"].titre
    assert c["VALEUR_HORS_LISTE_BLUETOOTH"].onglet == "Audioprothèses"


def test_choix_profil_optique_pour_csv(config):
    _, profil = lire_classeur(EXEMPLES / "catalogue_actuel.csv")
    assert profil["nom"] == config["nom"]
    assert len(charger_profils()) >= 2


@pytest.mark.skipif(not os.environ.get("CATALOGUE_AUDITION_REEL"), reason="catalogue réel non fourni")
def test_catalogue_reel_correct_sans_alerte_bloquante():
    """Non-régression sur un vrai catalogue réputé correct (fichier non versionné).

    CATALOGUE_AUDITION_REEL=/chemin/catalogue.xlsx python -m pytest
    """
    classeur, config = lire_classeur(os.environ["CATALOGUE_AUDITION_REEL"])
    res = analyser(classeur, config)
    assert res.nb("critique") == 0
    assert res.score >= 90
