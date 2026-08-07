from __future__ import annotations

import logging
from datetime import date

from . import fetch_archive, geocode, llm
from .config import JOURS_FR, MOIS_FR, NOMBRE_ARTICLES, SEUIL_SCORE, TOP_CANDIDATS

log = logging.getLogger(__name__)


def _normaliser_article(item: dict, articles: list[dict]) -> dict | None:
    idx = item.get("id")
    if not isinstance(idx, int) or not (0 <= idx < len(articles)):
        return None
    article = articles[idx]
    titre = article["titre"]
    lieu = (item.get("lieu") or "").strip()
    type_lieu = (item.get("type") or "").strip().lower().replace("é", "e")

    if not lieu or type_lieu != "ville":
        return None
    if geocode._norm(lieu) in geocode.NOMS_NAMES and geocode._norm(lieu) != "paris":
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
    """Scoring LLM puis sélection déterministe : géocodage + diversité."""
    try:
        scores = llm.noter_articles(candidats, _nommer_jour(jour))
    except llm.SelectionIndisponible as erreur:
        log.warning("Scoring LLM impossible : %s", erreur)
        return []

    ordres = sorted(scores.items(), key=lambda paire: paire[1], reverse=True)
    top = [idx for idx, score in ordres if score >= SEUIL_SCORE][:TOP_CANDIDATS]
    if not top:
        log.warning("Aucun article au-dessus du seuil %d", SEUIL_SCORE)
        return []

    extraits: dict[int, dict] = {}
    a_traiter = list(top)
    for _ in range(3):
        if not a_traiter:
            break
        try:
            extraits.update(llm.extraire_lieux(candidats, _nommer_jour(jour), a_traiter))
        except llm.SelectionIndisponible as erreur:
            log.warning("Extraction LLM impossible : %s", erreur)
            break
        a_traiter = [idx for idx in a_traiter if idx not in extraits]
    if not extraits:
        return []

    retenus: list[dict] = []
    lieux_deja: set[str] = set()
    sujets_deja: set[str] = set()
    for idx in top:
        if len(retenus) >= NOMBRE_ARTICLES:
            break
        item = extraits.get(idx)
        if item is None:
            continue
        sujet = geocode._norm(item.get("sujet", ""))
        if sujet and sujet in sujets_deja:
            continue
        normalise = _normaliser_article({"id": idx, **item}, candidats)
        if normalise is None:
            continue
        cle = geocode._norm(normalise["lieu"])
        if cle in lieux_deja:
            continue
        coordonnees = geocode.geocoder(normalise["lieu"])
        if coordonnees is None:
            continue
        normalise["latitude"], normalise["longitude"] = coordonnees
        lieux_deja.add(cle)
        if sujet:
            sujets_deja.add(sujet)
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
