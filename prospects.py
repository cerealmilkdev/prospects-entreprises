#!/usr/bin/env python3
"""Construit une liste de prospects depuis l'API Recherche d'entreprises.

Source : https://recherche-entreprises.api.gouv.fr — donnees ouvertes officielles
(INSEE / annuaire-entreprises.data.gouv.fr). Pas de scraping, pas de cle, pas de quota
commercial. C'est la version legitime de ce qu'un scraper ferait mal.

Ce que l'API donne : raison sociale, SIREN/SIRET, adresse du siege, code NAF,
tranche d'effectif, date de creation.
Ce qu'elle ne donne PAS : telephone et e-mail. Ils ne sont pas dans l'open data.
Le telephone se recupere ensuite a la main (Google Maps, site web, PagesJaunes).

Usage :
    python3 prospects.py --secteur depannage --departement 69 --effectif 01 --max 30
    python3 prospects.py --secteur dental --departement 75 --max 50 --sortie dental75.csv
"""
import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request

API = "https://recherche-entreprises.api.gouv.fr/search"

# Codes NAF par secteur cible. Un prospect = un decideur joignable, pas une grande structure.
SECTEURS = {
    "depannage": {
        "naf": ["43.22A", "43.22B", "43.21A"],
        "libelle": "plomberie, chauffage-clim, electricite",
    },
    "dental": {"naf": ["86.23Z"], "libelle": "chirurgie dentaire"},
    "medical": {"naf": ["86.21Z", "86.22B", "86.22C"], "libelle": "medecine de ville"},
    "veterinaire": {"naf": ["75.00Z"], "libelle": "veterinaires"},
    "immobilier": {"naf": ["68.31Z"], "libelle": "agences immobilieres"},
    "garage": {"naf": ["45.20A"], "libelle": "entretien et reparation auto"},
    "comptable": {"naf": ["69.20Z"], "libelle": "expertise comptable"},
    "avocat": {"naf": ["69.10Z"], "libelle": "activites juridiques"},
    "btp": {"naf": ["43.32A", "43.33Z", "43.91A"], "libelle": "menuiserie, platrerie, charpente"},
}

# Tranches d'effectif INSEE. 00=0 salarie, 01=1-2, 02=3-5, 03=6-9, 11=10-19.
# Cibler les petites structures : celui qui decroche est celui qui decide.
EFFECTIFS = {
    "00": "0 salarie", "01": "1 a 2", "02": "3 a 5", "03": "6 a 9", "11": "10 a 19",
}


def interroge(naf, departement, effectif, max_resultats):
    """Interroge l'API et rend les fiches dont le SIEGE est bien dans le departement."""
    resultats, page = [], 1
    while len(resultats) < max_resultats and page <= 20:
        params = {
            "activite_principale": naf,
            "departement": departement,
            "per_page": 25,
            "page": page,
        }
        if effectif:
            params["tranche_effectif_salarie"] = effectif
        url = f"{API}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                data = json.load(r)
        except Exception as exc:  # reseau ou API indisponible
            print(f"  ! {naf} page {page} : {exc}", file=sys.stderr)
            break

        lot = data.get("results", [])
        if not lot:
            break

        # Le filtre departement de l'API porte sur les ETABLISSEMENTS : le siege peut etre
        # ailleurs. On ne garde que les sieges effectivement dans le departement vise.
        for e in lot:
            siege = e.get("siege") or {}
            cp = (siege.get("code_postal") or "").strip()
            if not cp.startswith(departement):
                continue
            resultats.append({
                "raison_sociale": e.get("nom_complet") or e.get("nom_raison_sociale") or "",
                "siren": e.get("siren", ""),
                "siret_siege": siege.get("siret", ""),
                "adresse": siege.get("adresse", ""),
                "code_postal": cp,
                "commune": siege.get("libelle_commune", ""),
                "naf": e.get("activite_principale", ""),
                "effectif": EFFECTIFS.get(e.get("tranche_effectif_salarie") or "", e.get("tranche_effectif_salarie") or ""),
                "cree_le": e.get("date_creation", ""),
                "telephone": "",   # a remplir a la main : absent de l'open data
                "appele_le": "",
                "statut": "",
                "note": "",
            })
            if len(resultats) >= max_resultats:
                break
        page += 1
        time.sleep(0.3)  # courtoisie envers une API publique
    return resultats


def main():
    ap = argparse.ArgumentParser(description="Liste de prospects depuis l'open data officiel.")
    ap.add_argument("--secteur", required=True, choices=sorted(SECTEURS))
    ap.add_argument("--departement", required=True, help="ex. 69, 75, 13")
    ap.add_argument("--effectif", default="01", choices=sorted(EFFECTIFS),
                    help="tranche d'effectif (defaut 01 = 1 a 2 salaries)")
    ap.add_argument("--max", type=int, default=30, help="nombre de prospects vises")
    ap.add_argument("--sortie", default=None, help="fichier CSV (defaut : secteur-departement.csv)")
    args = ap.parse_args()

    sect = SECTEURS[args.secteur]
    sortie = args.sortie or f"prospects-{args.secteur}-{args.departement}.csv"

    print(f"Secteur   : {args.secteur} — {sect['libelle']}")
    print(f"Codes NAF : {', '.join(sect['naf'])}")
    print(f"Zone      : departement {args.departement}")
    print(f"Effectif  : {EFFECTIFS.get(args.effectif, args.effectif)}")
    print()

    vus, fiches = set(), []
    for naf in sect["naf"]:
        reste = args.max - len(fiches)
        if reste <= 0:
            break
        trouve = interroge(naf, args.departement, args.effectif, reste)
        for f in trouve:
            if f["siren"] not in vus:
                vus.add(f["siren"])
                fiches.append(f)
        print(f"  {naf} : {len(trouve)} fiche(s) retenue(s)")

    if not fiches:
        print("\nAucun resultat. Essaie une autre tranche d'effectif ou un autre departement.")
        return 1

    with open(sortie, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fiches[0]))
        w.writeheader()
        w.writerows(fiches)

    print(f"\n{len(fiches)} prospects ecrits dans {sortie}")
    print("Le champ 'telephone' est vide : l'open data ne le publie pas. A completer")
    print("a la main depuis Google Maps ou le site du prospect avant d'appeler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
