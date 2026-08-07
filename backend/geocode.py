from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path

import requests

from .config import CACHE_GEOCODAGE, NOMINATIM_UA, PAUSE_NOMINATIM

REGIONS = [
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire",
    "Corse", "Grand Est", "Hauts-de-France", "Île-de-France", "Normandie",
    "Nouvelle-Aquitaine", "Occitanie", "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
]

DEPARTEMENTS = [
    "Ain", "Aisne", "Allier", "Alpes-de-Haute-Provence", "Hautes-Alpes", "Alpes-Maritimes",
    "Ardèche", "Ardennes", "Ariège", "Aube", "Aude", "Aveyron", "Bouches-du-Rhône",
    "Calvados", "Cantal", "Charente", "Charente-Maritime", "Cher", "Corrèze",
    "Corse-du-Sud", "Haute-Corse", "Côte-d'Or", "Côtes-d'Armor", "Creuse", "Dordogne",
    "Doubs", "Drôme", "Eure", "Eure-et-Loir", "Finistère", "Gard", "Haute-Garonne",
    "Gers", "Gironde", "Hérault", "Ille-et-Vilaine", "Indre", "Indre-et-Loire", "Isère",
    "Jura", "Landes", "Loir-et-Cher", "Loire", "Haute-Loire", "Loire-Atlantique",
    "Loiret", "Lot", "Lot-et-Garonne", "Lozère", "Maine-et-Loire", "Manche", "Marne",
    "Haute-Marne", "Mayenne", "Meurthe-et-Moselle", "Meuse", "Morbihan", "Moselle",
    "Nièvre", "Nord", "Oise", "Orne", "Pas-de-Calais", "Puy-de-Dôme",
    "Pyrénées-Atlantiques", "Hautes-Pyrénées", "Pyrénées-Orientales", "Bas-Rhin",
    "Haut-Rhin", "Rhône", "Haute-Saône", "Saône-et-Loire", "Sarthe", "Savoie",
    "Haute-Savoie", "Paris", "Seine-Maritime", "Seine-et-Marne", "Yvelines",
    "Deux-Sèvres", "Somme", "Tarn", "Tarn-et-Garonne", "Var", "Vaucluse", "Vendée",
    "Vienne", "Haute-Vienne", "Vosges", "Yonne", "Territoire de Belfort", "Essonne",
    "Hauts-de-Seine", "Seine-Saint-Denis", "Val-de-Marne", "Val-d'Oise",
]

# Régions historiques / espaces géographiques que le type "région" peut renvoyer
REGIONS_HISTORIQUES = [
    "Alsace", "Aquitaine", "Auvergne", "Bourgogne", "Champagne", "Champagne-Ardenne",
    "Franche-Comté", "Limousin", "Lorraine", "Midi-Pyrénées", "Nord-Pas-de-Calais",
    "Picardie", "Poitou", "Poitou-Charentes", "Rhône-Alpes", "Sologne", "Beauce",
    "Brie", "Causses", "Gascogne", "Périgord", "Camargue", "Bassin parisien",
]

# Gentilés de grandes villes -> ville
GENTILES_VILLES = {
    "parisien": "Paris", "parisienne": "Paris", "parisiens": "Paris",
    "marseillais": "Marseille", "marseillaise": "Marseille",
    "lyonnais": "Lyon", "lyonnaise": "Lyon",
    "toulousain": "Toulouse", "toulousaine": "Toulouse",
    "niçois": "Nice", "niçoise": "Nice",
    "nantais": "Nantes", "nantaise": "Nantes",
    "bordelais": "Bordeaux", "bordelaise": "Bordeaux",
    "lillois": "Lille", "lilloise": "Lille",
    "rennais": "Rennes", "rennaise": "Rennes",
    "grenoblois": "Grenoble", "grenobloise": "Grenoble",
    "montpelliérain": "Montpellier", "montpelliéraine": "Montpellier",
    "strasbourgeois": "Strasbourg", "strasbourgeoise": "Strasbourg",
    "nîmois": "Nîmes", "nîmoise": "Nîmes",
    "angevin": "Angers", "angevine": "Angers",
    "brestois": "Brest", "brestoise": "Brest",
    "havrais": "Le Havre", "havraise": "Le Havre",
    "cannois": "Cannes", "cannoise": "Cannes",
    "messin": "Metz", "messine": "Metz",
    "rémois": "Reims", "rémoise": "Reims",
    "tourangeau": "Tours", "tourangelle": "Tours",
    "dijonnais": "Dijon", "dijonnaise": "Dijon",
    "clermontois": "Clermont-Ferrand", "clermontoise": "Clermont-Ferrand",
    "aixois": "Aix-en-Provence", "aixoise": "Aix-en-Provence",
    "toulonnais": "Toulon", "toulonnaise": "Toulon",
    "perpignanais": "Perpignan", "perpignanaise": "Perpignan",
    "avignonnais": "Avignon", "avignonnaise": "Avignon",
    "poitevin": "Poitiers", "poitevine": "Poitiers",
    "caennais": "Caen", "caennaise": "Caen",
    "rouennais": "Rouen", "rouennaise": "Rouen",
    "cévenol": "Cévennes", "dauphinois": "Dauphiné",
}

