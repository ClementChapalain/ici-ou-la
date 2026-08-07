from __future__ import annotations

import logging
from datetime import date

from . import fetch_archive, geocode, llm
from .config import JOURS_FR, MOIS_FR, NOMBRE_ARTICLES

log = logging.getLogger(__name__)


def _normaliser_article(item: dict, articles: list[dict]) -> dict | None:
    idx = item.get("id")
    if not isinstance(idx, int) or not (0 <= idx < len(articles)):
        return None
    article = articles[idx]
    titre = article["titre"]
    lieu = (item.get("lieu") or "").strip()
    type_lieu = (item.get("type") or "").strip().replace("région", "region")

    if not lieu or type_lieu not in ("ville", "departement", "region"):
        return None
    base, est_gentile = geocode.nettoyer_lieu(lieu, type_lieu)
    tronque = geocode.generer_titre_tronque(titre, lieu, base if est_gentile else None)
    if not tronque:
        return None
    return {
        "lieu": base,
        "type": type_lieu,
        "titre_original": titre,
        "titre_tronque": tronque,
        "lien": article["url"],
        "latitude": None,
        "longitude": None,
    }


def _nommer_jour(jour: date) -> str:
    return f"{JOURS_FR[jour.weekday()]} {jour.day} {MOIS_FR[jour.month - 1]} {jour.year}"


def _recherche_complete(candidats: list[dict], jour: date) -> list[dict]:
    """Sélectionne les 5 meilleurs articles (LLM) avec validation géocodage."""
    retenus: list[dict] = []
    exclus: set[int] = set()
    lieux_deja: set[str] = set()

    for _ in range(6):
        if len(retenus) >= NOMBRE_ARTICLES:
            break
        try:
            proposition = llm.appeler_llm(candidats, _nommer_jour(jour), exclus)
        except llm.SelectionIndisponible as erreur:
            log.warning("Sélection LLM impossible : %s", erreur)
            break

        for item in proposition:
            if len(retenus) >= NOMBRE_ARTICLES:
                break
            if item["id"] in exclus:
                continue
            exclus.add(item["id"])
            normalise = _normaliser_article(item, candidats)
            if normalise is None:
                continue
            cle = geocode._norm(normalise["lieu"])
            if cle in lieux_deja:
                continue
            if normalise["type"] == "region":
                coordonnees = geocode.coordonnees_region(normalise["lieu"])
            else:
                coordonnees = geocode.geocoder(normalise["lieu"])
            if coordonnees is None:
                continue
            normalise["latitude"], normalise["longitude"] = coordonnees
            lieux_deja.add(cle)
            retenus.append(normalise)

    return retenus


def construire_partie(jour: date, appel_selection=None) -> dict | None:
    """Construit la partie (dict CSV) du jour donné, ou None si impossible."""
    try:
        articles = fetch_archive.articles_du_jour(jour)
    except fetch_archive.ArchiveIndisponible as erreur:
        log.warning("%s", erreur)
        return None

    log.info("%d articles récupérés pour le %s", len(articles), jour)
    if len(articles) < NOMBRE_ARTICLES:
        return None

    retenus = appel_selection(articles) if appel_selection else _recherche_complete(articles, jour)
    if len(retenus) < NOMBRE_ARTICLES:
        log.warning("Seulement %d articles valides pour le %s", len(retenus), jour)
        return None

    return {"date": jour, "articles": retenus[:NOMBRE_ARTICLES]}
