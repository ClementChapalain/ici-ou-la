from __future__ import annotations

import csv
import logging
from datetime import date

from .config import ARCHIVES_HTML, CSV_PARTIES, JOURS_FR, MAX_ROWS_CSV, MOIS_FR, NOMBRE_ARTICLES, parser_date_csv

log = logging.getLogger(__name__)

CHAMPS = ["Date"]
for n in range(1, NOMBRE_ARTICLES + 1):
    CHAMPS += [
        f"{n}-Titre_original",
        f"{n}-Titre_tronqué",
        f"{n}-Type",
        f"{n}-Lieu",
        f"{n}-Lien",
        f"{n}-Latitude",
        f"{n}-Longitude",
    ]


def _date_csv(jour: date) -> str:
    return f"{jour.day}/{jour.month}/{jour.year}"


def charger_parties() -> list[dict]:
    if not CSV_PARTIES.exists():
        return []
    with CSV_PARTIES.open(encoding="utf-8-sig", newline="") as fichier:
        lignes = list(csv.DictReader(fichier))
    return [ligne for ligne in lignes if ligne.get("Date")]


def _ligne_partie(partie: dict) -> dict:
    ligne = {"Date": _date_csv(partie["date"])}
    for n, article in enumerate(partie["articles"], start=1):
        ligne[f"{n}-Titre_original"] = article["titre_original"]
        ligne[f"{n}-Titre_tronqué"] = article["titre_tronque"]
        ligne[f"{n}-Type"] = article["type"]
        ligne[f"{n}-Lieu"] = article["lieu"]
        ligne[f"{n}-Lien"] = article["lien"]
        ligne[f"{n}-Latitude"] = article["latitude"] if article["latitude"] is not None else ""
        ligne[f"{n}-Longitude"] = article["longitude"] if article["longitude"] is not None else ""
    return ligne


def _cle_tri(ligne: dict) -> tuple:
    d = parser_date_csv(ligne.get("Date", ""))
    return (1, d.toordinal()) if d else (0, 0)


def mettre_a_jour_csv(parties: list[dict]) -> None:
    nouvelles = [_ligne_partie(partie) for partie in parties]
    anciennes = charger_parties()
    for ancienne in anciennes:
        if not any(nouvelle.get("Date") == ancienne.get("Date") for nouvelle in nouvelles):
            nouvelles.append(ancienne)
    nouvelles.sort(key=_cle_tri, reverse=True)
    nouvelles = nouvelles[:MAX_ROWS_CSV]

    with CSV_PARTIES.open("w", encoding="utf-8-sig", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=CHAMPS, restval="", lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(nouvelles)
    log.info("CSV mis à jour : %d parties", len(nouvelles))


def _nommer_date(jour: date, avec_annee: bool = False) -> str:
    partie = f"{JOURS_FR[jour.weekday()].capitalize()} {jour.day} {MOIS_FR[jour.month - 1]}"
    if avec_annee:
        partie += f" {jour.year}"
    return partie


def _carte_du_jour(jour: date) -> str:
    return f"""
      <a class="today-card" href="daily.html" aria-label="Jouer la partie du jour du {_nommer_date(jour)}">
        <div>
          <p class="eyebrow">La partie du jour</p>
          <p class="today-card-title">{_nommer_date(jour, avec_annee=True)}</p>
          <p class="today-card-meta">5 lieux à retrouver sur la carte de France</p>
        </div>
        <span class="today-card-cta">Jouer<span aria-hidden="true">→</span></span>
      </a>"""


def _ligne_archive(jour: date) -> str:
    iso = jour.isoformat()
    return f"""
          <li class="game">
            <a class="game-link" href="daily.html?date={iso}" aria-label="Rejouer la partie du {_nommer_date(jour)}">
              <span class="game-date">{_nommer_date(jour)}</span>
              <span class="game-right">
                <span class="game-badge" data-date="{iso}">À jouer</span>
                <span class="game-go" aria-hidden="true">→</span>
              </span>
            </a>
          </li>"""


def generer_archives(parties: list[dict]) -> None:
    dates = [date(int(annee), int(mois), int(jour)) for jour, mois, annee in (d["Date"].split("/") for d in parties)]
    jour = dates[0]
    liste = "\n".join(_ligne_archive(d) for d in dates[1 : MAX_ROWS_CSV])

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Les anciennes parties - ICI ou là</title>
  <link rel="icon" href="favicon.png">
  <link rel="stylesheet" href="style.css">
</head>

<body class="home">
  <div class="page">
    <header class="header">
      <a class="ici-brand" href="index.html" aria-label="ICI ou là, accueil">
        <img src="logo.svg" alt="ICI ou là">
      </a>
    </header>

    <main class="archives">
{_carte_du_jour(jour)}
      <section class="archives-list" aria-labelledby="archives-list-title">
        <h1 id="archives-list-title">Les 30 dernières parties</h1>

        <ol class="games">
{liste}
        </ol>
      </section>

    </main>

  </div>

  <script>
    const CLEF_PARTIES_JOUÉES = "icioulà-parties-jouées";
    try {{
      const jouées = new Set(JSON.parse(localStorage.getItem(CLEF_PARTIES_JOUÉES) || "[]"));
      document.querySelectorAll("[data-date]").forEach(noeud => {{
        if (jouées.has(noeud.dataset.date)) {{
          noeud.closest(".game").classList.add("game--played");
          noeud.textContent = "Jouée";
        }}
      }});
    }} catch (erreur) {{}}
  </script>
</body>

</html>
"""
    ARCHIVES_HTML.write_text(page, encoding="utf-8")
    log.info("archives.html régénéré")
