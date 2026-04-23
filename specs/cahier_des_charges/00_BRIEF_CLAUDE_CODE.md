# Brief pour Claude Code — Module "Cahier des charges" d'Arhiane

**Version** : 1.0 — Avril 2026
**Destinataire** : Claude Code (ou autre développeur)
**Ce fichier est le PREMIER à lire.** Il donne la vue d'ensemble et l'ordre de travail.

---

## 1. Ta mission en une phrase

Développer un nouveau module d'Arhiane appelé **"Cahier des charges"**, qui permet à un responsable RH de PME suisse romande de transformer une liste de tâches en vrac en un cahier des charges structuré au format .docx, puis de générer 4 variantes d'annonce d'emploi à partir de ce document, le tout en mode local air-gapped avec LLM embarqué.

Ce module s'ajoute au produit Arhiane existant (dont tu as déjà les specs et qui inclut déjà les modules Consultation documentaire juridique et Certificat de travail). Il utilise la même stack, la même architecture, les mêmes principes de souveraineté et de confidentialité.

---

## 2. Positionnement produit — à respecter impérativement

Arhiane est positionné comme une **boîte à outils RH** pour PME suisses. Ce module s'inscrit dans ce positionnement :

- **Ce n'est PAS un SIRH.** Pas de base de données employés, pas de synchronisation inter-modules, pas de workflow collaboratif multi-utilisateurs.
- **Ce n'est PAS un générateur d'annonces type ChatGPT.** La valeur ajoutée est l'ancrage suisse romand : terminologie officielle ("cahier des charges"), structure des modèles Vaud/Genève/Fribourg, conformité ORP/LEg, référentiels suisses.
- **Ce n'est PAS un outil de conseil juridique.** Les disclaimers d'Arhiane s'appliquent : "outil d'aide à la décision, vérifier avec un avocat pour cas sensibles".

Le terme à utiliser partout dans l'interface et la documentation : **"cahier des charges"** (jamais "fiche de poste" qui est français). Synonyme accessible : "fiche de fonction".

---

## 3. Règles d'autonomie — ce que tu peux décider seul vs valider avec moi

