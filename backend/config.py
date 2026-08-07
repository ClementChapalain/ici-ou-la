from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

CSV_PARTIES = PROJECT_ROOT / "articles.csv"
ARCHIVES_HTML = PROJECT_ROOT / "archives.html"
CACHE_GEOCODAGE = BACKEND_DIR / "geocode_cache.json"
CACHE_ARCHIVES = BACKEND_DIR / "archives_cache"

BASE_URL = "https://www.ici.fr"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
NOMINATIM_UA = "ICIouLa/1.0 (jeu quotidien de geolocalisation a partir des articles de ici.fr)"

FUSEAU = ZoneInfo("Europe/Paris")

MAX_ROWS_CSV = 31
MAX_CANDIDATS = 300
NOMBRE_ARTICLES = 5
PAUSE_NOMINATIM = 1.1
SEUIL_SCORE = 2
TOP_CANDIDATS = 40

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def date_hier() -> date:
    maintenant = datetime.now(FUSEAU)
    return (maintenant - timedelta(days=1)).date()


def dater_aujourdhui() -> date:
    return datetime.now(FUSEAU).date()


def parser_date_csv(valeur: str) -> date | None:
    try:
        jour, mois, annee = valeur.strip().split("/")
        return date(int(annee), int(mois), int(jour))
    except (ValueError, AttributeError):
        return None
