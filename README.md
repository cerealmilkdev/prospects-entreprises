# prospects-entreprises

## Ce que fait l'outil

Un petit script Python qui construit une liste d'entreprises françaises à contacter, à partir d'un secteur d'activité, d'un département et d'une taille d'entreprise. Il écrit le résultat dans un fichier CSV prêt à ouvrir dans un tableur.

## La source

Les données viennent de l'[API Recherche d'entreprises](https://recherche-entreprises.api.gouv.fr), une donnée ouverte officielle de l'État français : pas de clé d'API, pas de limite commerciale. Le script ne dépend que de la bibliothèque standard de Python.

## Pourquoi pas du scraping

C'est la même information qu'un scraper irait chercher, mais obtenue de façon légale, stable, et sans conditions d'utilisation à violer.

## Installation et usage

Python 3 suffit, il n'y a aucune dépendance à installer.

```bash
git clone https://github.com/cerealmilkdev/prospects-entreprises.git
cd prospects-entreprises
python3 prospects.py --secteur depannage --departement 69 --effectif 01 --max 30
```

Options :

| Option | Rôle | Défaut |
|---|---|---|
| `--secteur` | secteur cible (voir la liste ci-dessous) | obligatoire |
| `--departement` | numéro de département, ex. `69`, `75`, `13` | obligatoire |
| `--effectif` | tranche d'effectif INSEE : `00` (0 salarié), `01` (1 à 2), `02` (3 à 5), `03` (6 à 9), `11` (10 à 19) | `01` |
| `--max` | nombre de fiches visées | `30` |
| `--sortie` | nom du fichier CSV | `prospects-<secteur>-<departement>.csv` |

Exemple complet :

```bash
python3 prospects.py --secteur dental --departement 75 --max 50 --sortie dental75.csv
```

Colonnes du CSV : `raison_sociale`, `siren`, `siret_siege`, `adresse`, `code_postal`, `commune`, `naf`, `effectif`, `cree_le`, `telephone`, `appele_le`, `statut`, `note`. Les quatre dernières sont vides : elles servent à suivre vos appels.

Les fichiers CSV produits contiennent des entreprises réelles ; ils sont exclus du dépôt par le `.gitignore`.

## Les secteurs disponibles

| Clé | Libellé |
|---|---|
| `depannage` | plomberie, chauffage-clim, électricité |
| `dental` | chirurgie dentaire |
| `medical` | médecine de ville |
| `veterinaire` | vétérinaires |
| `immobilier` | agences immobilières |
| `garage` | entretien et réparation auto |
| `comptable` | expertise comptable |
| `avocat` | activités juridiques |
| `btp` | menuiserie, plâtrerie, charpente |

Les secteurs sont définis par des codes NAF dans le dictionnaire `SECTEURS` de `prospects.py` ; on peut en ajouter.

## Les deux limites mesurées

1. **Pas de téléphone ni d'e-mail.** L'API ne publie ni l'un ni l'autre. Le script écrit donc une colonne `telephone` vide ; le numéro se récupère ensuite ailleurs (site de l'entreprise, carte en ligne, annuaire).
2. **Le filtre `departement` de l'API porte sur les établissements, pas sur les sièges.** Un siège peut donc se trouver hors de la zone demandée. Le script ajoute un post-filtrage : il ne garde que les entreprises dont le code postal du siège commence par le numéro du département.

## Licence

MIT — voir [LICENSE](LICENSE).
