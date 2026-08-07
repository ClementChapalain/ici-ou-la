from __future__ import annotations

import html
import re
from datetime import date

import requests

from .config import BASE_URL, USER_AGENT

REGLE_SECTION = re.compile(r'<ul id="DayArchivesSection".*?</ul>', re.S)
REGLE_LIEN = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
REGLE_COMMENTAIRE = re.compile(r"<!---->|<!--[^>]*-->")


class ArchiveIndisponible(Exception):
    pass


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "fr-FR,fr;q=0.9"})
    return session


def _titre_propre(texte: str) -> str:
    texte = REGLE_COMMENTAIRE.sub("", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    texte = html.unescape(texte)
    return re.sub(r"\s+", " ", texte).strip()


def url_archives(jour: date) -> str:
    return f"{BASE_URL}/archives/{jour.year}/{jour.day}-{jour.month}"


def _page_archives(session: requests.Session, jour: date, page: int) -> str | None:
    url = url_archives(jour) if page == 1 else f"{url_archives(jour)}?page={page}"
    reponse = session.get(url, timeout=30)
    if reponse.status_code == 404:
        return None
    reponse.raise_for_status()
    return reponse.text


def _articles_depuis_html(texte: str) -> list[tuple[str, str]]:
    section = REGLE_SECTION.search(texte)
    if not section:
        return []
    resultats = []
    for lien in REGLE_LIEN.finditer(section.group(0)):
        chemin = lien.group(1)
        titre = _titre_propre(lien.group(2))
        if not titre:
            continue
        url = chemin if chemin.startswith("http") else BASE_URL + chemin
        resultats.append((url, titre))
    return resultats


def articles_du_jour(jour: date, limite: int = 400) -> list[dict]:
    session = _session()
    vus: dict[str, dict] = {}
    page = 1
    while True:
        texte = _page_archives(session, jour, page)
        if texte is None:
            if page == 1:
                raise ArchiveIndisponible(f"Aucune archive pour le {jour:%d/%m/%Y}")
            break
        entrées = _articles_depuis_html(texte)
        nouvelles = 0
        for url, titre in entrées:
            if url in vus:
                continue
            vus[url] = {"url": url, "titre": titre}
            nouvelles += 1
        if not entrées or nouvelles == 0:
            break
        if len(vus) >= limite:
            break
        page += 1

    articles = list(vus.values())
    if len(articles) > limite:
        articles = articles[:limite]
    return articles
