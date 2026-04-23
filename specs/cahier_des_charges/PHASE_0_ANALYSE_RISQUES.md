# Phase 0 — Analyse des risques et go/no-go

**Module :** Cahier des charges
**Date :** 23 avril 2026
**Auteur :** Claude Code
**Livrable demandé par :** [00_BRIEF_CLAUDE_CODE.md §4](00_BRIEF_CLAUDE_CODE.md) + [11_ROADMAP.md §2](11_ROADMAP.md)
**Référence décisions :** [12_DIVERGENCES_CAHIER_DES_CHARGES.md](../../12_DIVERGENCES_CAHIER_DES_CHARGES.md)

---

## Question 1 — Les 3 points les plus risqués techniquement

### Risque n°1 — Fiabilité du LLM sur sortie structurée JSON (sévérité : élevée)

La spec prévoit une génération structurée multi-appels : le LLM doit produire un JSON bien formé pour chacune des 11 sections du cahier des charges, avec des contraintes fortes (somme des pourcentages = 100 %, typologie S/P/O/Su respectée, référentiel de verbes recommandés, etc. — cf. [02_STRUCTURE_DOCX.md](02_STRUCTURE_DOCX.md) et [09_PROMPTS_LLM.md §2](09_PROMPTS_LLM.md)).

À température 0.5 ciblée pour ce module (archi globale §4), un Qwen 3.5 9B Q4_K_M peut produire du JSON cassé 5 à 15 % du temps (caractères parasites, accolades non fermées, virgules surnuméraires). Le spec prévoit un "parser JSON tolérant" mais ne précise pas sa politique de retry.

Conséquence si mal traité : mauvaise UX (erreur technique remontée au RH), taux de régénération élevé, perte de temps.

### Risque n°2 — Architecture UX "3 zones + copilote streaming persistant" (sévérité : élevée)

La spec ([04_UX_FLUX.md](04_UX_FLUX.md)) demande une interface très différente du pattern actuel d'Arhiane :

- **Existant** : formulaire (saisie) → preview streaming → boutons d'export. Mono-écran, mono-état. Pattern incarné par le module Certificats (WizardModuleBase = suite d'étapes, une étape à la fois).
- **Demandé** : **3 zones simultanées** = navigation gauche (sections) + édition centrale (richtext éditable par section) + copilote droit (chat persistant avec contexte de la section active). Édition partielle en temps réel, actions contextuelles par section, sauvegarde auto 30 s, streaming de génération LLM dans la zone centrale pendant que le RH édite autre part.

