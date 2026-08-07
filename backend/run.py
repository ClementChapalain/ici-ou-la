from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from . import generate, pipeline
from .config import date_hier, parser_date_csv

log = logging.getLogger("backend")


def _argument_date(valeur: str) -> date:
    return date.fromisoformat(valeur)


def construire_argumentaire() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(description="Génère la partie ICI ou là à partir des archives ici.fr")
    analyseur.add_argument("--date", type=_argument_date, default=None,
                           help="Jour à traiter (ISO), par défaut hier à Paris")
    analyseur.add_argument("--start", type=_argument_date, default=None,
                           help="Début d'une plage de dates (ISO), pour un rattrapage")
    analyseur.add_argument("--end", type=_argument_date, default=None,
                           help="Fin de la plage de dates (ISO)")
    analyseur.add_argument("--dry-run", action="store_true",
                           help="Calcule et affiche la sélection sans écrire de fichiers")
    analyseur.add_argument("--force", action="store_true",
                           help="Régénère même si la date existe déjà dans le CSV")
    analyseur.add_argument("--verbose", action="store_true", help="Logs détaillés")
    return analyseur


def _afficher_partie(partie: dict) -> None:
    print(f"\n=== Partie du {partie['date']} ===")
    for n, article in enumerate(partie["articles"], start=1):
        print(f"{n}. {article['titre_original']}")
        print(f"   lieu : {article['lieu']} ({article['type']})")
        print(f"   tronqué : {article['titre_tronque']}")
        print(f"   {article['lien']}")
        print(f"   {article['latitude']}, {article['longitude']}")


def _journees(argumentaire) -> list[date]:
    if argumentaire.start or argumentaire.end:
        debut = argumentaire.start or argumentaire.date or date_hier()
        fin = argumentaire.end or argumentaire.date or debut
        if debut > fin:
            debut, fin = fin, debut
        return [debut + timedelta(days=i) for i in range((fin - debut).days + 1)]
    return [argumentaire.date or date_hier()]


def principal() -> int:
    analyseur = construire_argumentaire()
    args = analyseur.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    dates_existantes = {d for d in (parser_date_csv(l.get("Date", "")) for l in generate.charger_parties()) if d}

    parties = []
    ignorees = 0
    for jour in _journees(args):
        if jour in dates_existantes and not args.force:
            ignorees += 1
            log.info("%s déjà dans le CSV, génération ignorée (--force pour régénérer)", jour)
            continue
        partie = pipeline.construire_partie(jour)
        if partie:
            parties.append(partie)
            if args.dry_run or args.verbose:
                _afficher_partie(partie)

    if not parties:
        if ignorees:
            log.info("Rien à faire : toutes les dates demandées sont déjà dans le CSV.")
            return 0
        log.warning("Aucune partie générée.")
        return 1

    if args.dry_run:
        return 0

    generate.mettre_a_jour_csv(parties)
    generate.generer_archives(generate.charger_parties())
    return 0


if __name__ == "__main__":
    sys.exit(principal())
