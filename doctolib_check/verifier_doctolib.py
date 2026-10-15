"""Contrôle des fiches magasins Doctolib : détecte la mention « n'est pas réservable en ligne ».

Lit une liste d'URL dans un fichier Excel, ouvre chaque page avec Playwright (Chromium),
attend son chargement, cherche la mention dans le texte visible et écrit les résultats
dans un fichier Excel, au fur et à mesure.

Exemple :
    python verifier_doctolib.py urls_magasins.xlsx --onglets 4 --attente 2
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeout
from tqdm import tqdm

MENTION = re.compile(r"n\s*['’ʼ`]\s*est\s+pas\s+réservable\s+en\s+ligne", re.IGNORECASE)

# Boutons de consentement cookies (Didomi, utilisé par Doctolib), cliqués s'ils sont présents.
BOUTONS_COOKIES = [
    "#didomi-notice-agree-button",
    "button:has-text('Accepter')",
    "button:has-text('Tout accepter')",
]

# Indices d'une page de blocage anti-robot (captcha) à la place de la fiche.
INDICES_BLOCAGE = ("captcha-delivery", "datadome", "vérifiez que vous êtes humain", "access denied")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

COLONNES = ["URL", "Nom du magasin", "Statut", "Texte détecté", "Erreur éventuelle"]

RESERVABLE = "Réservable"
NON_RESERVABLE = "Non réservable"
INDETERMINE = "Indéterminé"


@dataclass
class Resultat:
    url: str
    nom: str = ""
    statut: str = INDETERMINE
    texte: str = ""
    erreur: str = ""

    def ligne(self) -> dict:
        return dict(zip(COLONNES, asdict(self).values()))


# --------------------------------------------------------------------------- lecture

def lire_urls(fichier: Path, colonne: str | None, onglet: str | int) -> list[str]:
    df = pd.read_excel(fichier, sheet_name=onglet, dtype=str)
    if colonne is None:
        candidates = [c for c in df.columns if str(c).strip().lower() in ("url", "urls", "lien", "liens")]
        if not candidates:
            raise SystemExit(
                f"Aucune colonne 'URL' trouvée dans {fichier} (colonnes : {list(df.columns)}). "
                "Préciser la colonne avec --colonne."
            )
        colonne = candidates[0]
    elif colonne not in df.columns:
        raise SystemExit(f"Colonne '{colonne}' absente de {fichier} (colonnes : {list(df.columns)}).")

    urls, vues = [], set()
    for brute in df[colonne].dropna():
        url = str(brute).strip()
        if not url:
            continue
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        if url not in vues:
            vues.add(url)
            urls.append(url)
    return urls


# --------------------------------------------------------------------------- sauvegarde

class Sauvegarde:
    """Journal CSV écrit ligne par ligne (aucune perte en cas d'arrêt) + export Excel périodique."""

    def __init__(self, sortie: Path, frequence: int):
        self.sortie = sortie
        self.journal = sortie.with_suffix(".encours.csv")
        self.frequence = max(1, frequence)
        self.resultats: dict[str, dict] = {}
        self._depuis_export = 0

    def reprendre(self) -> int:
        """Recharge les résultats déjà obtenus (hors erreurs, qui seront retentées)."""
        if not self.journal.exists():
            return 0
        with self.journal.open(encoding="utf-8-sig", newline="") as f:
            for ligne in csv.DictReader(f, delimiter=";"):
                if ligne.get("Statut") != INDETERMINE:
                    self.resultats[ligne["URL"]] = ligne
        return len(self.resultats)

    def demarrer(self, reprise: bool) -> None:
        if not reprise or not self.journal.exists():
            with self.journal.open("w", encoding="utf-8-sig", newline="") as f:
                csv.DictWriter(f, COLONNES, delimiter=";").writeheader()

    def ajouter(self, res: Resultat) -> None:
        ligne = res.ligne()
        self.resultats[res.url] = ligne
        with self.journal.open("a", encoding="utf-8-sig", newline="") as f:
            csv.DictWriter(f, COLONNES, delimiter=";").writerow(ligne)
        self._depuis_export += 1
        if self._depuis_export >= self.frequence:
            self.exporter()

    def exporter(self, ordre: list[str] | None = None) -> pd.DataFrame:
        lignes = list(self.resultats.values())
        if ordre:
            rang = {u: i for i, u in enumerate(ordre)}
            lignes.sort(key=lambda l: rang.get(l["URL"], len(rang)))
        df = pd.DataFrame(lignes, columns=COLONNES)
        ecrire_excel(df, self.sortie)
        self._depuis_export = 0
        return df


def ecrire_excel(df: pd.DataFrame, chemin: Path) -> None:
    temporaire = chemin.with_name(f"~tmp_{chemin.name}")
    with pd.ExcelWriter(temporaire, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Résultats")
        feuille = writer.sheets["Résultats"]
        for col, largeur in zip("ABCDE", (70, 40, 16, 60, 50)):
            feuille.column_dimensions[col].width = largeur
        feuille.auto_filter.ref = feuille.dimensions
        feuille.freeze_panes = "A2"
    try:
        temporaire.replace(chemin)  # remplacement atomique : le fichier n'est jamais à moitié écrit
    except PermissionError:
        tqdm.write(f"⚠ {chemin.name} est ouvert dans Excel : résultats écrits dans {temporaire.name}")


# --------------------------------------------------------------------------- analyse d'une page

async def accepter_cookies(page: Page) -> None:
    for selecteur in BOUTONS_COOKIES:
        try:
            bouton = page.locator(selecteur).first
            if await bouton.is_visible(timeout=500):
                await bouton.click(timeout=2000)
                return
        except PlaywrightError:
            pass


async def nom_magasin(page: Page) -> str:
    try:
        h1 = page.locator("h1").first
        if await h1.count():
            nom = (await h1.inner_text(timeout=2000)).strip()
            if nom:
                return " ".join(nom.split())
    except PlaywrightError:
        pass
    titre = (await page.title()).strip()
    # Ex. « Optique X - Opticien à Lyon - Prenez RDV en ligne | Doctolib »
    return re.split(r"\s+[-|–]\s+", titre)[0] if titre else ""


def extrait_autour(texte: str, match: re.Match) -> str:
    """Renvoie la ligne (ou phrase) du texte visible qui contient la mention."""
    debut = texte.rfind("\n", 0, match.start()) + 1
    fin = texte.find("\n", match.end())
    ligne = texte[debut: fin if fin != -1 else len(texte)].strip()
    return ligne[:500]


async def analyser(page: Page, url: str, args: argparse.Namespace) -> Resultat:
    res = Resultat(url=url)
    reponse = await page.goto(url, wait_until="domcontentloaded", timeout=args.timeout * 1000)
    if reponse is not None and reponse.status >= 400:
        res.erreur = f"HTTP {reponse.status}"
    try:
        # Chargement complet : plus aucune requête réseau pendant 500 ms.
        await page.wait_for_load_state("networkidle", timeout=args.timeout * 1000)
    except PlaywrightTimeout:
        pass  # Certaines pages gardent des connexions ouvertes : on analyse quand même.
    await accepter_cookies(page)
    if args.attente > 0:
        await page.wait_for_timeout(args.attente * 1000)

    texte = await page.locator("body").inner_text(timeout=args.timeout * 1000)
    texte = texte.replace(" ", " ").replace(" ", " ")
    res.nom = await nom_magasin(page)

    match = MENTION.search(texte)
    if match:
        res.statut = NON_RESERVABLE
        res.texte = extrait_autour(texte, match)
        res.erreur = ""
        return res

    html = (await page.content()).lower()
    if any(indice in html for indice in INDICES_BLOCAGE) and len(texte) < 2000:
        res.erreur = "Page de blocage anti-robot (captcha) : réduire --onglets ou augmenter --pause"
        return res
    if res.erreur:  # HTTP 404/410… sans la mention : fiche introuvable
        res.nom = ""
        return res
    res.statut = RESERVABLE
    return res


async def analyser_avec_reprises(page: Page, url: str, args: argparse.Namespace) -> Resultat:
    derniere_erreur = ""
    for essai in range(1, args.essais + 1):
        try:
            res = await analyser(page, url, args)
            if res.statut != INDETERMINE or essai == args.essais:
                return res
            derniere_erreur = res.erreur
        except PlaywrightTimeout:
            derniere_erreur = f"Délai dépassé ({args.timeout} s)"
        except PlaywrightError as e:
            derniere_erreur = str(e).splitlines()[0][:300]
        except Exception as e:  # noqa: BLE001 - une URL ne doit jamais arrêter le traitement
            derniere_erreur = f"{type(e).__name__} : {e}"[:300]
        await asyncio.sleep(2 * essai)
    return Resultat(url=url, erreur=f"{derniere_erreur} (après {args.essais} essai(s))")


# --------------------------------------------------------------------------- orchestration

async def onglet_worker(browser: Browser, file: asyncio.Queue, args, sauvegarde: Sauvegarde, barre: tqdm):
    contexte = await browser.new_context(user_agent=USER_AGENT, locale="fr-FR", viewport={"width": 1366, "height": 900})
    if args.sans_images:
        await contexte.route(
            "**/*",
            lambda route: route.abort() if route.request.resource_type in ("image", "media", "font") else route.continue_(),
        )
    page = await contexte.new_page()
    try:
        while True:
            try:
                url = file.get_nowait()
            except asyncio.QueueEmpty:
                return
            res = await analyser_avec_reprises(page, url, args)
            sauvegarde.ajouter(res)
            barre.update(1)
            if res.statut == NON_RESERVABLE:
                barre.set_postfix_str(f"non réservables : {compter(sauvegarde, NON_RESERVABLE)}")
            if res.erreur and res.statut == INDETERMINE:
                tqdm.write(f"✗ {url} → {res.erreur}")
            if page.is_closed():  # onglet planté : on en rouvre un
                page = await contexte.new_page()
            if args.pause > 0:
                await asyncio.sleep(args.pause * random.uniform(0.5, 1.5))
    finally:
        await contexte.close()


def compter(sauvegarde: Sauvegarde, statut: str) -> int:
    return sum(1 for l in sauvegarde.resultats.values() if l["Statut"] == statut)


async def executer(args: argparse.Namespace) -> None:
    entree = Path(args.fichier)
    sortie = Path(args.sortie) if args.sortie else entree.with_name(f"{entree.stem}_resultats.xlsx")
    sortie_non_reservables = sortie.with_name(f"{sortie.stem}_non_reservables.xlsx")

    urls = lire_urls(entree, args.colonne, args.onglet)
    if args.limite:
        urls = urls[: args.limite]
    print(f"{len(urls)} URL à contrôler (fichier : {entree.name})")

    sauvegarde = Sauvegarde(sortie, args.frequence_sauvegarde)
    deja = sauvegarde.reprendre() if args.reprendre else 0
    sauvegarde.demarrer(args.reprendre)
    a_traiter = [u for u in urls if u not in sauvegarde.resultats]
    if deja:
        print(f"Reprise : {deja} URL déjà traitées, {len(a_traiter)} restantes.")

    file: asyncio.Queue[str] = asyncio.Queue()
    for url in a_traiter:
        file.put_nowait(url)

    debut = time.monotonic()
    async with async_playwright() as p:
        options = {"headless": not args.visible}
        if args.executable:
            options["executable_path"] = args.executable
        elif args.chrome:
            options["channel"] = "chrome"
        browser = await p.chromium.launch(**options)
        try:
            with tqdm(total=len(a_traiter), unit="URL", desc="Contrôle", dynamic_ncols=True) as barre:
                nb = max(1, min(args.onglets, len(a_traiter) or 1))
                await asyncio.gather(*(onglet_worker(browser, file, args, sauvegarde, barre) for _ in range(nb)))
        finally:
            await browser.close()
            df = sauvegarde.exporter(ordre=urls)

    non_reservables = df[df["Statut"] == NON_RESERVABLE]
    ecrire_excel(non_reservables.reset_index(drop=True), sortie_non_reservables)

    duree = time.monotonic() - debut
    print(f"\nTerminé en {duree / 60:.1f} min.")
    print(f"  Réservables      : {(df['Statut'] == RESERVABLE).sum()}")
    print(f"  Non réservables  : {len(non_reservables)}")
    print(f"  En erreur        : {(df['Statut'] == INDETERMINE).sum()}  (relancer avec --reprendre pour les retenter)")
    print(f"Résultats complets : {sortie}")
    print(f"Non réservables    : {sortie_non_reservables}")


def parser_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Détecte les fiches Doctolib « non réservables en ligne ».")
    p.add_argument("fichier", help="Fichier Excel contenant les URL")
    p.add_argument("--colonne", help="Nom de la colonne des URL (défaut : colonne 'URL')")
    p.add_argument("--onglet", default=0, help="Onglet Excel à lire (nom ou numéro, défaut : le premier)")
    p.add_argument("--sortie", help="Fichier Excel de résultats (défaut : <fichier>_resultats.xlsx)")
    p.add_argument("--onglets", type=int, default=4, help="Nombre d'onglets ouverts en parallèle (défaut : 4)")
    p.add_argument("--timeout", type=float, default=30, help="Délai max de chargement d'une page, en s (défaut : 30)")
    p.add_argument("--attente", type=float, default=2, help="Attente supplémentaire après chargement, en s (défaut : 2)")
    p.add_argument("--pause", type=float, default=1, help="Pause moyenne entre deux URL d'un même onglet, en s (défaut : 1)")
    p.add_argument("--essais", type=int, default=3, help="Nombre d'essais par URL en cas d'erreur (défaut : 3)")
    p.add_argument("--frequence-sauvegarde", type=int, default=10, help="Mise à jour du fichier Excel toutes les N URL (défaut : 10)")
    p.add_argument("--reprendre", action="store_true", help="Reprendre un traitement interrompu (ne refait que les URL manquantes ou en erreur)")
    p.add_argument("--limite", type=int, help="Ne traiter que les N premières URL (pour un essai)")
    p.add_argument("--visible", action="store_true", help="Afficher le navigateur (utile pour vérifier)")
    p.add_argument("--chrome", action="store_true", help="Utiliser Google Chrome installé sur le poste au lieu du Chromium de Playwright")
    p.add_argument("--executable", help="Chemin d'un exécutable Chrome/Chromium à utiliser")
    p.add_argument("--sans-images", action="store_true", help="Ne pas charger images/polices (plus rapide)")
    args = p.parse_args(argv)
    if isinstance(args.onglet, str) and args.onglet.isdigit():
        args.onglet = int(args.onglet)
    args.essais = max(1, args.essais)
    return args


def main(argv: list[str] | None = None) -> None:
    args = parser_arguments(argv)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        asyncio.run(executer(args))
    except KeyboardInterrupt:
        print("\nInterrompu : les résultats déjà obtenus sont sauvegardés. Relancer avec --reprendre pour continuer.")


if __name__ == "__main__":
    main()
