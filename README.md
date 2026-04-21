# Swiss HR Local AI Toolbox

Boîte à outils RH pour PME suisses, fonctionnant **100 % en local** via LM Studio.
Zéro cloud, conformité LPD, expertise juridique helvétique (CO, LTr, CCT).

> **Statut actuel :** Phase 0 — socle applicatif et interface générale.
> Les 10 modules métier sont présentés comme "À venir" dans le dashboard
> et seront implémentés un par un à partir de la Phase 1.

---

## Prérequis (poste utilisateur)

1. **Windows 10/11** (macOS et Linux fonctionnent aussi pour le dev).
2. **[LM Studio](https://lmstudio.ai/)** installé, avec le modèle
   **Qwen 3.5 9B** (version quantifiée GGUF) chargé.
3. **Python 3.11+** (uniquement en mode développement ; inutile après packaging `.exe`).

## Installation (mode développement)

```bash
git clone <URL-de-votre-repo-prive>.git "Swiss HR AI"
cd "Swiss HR AI"

python -m venv .venv
.venv\Scripts\activate          # (Windows)   source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
```

## Lancement

1. Ouvrez LM Studio, chargez le modèle, puis **Start Server** dans l'onglet Developer.
2. Double-cliquez sur **`SwissHR.bat`** (Windows) ou lancez `python run.py`.

Pour tester uniquement la connexion à LM Studio sans ouvrir la fenêtre :

```bash
python run.py --check
```

---

## Architecture (résumé)

```
Swiss HR AI/
├── _app/                  ← code : core/ (socle), modules/ (outils RH), ui/ (PyWebView)
├── Base_Juridique/        ← PDFs CO, LTr, CCT (éditable utilisateur)
├── Templates/             ← modèles Word (éditable utilisateur)
├── Entities/              ← une société = un sous-dossier (logo, signature, config.json)
├── Outputs/               ← documents générés horodatés
├── Logs/                  ← journal auditable LPD (JSONL)
├── data/                  ← index vectoriel ChromaDB (régénérable)
├── config.json            ← réglages globaux
├── run.py                 ← point d'entrée
└── SwissHR.bat            ← lanceur Windows
```

Voir `00_ARCHITECTURE_GLOBALE.md` pour la documentation détaillée.

## Sécurité & conformité

- **Air-gapped** : aucune requête sortante. Tout trafic reste sur `127.0.0.1`.
- **Auditabilité** : chaque interaction avec l'IA est loguée dans `Logs/audit_YYYY-MM-DD.jsonl`.
- **Grounding** : les modules juridiques afficheront le passage source avant la réponse.
- **Température** : 0.1 pour les modules factuels/juridiques, 0.7 pour les créatifs.

## Ajouter un module

1. Créer un dossier `_app/modules/<id>/` avec un fichier `module.py`.
2. Définir une classe `Module(ModuleBase)` avec métadonnées + `inputs_schema()` + `run()`.
3. Redémarrer l'application : le dashboard détecte le module automatiquement.

## Licence / confidentialité

Projet privé — usage interne Gates Solutions.