# Gentilés de départements peu réguliers -> département
GENTILES_DEPARTEMENTS = {
    "corrézien": "Corrèze", "corrézienne": "Corrèze",
    "lozérien": "Lozère", "lozérienne": "Lozère",
    "creusois": "Creuse", "creusoise": "Creuse",
    "dordognais": "Dordogne", "dordognaise": "Dordogne",
    "girondin": "Gironde", "girondine": "Gironde",
    "landais": "Landes", "landaise": "Landes",
    "lotois": "Lot", "lotoise": "Lot",
    "eurois": "Eure", "euroise": "Eure",
    "eurelien": "Eure-et-Loir", "eurelienne": "Eure-et-Loir",
    "morbihannais": "Morbihan", "morbihannaise": "Morbihan",
    "vendéen": "Vendée", "vendéenne": "Vendée",
    "mayennais": "Mayenne", "mayennaise": "Mayenne",
    "aveyronnais": "Aveyron", "aveyronnaise": "Aveyron",
    "gardois": "Gard", "gardoise": "Gard",
    "sarthois": "Sarthe", "sarthoise": "Sarthe",
    "varois": "Var", "varoise": "Var",
    "vauclusien": "Vaucluse", "vauclusienne": "Vaucluse",
    "dromois": "Drôme", "dromoise": "Drôme",
    "ardéchois": "Ardèche", "ardéchoise": "Ardèche",
    "haut-alpin": "Hautes-Alpes", "haut-alpine": "Hautes-Alpes",
    "bas-alpin": "Alpes-de-Haute-Provence", "bas-alpine": "Alpes-de-Haute-Provence",
    "isérois": "Isère", "iséroise": "Isère",
    "loirétain": "Loiret", "loirétaine": "Loiret",
    "pyrénéen": "Pyrénées-Atlantiques", "pyrénéenne": "Pyrénées-Atlantiques",
    "haut-pyrénéen": "Hautes-Pyrénées", "haut-pyrénéenne": "Hautes-Pyrénées",
    "finistérien": "Finistère", "finistérienne": "Finistère",
    "cantalien": "Cantal", "cantalienne": "Cantal",
    "tarnais": "Tarn", "tarnaise": "Tarn",
    "seine-et-marnais": "Seine-et-Marne", "seine-et-marnaise": "Seine-et-Marne",
}

GENTILES_MAP = {**GENTILES_VILLES, **GENTILES_DEPARTEMENTS}

# Centroïdes approximatifs pour les réponses de type "region" : Nominatim est peu
# fiable sur les noms de régions (confusion avec des voies, homonymies).
REGION_CENTROIDS = {
    "auvergne-rhone-alpes": (45.6, 4.2),
    "bourgogne-franche-comte": (47.2, 4.8),
    "bretagne": (48.2, -2.6),
    "centre-val-de-loire": (47.5, 1.5),
    "corse": (42.2, 9.0),
    "grand-est": (48.9, 5.0),
    "hauts-de-france": (49.9, 2.8),
    "ile-de-france": (48.6, 2.4),
    "normandie": (49.1, -0.4),
    "nouvelle-aquitaine": (44.8, 0.3),
    "occitanie": (43.7, 2.2),
    "pays-de-la-loire": (47.5, -0.7),
    "provence-alpes-cote-d-azur": (43.9, 6.1),
    "alsace": (48.3, 7.4),
    "aquitaine": (44.5, 0.0),
    "auvergne": (45.6, 3.0),
    "bourgogne": (47.2, 4.2),
    "champagne": (48.8, 4.4),
    "champagne-ardenne": (48.8, 4.4),
    "franche-comte": (47.1, 5.9),
    "limousin": (45.7, 1.5),
    "lorraine": (48.8, 6.2),
    "midi-pyrenees": (43.9, 1.4),
    "nord-pas-de-calais": (50.5, 2.8),
    "picardie": (49.7, 2.6),
    "poitou": (46.6, 0.2),
    "poitou-charentes": (46.2, 0.0),
    "rhone-alpes": (45.6, 4.9),
    "sologne": (47.48, 1.93),
    "beauce": (48.2, 1.8),
    "brie": (48.8, 3.0),
    "causses": (44.2, 3.3),
    "gascogne": (43.8, 0.3),
    "perigord": (45.1, 0.8),
    "camargue": (43.5, 4.5),
    "cevennes": (44.2, 3.7),
    "dauphine": (45.2, 5.6),
}

SUFFIXES_GENTILES = sorted(
    [
        "aises", "oises", "aises", "iennes", "iennes", "ainais", "annaise", "ais",
        "aise", "oise", "iennes", "ienne", "ien", "ain", "aine", "ains", "anes",
        "ans", "ane", "es", "ard", "arde", "aud", "aude", "at", "ate", "ais",
        "ois", "enne", "ais", "eoise", "esse", "ète", "e", "is", "ois", "in",
        "ine", "el", "elle", "ot", "ote", "ais", "ique", "ache", "aque", "ais",
        "auge", "eau", "aie", "iat", "ière", "e", "ais", "os", "ois", "in",
        "ien", "ais", "aise", "oise", "oises", "iens", "iennes", "aine", "ains",
    ],
    key=len,
    reverse=True,
)


