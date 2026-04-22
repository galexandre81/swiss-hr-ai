# ARHIANE — L'IA qui remet les RH au centre

Boîte à outils RH pour PME suisses, fonctionnant **100 % en local** via LM Studio.
Zéro cloud, conformité LPD, expertise juridique helvétique (CO, LTr, CCT).

> **Statut actuel :** Phase 0 — socle applicatif + interface générale durcis
> (CSP, audit LPD minimal, dark mode, wizard, tests, CI).
> Les 10 modules métier sont présentés comme "À venir" dans le dashboard
> et seront implémentés un par un à partir de la Phase 1 (Certificats en premier).

---

## Prérequis (poste utilisateur)

1. **Windows 10/11** (macOS et Linux fonctionnent pour le dev).
2. **[LM Studio](https://lmstudio.ai/)** installé, avec un modèle GGUF chargé
   (cible recommandée : **Qwen 3 8B Instruct Q4_K_M**).
3. **Python 3.11+** (uniquement en mode développement ; inutile après packaging `.exe`).

## Installation (mode développement)

```bash
git clone <URL-de-votre-repo-prive>.git "ARHIANE"
cd "ARHIANE"

python -m venv .venv
.venv\Scripts\activate          # (Windows)   source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pour tester / linter
```

## Lancement

1. Ouvrez LM Studio, chargez un modèle, puis **Start Server** (onglet Developer).
2. Double-cliquez sur **`ARHIANE.bat`** (Windows) ou lancez `python run.py`.

Vérifier uniquement la connexion à LM Studio (sans ouvrir la fenêtre) :

```bash
python run.py --check
```

Lancer les tests et le linter en local :

```bash
ruff check .
pytest
```

---

## Architecture (résumé)

```
ARHIANE/
├── _app/                  ← code : core/ (socle), modules/ (outils RH), ui/ (PyWebView)
├── Base_Juridique/        ← PDFs CO, LTr, CCT (éditable utilisateur)
├── Templates/             ← modèles Word (éditable utilisateur)
├── Entities/              ← une société = un sous-dossier (logo, signature, config.json)
├── Outputs/               ← documents générés horodatés
├── Logs/                  ← journal auditable LPD (JSONL)
├── data/                  ← index vectoriel ChromaDB (régénérable)
├── tests/                 ← suite pytest du socle
├── config.json            ← réglages globaux + préférences utilisateur
├── pyproject.toml         ← config ruff + pytest
├── requirements.txt       ← dépendances d'exécution
├── requirements-dev.txt   ← dépendances de dev (pytest, ruff)
├── run.py                 ← point d'entrée
└── ARHIANE.bat            ← lanceur Windows
```

Voir `00_ARCHITECTURE_GLOBALE.md` pour la documentation détaillée.

## Sécurité & conformité

- **Air-gapped** : le `LLMClient` refuse au démarrage toute URL non-locale
  (`localhost`, `127.0.0.1`, `::1`). La `Content-Security-Policy` de l'UI
  interdit toute connexion sortante et toute ressource externe.
- **Auditabilité** : chaque appel IA est logué dans
  `Logs/audit_YYYY-MM-DD.jsonl` (événement `llm_call` avec module, entité,
  température, durée, hash du prompt/réponse). Le contenu intégral n'est
  stocké que si l'administrateur active explicitement
  `audit_log_prompts: true` dans `config.json` (accord DPO recommandé).
- **Validation des chemins** : tout accès disque exposé au frontend passe
  par `safe_within()` (refus des traversées `../..` ou des liens symboliques
  hors de la racine projet).
- **Grounding** : les modules juridiques afficheront le passage source
  avant la réponse (à brancher en Phase 2 via `rag_engine`).
- **Températures** : 0.1 pour les modules factuels/juridiques, 0.7 pour les créatifs.

## Expérience utilisateur

- **Premier lancement** : si aucune entité n'existe, un wizard demande les
  informations de la première société (nom, forme juridique, adresse,
  signataire). Logo et signature se déposent ensuite dans son dossier.
- **Thème** : clair / sombre / automatique (suit le système).
  Bouton dans le header + réglage persistant dans les paramètres.
- **Toasts** : messages contextuels non-bloquants pour confirmations,
  alertes LPD et erreurs — plus d'alertes navigateur.
- **A11y** : focus trap sur les modales, navigation clavier du sélecteur
  d'entité, `aria-live` sur la barre de statut, respect de
  `prefers-reduced-motion`.
- **Streaming** : infrastructure prête — les modules peuvent pousser des
  tokens au fil de l'eau vers l'UI (`ctx.extras["emit"](chunk)`).

## Ajouter un module

1. Créer un dossier `_app/modules/<id>/` avec un fichier `module.py`.
2. Définir une classe `Module(ModuleBase)` avec métadonnées + `inputs_schema()` + `run()`.
3. Redémarrer l'application : le dashboard détecte le module automatiquement.

## Qualité logicielle

- **Tests** : `pytest` — suite du socle (config, paths, entities, logger,
  llm_client, module_registry). Fixture `sandbox` qui isole chaque test
  dans un bac à sable.
- **Lint** : `ruff` (ensemble E/W/F/I/B/UP), configuré dans `pyproject.toml`.
- **CI** : GitHub Actions (`.github/workflows/ci.yml`) exécute ruff + pytest
  sur Python 3.11 et 3.12 à chaque push / PR.

## Licence / confidentialité

Projet privé — usage interne Gates Solutions.