Ce n'est plus un wizard, c'est un éditeur de documents IA-augmenté. Le frontend actuel (PyWebView + HTML/Tailwind + `app.js` vanille, 900 lignes d'API dans [api.py](../../_app/ui/api.py)) n'est pas dimensionné pour ça sans refactor. C'est la part de travail la plus coûteuse du module et la moins linéaire à estimer.

### Risque n°3 — Référentiel factuel suisse et sa maintenance (sévérité : moyenne, coût opérationnel continu)

La spec ([07_CONFORMITE_SUISSE.md](07_CONFORMITE_SUISSE.md)) demande un référentiel embarqué :
- Familles de diplômes suisses + équivalences internationales
- Nomenclature CH-ISCO-08
- CCT étendues par secteur
- Liste ORP/SECO 2026

Ce n'est pas un risque technique pur : c'est un risque de **véracité et de fraîcheur**. Si les checks déterministes citent une CCT qui n'existe plus ou un code CH-ISCO incorrect, le RH perd confiance dans l'outil. La mise à jour annuelle par "pack payant OU par le client" ([00_BRIEF_CLAUDE_CODE.md §5](00_BRIEF_CLAUDE_CODE.md) — synthèse README) n'est pas détaillée techniquement.

Conséquence si mal traité : plus coûteux à maintenir sur la durée que tous les autres risques techniques réunis.

---

## Question 2 — Comment proposes-tu de les aborder ?

### Pour R1 (JSON cassé)

1. **Contrat JSON minimal par appel**. Plutôt qu'un gros appel "génère les 11 sections", découper en ~5 appels ciblés avec un schéma simple chacun (cf. déjà prévu par la spec §3 Orchestration LLM). Probabilité d'erreur par appel × surface réduite.
2. **Parser tolérant en 3 passes** :
   - (a) `json.loads` strict
   - (b) si échec, nettoyage regex des patterns connus (trailing comma, text avant/après le premier `{`, code fences `\`\`\`json`)
   - (c) si échec, retry LLM une fois avec le prompt "ta précédente réponse n'était pas du JSON valide, recommence"
3. **Validation post-parse** (pydantic ou schéma custom) : type des champs, somme % = 100, typologie ∈ {S,P,O,Su}, longueurs bornées. Si invalide → remonte au reviewer 4 passes (cf. [09_PROMPTS_LLM.md §3](09_PROMPTS_LLM.md)) pour correction ciblée.
4. **Benchmark** sur 30 fixtures de tâches vrac en début de Phase 2. Si taux de JSON cassé > 10 % après les 3 mitigations, décision : passer la température à 0.3 et réentraîner le prompt.

### Pour R2 (UX 3 zones)

1. **Ne pas casser le pattern WizardModuleBase existant**. Au lieu de refondre, **créer une seconde classe mère** `EditorModuleBase` dans `_app/core/` qui cohabite avec `WizardModuleBase`. Le frontend (`app.js`) détecte `is_editor: true` dans les meta et route vers une nouvelle vue `editor.html`.
2. **MVP UX en 2 temps** :
   - **V1.0 minimal** : 2 zones (nav gauche + édition centrale). Le copilote de la zone droite est remplacé par une série de boutons d'action contextuelle ("reformuler", "développer", "traduire") — moins ambitieux, 3× plus rapide à construire. Le RH ne perd rien d'essentiel.
   - **V1.1** : ajout de la zone copilote chat persistant quand le reste est stable.
3. **Choix frontend** : rester sur PyWebView + HTML/JS vanille pour la cohérence Arhiane. Pas de framework React/Vue. Utiliser HTMX pour les interactions async (partial reloads de sections) — compatible avec PyWebView, ajoute 14 KB, pas de build step.
4. **Sauvegarde auto** : réutiliser le pattern `DossierStore` existant. Une sauvegarde = un `.json` écrit. Pas de synchro client/serveur, le serveur d'Arhiane est local.

### Pour R3 (référentiel factuel)

1. **Scope V1.0 minimum viable**, pas le corpus complet :
   - Diplômes suisses : **5 familles seulement** (CFC, brevet fédéral, diplôme ES, bachelor HES/EPF, master universitaire). Le reste en V1.5.
   - CH-ISCO-08 : niveau 2 de la nomenclature uniquement (10 grandes classes), pas le niveau 4.
   - CCT étendues : **4-5 CCT** les plus fréquentes en Suisse romande (hôtellerie, construction, horlogerie, nettoyage, commerce de détail). Liste complète = hors scope.
   - Liste ORP : fichier CSV dans `references/liste_orp_2026.csv`, **à charger par le client** la première fois (pas embarqué pour éviter les problèmes de licence SECO).
2. **Format** : JSON plat, commenté, versionné dans le code. `references/diplomes_suisses_v2026-04.json`. Le suffixe date permet au client de savoir si son fichier est à jour.
3. **Mise à jour utilisateur** : dans les Paramètres d'Arhiane, ajouter un onglet "Référentiels" avec, pour chaque fichier, sa date, sa version, et un bouton "Remplacer par…" qui accepte un JSON fourni par Arhiane (côté commercial = pack annuel payant).
4. **Disclaimer systématique** dans l'UI : "Données à jour au [date du fichier]. Vérifier les cas sensibles." Respect de la doctrine Arhiane ("outil d'aide, pas remplaçant").

---

## Question 3 — Dépendances avec le code existant

Bonne nouvelle : le socle Arhiane est déjà riche. Rien ne manque de critique, mais plusieurs pièces doivent être étendues ou adaptées.

### Réutilisables tels quels (zéro modification)

| Composant | Fichier | Usage prévu |
|---|---|---|
| Client LM Studio avec streaming + cancel | [llm_client.py](../../_app/core/llm_client.py) | Génération initiale, self-review, copilote. Le helper `time_generate` alimente l'audit. |
| Config globale | [config.py](../../_app/core/config.py) | Chemins, modèle LM Studio, préférences |
| Logger applicatif | [logger.py](../../_app/core/logger.py) | Journal technique (≠ audit) |
| Garde-fou "local only" | [llm_client._ensure_local](../../_app/core/llm_client.py) | Respect air-gapped |
| Détecteur vocabulaire interdit | [blacklist_detector.py](../../_app/core/blacklist_detector.py) | Check LEg inclusif / vocabulaire discriminatoire |
| Auto-découverte des modules | [module_registry.py](../../_app/core/module_registry.py) | Le module est déjà dans [_catalogue.json](../../_app/modules/_catalogue.json) avec id `cahier_des_charges`, statut "a_venir". Auto-discovery déclenchera quand on posera le fichier `module.py`. |

### À étendre (modifications contenues)

| Composant | Fichier | Extension nécessaire |
|---|---|---|
| Entité | [entity_manager.py](../../_app/core/entity_manager.py) | Ajouter 4 champs à `Entity` + `config.json` : `langue_principale`, `politique_inclusif`, `cct_applicable`, `competences_socles` (cf. [12_DIVERGENCES §divergences mineures](../../12_DIVERGENCES_CAHIER_DES_CHARGES.md)). Migration rétro-compatible (default si absent). |
| Bibliothèque de formulations | [formulation_library.py](../../_app/core/formulation_library.py) | Ajouter un jeu de formulations pour CdC (verbes de mission, compétences socles types). L'architecture est déjà prête à accueillir des catégories supplémentaires. |
| Base de modules | [module_base.py](../../_app/core/module_base.py) | Inchangée, mais introduction d'une **nouvelle classe mère** `EditorModuleBase` (cf. R2) à côté de `WizardModuleBase`. |
| Frontend | [api.py](../../_app/ui/api.py), [web/app.js](../../_app/ui/web/app.js), [web/index.html](../../_app/ui/web/index.html) | Ajout de nouveaux endpoints pour l'éditeur (charger/sauver section, streaming génération section, copilote chat). Nouvelle vue `editor.html`. |

### À créer from scratch (spécifique au module)

- `_app/modules/cahier_des_charges/` : `module.py`, `generator.py`, `reviewer.py`, `checks.py`, `docx_export.py`, `annonces.py`, `catalogue_store.py`, `prompts/*.txt`
- `_app/core/editor_base.py` : la nouvelle classe mère (cohabite avec `WizardModuleBase`)
- `references/` (racine projet) : fichiers JSON du référentiel factuel suisse
- `Templates/cahier_des_charges.docx`, `Templates/annonce_classique.docx`, etc. : 5 templates Word
- Tests dans `tests/cahier_des_charges/`

### Pas de dépendance manquante

La stack actuelle couvre tous les besoins. Pas de nouvelle dépendance Python majeure à introduire (python-docx est déjà dans l'écosystème Arhiane, reportlab aussi). HTMX (optionnel pour R2) = un fichier JS de 14 KB.

---

## Synthèse et recommandations

**Go recommandé**, avec 3 conditions :

1. **Les 3 décisions de divergence sont signées** (Qwen 3.5 9B, un seul modèle, persistance JSON). 3/3 déjà validées par Guillaume.
2. **Scope découpé en V1.0 minimal puis V1.1** :
   - **V1.0** (~2-3 semaines) : 11 sections + 1 format d'annonce (Classique) + checks déterministes + UI 2 zones + catalogue basique. Pas de copilote chat, pas de self-review LLM.
   - **V1.1** (~2-3 semaines) : self-review LLM + 3 autres formats d'annonce + copilote chat zone droite + versioning avancé.
   Total : 4-6 semaines (conforme à l'estimation spec) mais livrable utilisable à mi-parcours.
3. **Checkpoint intermédiaire** : démo interne après V1.0 avant d'engager V1.1. Permet de réorienter si l'UX 2 zones s'avère déjà suffisante pour le client pilote.

## Actions pour entrer en Phase 1

Ces 3 items ne bloquent pas la Phase 0 (déjà livrée par ce document) mais bloquent l'écriture du premier fichier Python du module :

- [ ] **Valider le découpage V1.0 / V1.1** proposé ci-dessus avec Guillaume.
- [ ] **Lancer Arhiane + LM Studio + Qwen 3.5 9B** sur le poste de dev, vérifier qu'une génération simple (via le module Certificats ou un script de test) fonctionne. *Non faisable par Claude Code, action utilisateur.*
- [ ] **Étendre `config.json` d'entité** avec les 4 champs (langue, inclusif, CCT, compétences socles). 1 h de travail max.

Une fois ces 3 points traités, Phase 1 (Backend et persistance) peut démarrer directement sur la base fichier JSON définie au [12_DIVERGENCES §3](../../12_DIVERGENCES_CAHIER_DES_CHARGES.md).
