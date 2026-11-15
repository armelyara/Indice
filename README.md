<p align="center">
  <img src="https://raw.githubusercontent.com/armelyara/Indice/main/indice/static/indice_logo.png" alt="Indice" width="180">
</p>

<h1 align="center">Indice</h1>

<p align="center">
  <a href="https://pypi.org/project/indice/"><img src="https://img.shields.io/pypi/v/indice.svg" alt="PyPI"></a>
</p>


Indice analyse des **sources texte et audio** pour mener une investigation : il extrait les entités d'intérêt, les corrèle, bâtit un graphe et une chronologie, flague les signaux et aide à monter un **dossier d'enquête ou de recherche**

Trois domaines (packs de connaissances) : **cybersécurité (CTI)**, **justice / Journalisme**, **santé / biomédical / pharmacovigilance**.

## Fonctions clés
- **INTERCEPT** — écoute micro en direct (FR/EN auto, transcription faster-whisper, VAD énergétique), flags et flèches en temps réel, modal d'alerte.
- **ANALYSE** — dépôt de fichiers (PDF / DOCX / images OCR / audio) → extraction → corrélation → rapport.
- **DOSSIER** — monte un dossier autour d'un sujet : **recherche web** (opt-in) → résultats **cochables** → téléchargement dans le dossier → **juxtaposition avant/maintenant** datée et sourcée → **export Markdown / PDF**.
- **Rapport déterministe** — ce qui ressort, qui est lié à qui, chronologie, flags, passages-clés **sourcés**.

## Extraction ouverte
- **Sélecteurs génériques** (sans lexique) : e-mail, téléphone, IP, URL, @pseudo, montants/FCFA, dates, coordonnées GPS, CVE, IBAN.
- **NER spaCy** : PERSON / ORG / LIEU / DATE / MONEY, même pour des entités jamais listées. Repli propre si le modèle est absent.
- **Watchlist utilisateur** : le sujet / les sélecteurs saisis pilotent flags, priorité et alertes.
- Les packs de domaine (`profiles/*.json`) apportent une connaissance métier **optionnelle**, jamais la condition d'entrée.

## Flag (par type, puis par sujet)
Toute **entité détectée** (personne, organisation, lieu, montant, GPS, IBAN, CVE, arme/violence…) est flaguée automatiquement → flèche vers la matrice. Le **sujet déclaré** (watchlist) ajoute une couche de **priorité** et déclenche le **modal d'alerte URGENT**.

## Architecture
| Fichier | Rôle |
|---|---|
| `indice_core.py` | moteur : extraction (sélecteurs + lexique + NER) → corrélation → hypothèses/lock → alertes → timeline |
| `packs.py` | charge et fusionne les packs de domaine sélectionnés |
| `server.py` | FastAPI : auth, WebSocket d'analyse, sessions, **dossiers**, **recherche web**, **export** |
| `cli.py` | commande `indice` : `serve` (interface) et `analyze` (ligne de commande) |
| `audio_transcriber.py` | transcription micro / fichier (faster-whisper, VAD énergétique, hors boucle asyncio) |
| `doc_ingest.py` | extraction de texte PDF (PyMuPDF) / DOCX / images (OCR RapidOCR) |
| `dossiers.py` | store local des dossiers d'enquête (fichiers, hors-ligne) |
| `web_collect.py` | collecte web **opt-in** (Exa / Tavily) — presse, archives |
| `dossier_analyze.py` | juxtaposition avant/maintenant + entités sur les sources d'un dossier |
| `dossier_export.py` | export d'un dossier en Markdown / PDF |
| `db.py` | persistance SQLite (sessions, réglages) |
| `auth.py` | gate par token (démo-grade — à remplacer en production) |
| `static/index.html` | interface : INTERCEPT · ANALYSE · REPORT · DOSSIER · ARCHIVE · CONFIG |
| `profiles/*.json` | packs de connaissances par domaine |

## Structure du projet
```
Indice/
├── indice/              # package installable (pip)
│   ├── server.py        # FastAPI — point d'entrée : indice.server:app
│   ├── cli.py           # commande `indice` (serve / analyze)
│   ├── indice_core.py   # moteur ; + packs, dossiers, web_collect, dossier_analyze/export, db, auth…
│   ├── static/          # interface web + logo (servis par le serveur)
│   ├── profiles/        # packs de domaine (cybersécurité / investigation / santé)
│   └── config.json      # auth, pipeline, réglages par défaut
├── pyproject.toml       # métadonnées + dépendances (installable)
├── requirements.txt
├── LICENSE · NOTICE
└── README.md
```
Données d'exécution créées dans le dossier courant, non versionnées : `uploads/`, `dossiers/`, `indice.db`.

## Lancer
```bash
# Installation
pip install indice
# extras optionnels : audio (micro), OCR, NER
pip install "indice[audio,ocr,ner]"

# Interface web
indice serve --open                 # ouvre http://127.0.0.1:8000

# Ligne de commande, sans interface
indice analyze mon_dossier/ --subject "nom, mot-clé" --format md --out dossier.md
```
Recherche web (optionnelle, une clé suffit) :
```bash
INDICE_WEB=1 EXA_API_KEY=... indice serve
# ou TAVILY_API_KEY=...
```
Les **modèles** (Whisper, OCR RapidOCR, spaCy) ne sont **pas inclus** dans le dépôt : ils sont téléchargés / servis côté serveur. Le code reste utilisable tel quel.

## Auteur & licence
Développé par **The Day Info**. Open source sous licence **Apache-2.0** (voir [`LICENSE`](LICENSE) et [`NOTICE`](NOTICE)) — libre de télécharger, utiliser, modifier et redistribuer, avec clause de brevet.