### Tu peux décider seul
- Choix techniques d'implémentation (structure des classes, patterns, librairies mineures) tant qu'ils respectent la stack Arhiane déjà définie
- Organisation interne du code (arborescence de fichiers, découpage en modules, tests unitaires)
- Nommage interne des variables, fonctions, classes (reste cohérent avec l'existant Arhiane)
- Optimisations de performance qui ne changent pas le comportement fonctionnel
- Choix de formulation des messages d'interface secondaires (tooltips, placeholder, infobulles) — mais respecte le ton défini dans les specs
- Choix de librairies mineures (utilitaires de formatage, helpers) si nécessaires

### Tu dois valider avec moi avant de coder
- Toute modification du scope fonctionnel défini dans les specs (ajouter/retirer une fonctionnalité)
- Tout changement de la structure du cahier des charges .docx (les 11 sections sont figées)
- Tout changement de la logique des 4 formats d'annonce
- Toute intégration avec d'autres modules Arhiane non prévue dans 08_INTEGRATION_ARHIANE.md
- Tout ajout de dépendance externe majeure
- Toute modification des prompts système du LLM (ils sont sensibles, validés en amont)
- Tout écart au positionnement produit ("boîte à outils RH, pas SIRH, pas assistant juridique")

### En cas de doute
Demande. Les specs sont le fruit d'un brainstorming approfondi avec l'utilisateur, elles incarnent des arbitrages réfléchis. Ne présume pas "ce qu'il voulait dire vraiment" — confirme.

---

## 4. Avant de commencer à coder

**Réponds à ces 3 questions dans ta première réponse après avoir lu ce dossier :**

1. Quels sont les 3 points les plus risqués techniquement dans ce module, selon ton analyse ?
2. Comment proposes-tu de les aborder ?
3. Quelles dépendances as-tu avec le code existant d'Arhiane, et as-tu besoin d'accès à du code existant pour démarrer ?

Cette analyse initiale nous permettra de valider ton approche avant que tu investisses du temps.

---

## 5. Ordre de lecture recommandé du dossier

```
00_BRIEF_CLAUDE_CODE.md          ← Tu es ici. Vue d'ensemble, règles de travail.
01_SPEC_FONCTIONNEL.md           Spec principal, vue d'ensemble du module.
02_STRUCTURE_DOCX.md             Détail de la structure du cahier des charges .docx (11 sections).
03_FORMATS_ANNONCES.md           Les 4 formats d'annonce, spécifications et exemples.
04_UX_FLUX.md                    Flux utilisateur en 8 phases, architecture 3 zones.
05_CATALOGUE_POSTES.md           Persistance, versioning, recherche, archivage.
06_GARDE_FOUS_QUALITE.md         Self-review LLM + checks déterministes + benchmark.
07_CONFORMITE_SUISSE.md          ORP, LEg, CCT, référentiel factuel, équivalences diplômes.
08_INTEGRATION_ARHIANE.md        Référentiel entité, journal d'audit, contraintes transverses.
09_PROMPTS_LLM.md                Prompts système pour génération, self-review, reformulation.
10_JEUX_DE_TESTS.md              Scénarios de tests, cas d'acceptation.
11_ROADMAP.md                    Jalons, ordre de travail, livrables attendus.
```

Lis dans l'ordre. Chaque fichier se réfère aux suivants uniquement en renvoi, pas en dépendance. Tu peux toujours y revenir.

---

## 6. Contraintes techniques héritées d'Arhiane (rappel)

- **Stack** : Python 3.11+ (backend), HTML/CSS/JS vanille ou HTMX/Alpine.js (frontend), conforme au spec Arhiane V1
- **LLM** : intégration via LM Studio, modèle principal Qwen 3.5 9B en Q4_K_M
- **LLM auxiliaire** (nouveau pour ce module) : modèle léger ~3B (Qwen 3B ou Phi 3.5) pour self-review, à charger/décharger à la demande pour économiser la VRAM
- **Base de données locale** : SQLite pour les données structurées (catalogue postes, versions, journal d'audit)
- **Génération .docx** : python-docx
- **Génération .pdf** : reportlab ou weasyprint (aligner avec l'existant Arhiane)
- **Mode air-gapped** : aucun appel réseau sortant, aucune dépendance à un service cloud
- **Multi-entité** : le module respecte le référentiel d'entité d'Arhiane, pas de mélange entre entités
- **Journalisation audit** : le module écrit dans le journal d'audit commun

---

## 7. Ce qui est dans le scope V1 vs reporté

### Scope V1 (à livrer)
- Module fonctionnel complet "Cahier des charges" avec les 11 sections
- Génération des 4 formats d'annonce
- Flux UX 8 phases complet avec architecture 3 zones
- Catalogue de postes par entité avec versioning, archivage, recherche, duplication
- Self-review LLM optionnel avec benchmark machine
- Checks déterministes (cohérence, ORP, LEg, CCT)
- Référentiel factuel minimal (familles titres suisses, équivalences internationales, CCT, CH-ISCO-08)
- Intégration référentiel d'entité Arhiane (lecture seule)
- Journalisation audit

### Hors scope V1 (reporté V1.5 ou V2)
- Lien synchronisé avec module Certificat de travail (abandonné, copier-coller si besoin)
- Bascule contextuelle vers module Consultation juridique
- Copilote Arhiane global transverse
- Vérificateur LEg/inclusif exposé comme service transverse (reste interne au module en V1)
- Mode "expert" avec désactivation de garde-fous
- Signature électronique
- Organigramme visuel automatique
- Matrice de compétences transverse
- Détection automatique de doublons de postes
- Workflow d'approbation multi-étapes

---

## 8. Livrables attendus à la fin

### Code source complet
Arborescence proposée (à valider avec l'existant Arhiane) :
```
arhiane/
├── modules/
│   ├── cahier_des_charges/
│   │   ├── __init__.py
│   │   ├── models.py              # Modèles de données
│   │   ├── routes.py              # Endpoints HTTP du module
│   │   ├── generator.py           # Génération LLM
│   │   ├── reviewer.py            # Self-review LLM
│   │   ├── checks.py              # Checks déterministes
│   │   ├── docx_export.py         # Export .docx
│   │   ├── annonces.py            # Génération 4 formats d'annonce
│   │   ├── catalogue.py           # Gestion catalogue postes
│   │   ├── prompts/               # Dossier des prompts LLM
│   │   ├── templates/             # Templates HTML de l'UI
│   │   └── static/                # CSS, JS
│   └── ...
├── references/
│   ├── diplomes_suisses.json      # Référentiel familles titres
│   ├── equivalences_international.json
│   ├── ch_isco_08.json            # Nomenclature professions
│   ├── cct_etendues.json          # CCT étendues par secteur
│   └── liste_orp_2026.csv         # Liste SECO (chargée client)
└── tests/
    └── cahier_des_charges/
        ├── test_generator.py
        ├── test_checks.py
        ├── test_docx_export.py
        ├── test_integration.py
        └── fixtures/              # Jeux de test
```

### Documentation technique
- README du module avec instructions d'utilisation
- Documentation des endpoints HTTP (format OpenAPI ou markdown)
- Documentation de la structure des prompts LLM
- Procédure de mise à jour de la liste SECO par l'utilisateur final (déjà brouillon, à finaliser)

### Tests
- Tests unitaires sur les checks déterministes (100 % de couverture sur cette partie)
- Tests d'intégration sur les flux principaux (création from scratch, import fiche existante, export)
- Suite de 10 à 15 scénarios de test end-to-end documentés (voir 10_JEUX_DE_TESTS.md)

---

## 9. Ton de la communication avec moi

- Sois direct. Si quelque chose me semble mal spécifié, dis-le.
- Si tu identifies une incohérence entre deux fichiers du dossier, signale-le avant de coder.
- Si tu penses qu'une décision est sous-optimale, propose une alternative avec les tradeoffs.
- Pas de flatterie, pas de "excellente question", juste de l'analyse.
- En cas de blocage, propose 2-3 options plutôt qu'une seule.

---

## 10. Question posée en fin de BRIEF

Après ta lecture du dossier complet, **réponds aux 3 questions du §4** avant de commencer à coder. Je validerai ton approche puis tu pourras démarrer.

Bonne construction.