def _norm(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte).casefold()
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


NOMS = {}
for _nom in REGIONS + DEPARTEMENTS + REGIONS_HISTORIQUES:
    NOMS[_norm(_nom)] = _nom
NOMS_NAMES = set(NOMS)
GENTILES_NORMS = {_norm(cle): valeur for cle, valeur in GENTILES_MAP.items()}


def _map_normalise_vers_original(texte: str) -> list[int]:
    positions: list[int] = []
    for i, caractere in enumerate(texte):
        decompose = unicodedata.normalize("NFD", caractere)
        for c in decompose:
            if unicodedata.category(c) != "Mn":
                positions.append(i)
    return positions


def spans_accent_insensibles(titre: str, lieu: str) -> list[tuple[int, int]]:
    tn = _norm(titre)
    ln = _norm(lieu)
    if not ln:
        return []
    positions = _map_normalise_vers_original(titre)
    resultats = []
    debut = 0
    while True:
        i = tn.find(ln, debut)
        if i == -1:
            break
        if i + len(ln) - 1 < len(positions):
            s = positions[i]
            e = positions[i + len(ln) - 1] + 1
            resultats.append((s, e))
        debut = i + 1
    return resultats


def nettoyer_lieu(lieu: str, type_lieu: str) -> tuple[str, bool]:
    """Renvoie (lieu de réponse, était-ce un gentilé)."""
    lieu = lieu.strip()
    if not lieu:
        return lieu, False
    n = _norm(lieu)
    if n in NOMS_NAMES:
        return NOMS[n], False
    if n in GENTILES_NORMS:
        return GENTILES_NORMS[n], True
    for suffixe in SUFFIXES_GENTILES:
        if n.endswith(suffixe):
            base = n[: -len(suffixe)]
            if base in NOMS_NAMES:
                return NOMS[base], True
            if len(base) > 1 and base[-1] == base[-2] and base[:-1] in NOMS_NAMES:
                return NOMS[base[:-1]], True
    return lieu, False


def _premier_mot(lieu: str) -> str | None:
    for separateur in (" ", "-"):
        if separateur in lieu:
            mot = lieu.split(separateur, 1)[0]
            return mot if len(mot) >= 4 else None
    return None


def generer_titre_tronque(titre: str, lieu: str, base: str | None = None) -> str | None:
    aiguilles = [lieu]
    if base and base != lieu:
        aiguilles.append(base)
    premier = _premier_mot(lieu)
    if premier and premier != lieu:
        aiguilles.append(premier)

    spans = set()
    for aiguille in aiguilles:
        for debut, fin in spans_accent_insensibles(titre, aiguille):
            spans.add((debut, fin))
    if not spans:
        return None

    ordres = sorted(spans)
    fusionnes = []
    for debut, fin in ordres:
        if fusionnes and debut < fusionnes[-1][1]:
            fusionnes[-1] = (fusionnes[-1][0], max(fusionnes[-1][1], fin))
        else:
            fusionnes.append((debut, fin))

    pieces = []
    precedent = 0
    for debut, fin in fusionnes:
        pieces.append(titre[precedent:debut])
        pieces.append("_____")
        precedent = fin
    pieces.append(titre[precedent:])
    return "".join(pieces)


_cache: dict | None = None


def _charger_cache() -> dict:
    global _cache
    if _cache is None:
        if CACHE_GEOCODAGE.exists():
            try:
                _cache = json.loads(CACHE_GEOCODAGE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                _cache = {}
        else:
            _cache = {}
    return _cache


def _sauver_cache() -> None:
    if _cache is not None:
        CACHE_GEOCODAGE.write_text(json.dumps(_cache, ensure_ascii=False, indent=1), encoding="utf-8")


def coordonnees_region(lieu: str) -> tuple[float, float] | None:
    return REGION_CENTROIDS.get(_norm(lieu))


def geocoder(lieu: str) -> tuple[float, float] | None:
    """Coordonnées (lat, lon) du lieu en France, ou None si introuvable."""
    cle = _norm(lieu).strip()
    cache = _charger_cache()
    if cle in cache:
        valeur = cache[cle]
        return (float(valeur[0]), float(valeur[1])) if valeur else None

    time.sleep(PAUSE_NOMINATIM)
    url = "https://nominatim.openstreetmap.org/search"
    parametres = {"q": f"{lieu}, France", "format": "jsonv2", "limit": "1", "countrycodes": "fr"}
    try:
        reponse = requests.get(url, params=parametres, headers={"User-Agent": NOMINATIM_UA}, timeout=30)
        reponse.raise_for_status()
        resultats = reponse.json()
    except requests.RequestException:
        cache[cle] = None
        _sauver_cache()
        return None

    if not resultats:
        cache[cle] = None
        _sauver_cache()
        return None

    coords = (float(resultats[0]["lat"]), float(resultats[0]["lon"]))
    cache[cle] = coords
    _sauver_cache()
    return coords
