# 11 — Roadmap de développement

Plan de travail pour livrer le module "Cahier des charges" en autonomie. Estimation : **4 à 6 semaines ETP** pour un développeur Python senior familier avec le stack Arhiane.

---

## 1. Découpage en 7 phases

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Phase 0  │──▶│ Phase 1  │──▶│ Phase 2  │──▶│ Phase 3  │──▶│ Phase 4  │──▶│ Phase 5  │──▶│ Phase 6  │
│          │   │          │   │          │   │          │   │          │   │          │   │          │
│ Setup &  │   │ Backend  │   │ LLM &    │   │ Frontend │   │ Qualité  │   │ Intégr.  │   │ Livraison│
│ analyse  │   │ & persist│   │ prompts  │   │ & UX     │   │ & checks │   │ Arhiane  │   │ & tests  │
│          │   │          │   │          │   │          │   │          │   │          │   │          │
│ 2-3 jours│   │ 4-5 jours│   │ 3-4 jours│   │ 6-8 jours│   │ 3-4 jours│   │ 2-3 jours│   │ 3-4 jours│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

**Durée totale** : ~23-31 jours ETP (4-6 semaines calendaires en tenant compte des revues, retours utilisateur, itérations).

---

## 2. Phase 0 — Setup et analyse (2-3 jours)

### Objectifs
- Comprendre le projet Arhiane existant
- Valider la compatibilité technique
- Lever les incertitudes avant de coder

### Tâches
1. Lecture exhaustive du dossier de spécifications (ce dossier)
2. Lecture du code source Arhiane existant (structure, conventions, patterns)
3. Test du stack en local : lancement Arhiane, LM Studio, génération simple avec Qwen 3.5 9B
4. Identification du modèle léger à utiliser pour self-review (tester Qwen 3B, Phi 3.5 mini, décider)
5. Réponse aux **3 questions du brief** (00_BRIEF_CLAUDE_CODE §4) :
   - Points techniques les plus risqués
   - Approche proposée pour les lever
   - Dépendances au code existant
6. Validation de l'approche avec l'utilisateur avant de coder

### Livrables
- Document court (1-2 pages) : analyse des risques + approche + dépendances
- Environnement de dev local opérationnel
- Go/no-go validé par l'utilisateur

### Critères de sortie
- Les 3 questions sont répondues par écrit
- L'utilisateur a validé l'approche
- L'environnement local fonctionne (Arhiane + LM Studio + au moins une génération LLM de test)

---

## 3. Phase 1 — Backend et persistance (4-5 jours)

### Objectifs
- Modèle de données complet
- API interne du module
- Tests unitaires sur la logique métier

### Tâches

**Jour 1-2** : Modèles et DB
- Création des tables SQLite (schéma en 05_CATALOGUE_POSTES.md §2)
- Migration Alembic ou équivalent (cohérent avec Arhiane)
- Classes de modèles Python (SQLAlchemy / Pydantic selon conventions Arhiane)
- Repository pattern avec injection `entite_id` (voir 08_INTEGRATION_ARHIANE.md §4.3)

**Jour 3** : Logique métier catalogue
- CRUD complet (create, read, update, delete soft, restore, archive)
- Versioning (changement mineur v1.0 → v1.1 vs majeur v1.0 → v2.0)
- Duplication
- Corbeille 30 jours + job de nettoyage
- Recherche full-text

**Jour 4** : Endpoints HTTP
- Endpoints REST ou HTMX (selon conventions Arhiane) pour le catalogue
- Endpoints pour création/édition CdC
- Endpoints pour génération LLM (à stuber pour l'instant)
- Endpoints pour export .docx/.pdf (à stuber pour l'instant)

**Jour 5** : Tests unitaires backend
- 100 % de couverture sur les repositories
- 100 % de couverture sur les services métier
- Tests d'intégration DB (création → lecture → mise à jour → suppression → restauration)

### Livrables
- Module `arhiane/modules/cahier_des_charges/` avec structure définie en 00_BRIEF §8
- Tests unitaires verts (> 80 % couverture globale, 100 % sur checks)
- README technique du module (très court)

### Critères de sortie
- CRUD fonctionnel en ligne de commande (via Python REPL ou script de test)
- Tests passent
- Pas d'intégration UI ni LLM à cette étape (les stubs renvoient des données fixtures)

---

## 4. Phase 2 — LLM et prompts (3-4 jours)

### Objectifs
- Orchestration LLM opérationnelle
- Prompts système implémentés et testés
- Benchmark machine au premier lancement

### Tâches

**Jour 1** : Intégration LM Studio
- Client HTTP pour LM Studio (cohérent avec Arhiane existant)
- Gestion erreurs (timeout, indisponibilité, output malformé)
- Retry automatique (1 tentative)
- Loggings des appels LLM

**Jour 2** : Prompts de génération principale
- Implémentation du Prompt 1 (génération structurée initiale) — voir 09_PROMPTS_LLM §2
- Templating simple avec variables
- Parser JSON tolérant avec validations (somme pourcentages, typologie)
- Tests sur 5 fixtures de texte vrac → vérification JSON produit

**Jour 3** : Prompts de self-review
- Implémentation des 4 passes (09_PROMPTS_LLM §3)
- Orchestration séquentielle avec interruption possible
- Chargement/déchargement du modèle léger si contrainte VRAM
- Tests sur 5 fixtures de CdC → vérification alertes produites

**Jour 4** : Prompts actions contextuelles et copilote
- Prompts 3-7 (09_PROMPTS_LLM §4)
- Intégration chat conversationnel avec contexte persistant
- Benchmark machine au premier lancement + affinage moyenne glissante

### Livrables
- Couche LLM opérationnelle avec tous les prompts
- Tests d'intégration avec LLM réel passant sur fixtures
- Messages adaptatifs selon benchmark machine

### Critères de sortie
- Génération initiale < 60s sur PC standard
- Self-review complet < 90s
- Benchmark machine mesure correctement

---

## 5. Phase 3 — Frontend et UX (6-8 jours)

### Objectifs
- Flux UX complet en 8 phases fonctionnel
- Architecture 3 zones opérationnelle en phase 5

### Tâches

**Jour 1** : Phase 1 et 2 (modal entrée + cadrage)
- Modal 3 cartes en page d'accueil du module
- Écran de cadrage avec 5 questions
- Routing vers phases suivantes selon choix utilisateur

**Jour 2-3** : Phase 3 (capture inputs)
- Sous-flux A : texte vrac + contexte additionnel
- Sous-flux B : import de fichier (.docx, .pdf, .txt, .odt)
- Parseurs de documents (python-docx, pypdf ou pdfminer)
- Écran d'analyse après import avec 3 options (utiliser / rafraîchir / restructurer)

**Jour 4** : Phase 4 (structuration assistée)
- Écran de progression avec barre + étapes
- Intégration avec l'appel Prompt 1
- Gestion des erreurs avec fallback

**Jour 5-6** : Phase 5 (édition 3 zones) — **cœur du travail**
- Layout 3 zones (navigation gauche / édition centrale / copilote droite)
- Navigation non-linéaire entre sections
- Édition inline avec auto-save 30s
- Actions par bloc (🔄 ✂️ 📝 🎯 🗑️)
- Chat copilote avec historique
- Palette contextuelle par section
- Diff visuels pour propositions LLM
- Toggle "Non applicable" pour sections 5, 6, 10
- Bascule preview .docx

**Jour 7** : Phase 6, 7, 8 (checks, annonces, export)
- Écran checks déterministes + self-review
- Proposition de relecture LLM adaptative selon benchmark
- Écran de synthèse d'alertes
- Grille 2×2 de génération d'annonces
- Édition fine par format
- Écran d'export final
- Téléchargement zip

**Jour 8** : Catalogue et finitions UX
- Écran catalogue (liste + filtres + vue regroupée)
- Page historique versions
- Page comparaison côte à côte
- Page corbeille
- Paramètres module au niveau entité

### Livrables
- Frontend complet cohérent avec Arhiane (HTMX/Alpine ou framework existant)
- Responsive 1366-1920
- Navigation clavier complète

### Critères de sortie
- Scénario T1 (création from scratch happy path) passe manuellement de bout en bout
- Sauvegarde auto 30s fonctionne
- Aucune perte de données possible en rechargement de page

---

## 6. Phase 4 — Qualité et checks (3-4 jours)

### Objectifs
- Couche 3 de garde-fous (checks déterministes) opérationnelle
- Référentiels factuels chargés
- Tests de conformité

### Tâches

**Jour 1** : Référentiels factuels
- Chargement `diplomes_suisses.json`
- Chargement `equivalences_international.json`
- Chargement `ch_isco_08.json`
- Chargement `cct_etendues.json` (4-5 CCT prioritaires)
- Chargement `liste_orp_2026.csv`
- Validation de schéma au chargement

**Jour 2** : Checks 3.1 à 3.4 (cohérence, diplômes)
- Check pourcentages
- Check subordonnés / activités pilotage
- Check expérience / catégorie cadre
- Check diplômes vs référentiel + "ou équivalent"
- Tests unitaires exhaustifs

**Jour 3** : Checks 3.5 à 3.7 (LEg, inclusif, ORP)
- Patterns LEg (liste Python)
- Détection écriture inclusive (selon politique entité)
- Matching ORP (intitulé → code CH-ISCO-08 → liste SECO)
- Calcul J+5 ouvrables avec jours fériés cantonaux
- Tests battery LEg (30 cas) + battery ORP (20 cas)

**Jour 4** : Checks 3.8 et 3.9 (CCT, entité)
- Cohérence CCT (si configurée)
- Cohérence référentiel entité
- Intégration dans l'écran de checks qualité
- Tests d'intégration

### Livrables
- 9 checks déterministes fonctionnels
- Référentiels factuels complets
- Tests : battery LEg (28/30), ORP (18/20), CCT (9/10)

### Critères de sortie
- Tous les checks tournent en < 3s globalement
- Aucun faux positif massif
- Intégration dans l'UI avec alertes correctement affichées

---

## 7. Phase 5 — Intégration Arhiane (2-3 jours)

### Objectifs
- Référentiel d'entité correctement lu et exploité
- Journal d'audit alimenté
- Isolation multi-entité stricte

### Tâches

**Jour 1** : Référentiel d'entité
- Lecture logo, nom, canton, CCT, politique inclusif, langue, compétences socles
- Pré-remplissage des champs concernés à la création d'un CdC
- Tests avec 3 entités fictives aux configurations différentes

**Jour 2** : Journal d'audit
- Implémentation du traçage pour toutes les actions listées en 08_INTEGRATION_ARHIANE §2.3
- Respect du schéma du journal d'audit Arhiane
- Tests sur chaque type d'action
- Vérification de la traçabilité end-to-end

**Jour 3** : Isolation multi-entité
- Vérification que tous les accès DB filtrent par entite_id
- Tests d'étanchéité (scénario T20)
- Code review ciblé pour détecter les oublis
- Documentation des conventions d'accès

### Livrables
- Intégration Arhiane V1 complète (axe référentiel + audit)
- Isolation étanche vérifiée

### Critères de sortie
- Scénario T20 (étanchéité multi-entité) passe à 100 %
- Toutes les actions tracées dans le journal d'audit
- Pré-remplissage fonctionne sur au moins 3 entités différentes

---

## 8. Phase 6 — Livraison et tests finaux (3-4 jours)

### Objectifs
- Validation finale sur tous les critères d'acceptation
- Documentation livrée
- Release candidate livrable

### Tâches

**Jour 1** : Tests d'acceptation complets
- Exécution manuelle des 7 scénarios T1-T7
- Exécution automatique des tests techniques T7-T12
- Exécution des tests de conformité T13-T16
- Exécution des tests d'ergonomie T17-T19

**Jour 2** : Tests de régression (golden set)
- Génération des 20 CdC du golden set
- Comparaison avec versions de référence
- Validation qualitative humaine
- Correction des régressions éventuelles

**Jour 3** : Documentation
- Finalisation du README du module
- Documentation des endpoints HTTP
- Procédure détaillée de mise à jour de la liste SECO
- Guide de troubleshooting (erreurs courantes)
- Changelog V1.0

**Jour 4** : Fignolage et release
- Revue finale du code
- Tests ultimes sur un environnement propre
- Packaging selon conventions Arhiane
- Création d'un tag Git `cdc_v1.0.0`
- Message de livraison récapitulatif

### Livrables
- Code source complet et propre
- Tests automatisés verts
- Documentation technique et utilisateur
- Changelog V1.0

### Critères de sortie
- Tous les critères d'acceptation de 10_JEUX_DE_TESTS §10 sont cochés
- Demo sur environnement propre réussie devant l'utilisateur
- Aucun bug bloquant connu
- Tag Git créé

---

## 9. Dépendances et prérequis

### Prérequis à avoir avant de démarrer
- Accès au code source Arhiane existant (V1 du produit)
- Accès au spec fonctionnel V1 d'Arhiane
- LM Studio installé localement avec Qwen 3.5 9B Q4_K_M
- Modèle léger choisi (Qwen 3B ou Phi 3.5 mini) installé
- Environnement Python 3.11+ avec les dépendances Arhiane
- Base de données SQLite de dev
- Un jeu de fixtures de test (à construire dès la Phase 0)

### Dépendances potentielles à valider en Phase 0
- Conventions de code Arhiane (formatage, typage, tests)
- Framework web utilisé (HTMX, Alpine.js, Flask, FastAPI, Django...)
- Système de traduction / i18n utilisé
- Gestion des sessions utilisateur
- Système de permissions/rôles

---

## 10. Décisions figées du brainstorming

Pour éviter les retours en arrière, rappel des décisions **figées** lors du brainstorming préparatoire. Toute remise en question doit passer par l'utilisateur.

### Produit
- Terme officiel : **"cahier des charges"** (jamais "fiche de poste")
- **Double entrée** : from scratch + fiche existante + duplication catalogue
- **4 formats d'annonce** : Classique corporate / Moderne narratif / Bref plateforme / ORP
- **Toggle "Non applicable"** par section pour aller vite
- **Langue de saisie respectée**, pas de traduction automatique
- **Pas de mode expert** en V1
- **Mention "Document de travail"** discrète si incomplet (pas watermark intrusif)

### Structure documentaire
- **11 sections canoniques** inspirées modèle Vaud, figées en V1
- **Hiérarchie Word native** (Titre 1, Titre 2, Titre 3)
- **Typologie [S/P/O/Su]** avec préfixes textuels
- **Pourcentages par mission, somme = 100**
- **"Ou équivalent reconnu"** systématique pour diplômes

### Qualité
- **Architecture 4 couches** : prompt → self-review → checks déterministes → relecture humaine
- **Alertes informatives, jamais bloquantes**
- **Self-review en 4 passes interrompables** sur modèle léger
- **Benchmark machine au premier lancement** + affinage moyenne glissante
- **Message adaptatif rapide / moyen / lent**

### Technique
- **SQLite** pour persistance
- **Stack Arhiane existant** (Python + HTMX/Alpine ou équivalent)
- **LM Studio** pour LLM
- **python-docx** pour génération .docx
- **Mode air-gapped strict**, aucun appel réseau sortant

### Intégration
- **Axe 1 uniquement** : lecture référentiel entité + catalogue propre + journal audit
- **PAS** : lien cert de travail, bascule juridique, copilote global, bus événements
- **Liste SECO** : pack payant OU client responsable, **jamais** livraison gratuite automatique

### UX
- **Architecture 3 zones** (25/50/25) en phase 5
- **Copilote conversationnel permanent** + **palette contextuelle**
- **Édition non-linéaire** des sections
- **Sauvegarde auto 30s**
- **Catalogue simple** : liste plate + vue regroupée optionnelle, pas d'arborescence

### Alternatives écartées (pour mémoire)
| Alternative proposée | Décision | Raison |
|---------------------|----------|--------|
| Stepper rigide en phase 5 | Rejeté | Frustre les utilisateurs expérimentés |
| Blocage à l'export si incomplet | Rejeté | On ne frustre pas l'utilisateur |
| Mode expert avec désactivation checks | Rejeté | Trop complexe, V1.5 si besoin |
| Bilinguisme automatique FR↔DE | Rejeté | Qualité médiocre, V1.5 pour FR→DE manuel |
| Livraison auto liste SECO | Rejeté | "Je ne veux pas maintenir l'app à vie" |
| Service vérificateur LEg transverse | Reporté | V1.5 si d'autres modules en ont besoin |
| Watermark/filigrane sur brouillons | Rejeté | Trop intrusif visuellement |
| Workflow d'approbation multi-étapes | Rejeté | Hors scope PME, trop lourd |

---

## 11. Risques techniques identifiés

### R1 — Performance LLM sur PC standard
**Risque** : certains postes PME ont une configuration plus modeste que prévu (ex. i5 8e génération, 8 Go RAM). Le LLM Qwen 3.5 9B peut être trop lent.

**Mitigation** :
- Benchmark au premier lancement détecte la situation
- Messages adaptatifs préviennent l'utilisateur
- Option de désactiver le self-review par défaut
- Documentation des specs minimales

**Plan B** : si la perf est vraiment inacceptable sur les PC cibles, envisager l'usage d'un modèle plus petit (Qwen 3B) pour la génération principale en V1.5. Cette décision doit être validée avec les utilisateurs.

### R2 — Fiabilité du self-review LLM sur modèle léger
**Risque** : un modèle 3B peut manquer de subtilité pour détecter les biais et stéréotypes.

**Mitigation** :
- Tests battery exhaustifs en Phase 4
- Seuil minimum de détection : 80 % de détection sur cas de régression
- Si seuil non atteint : reconsidérer le modèle (tester Phi 3.5 vs Qwen 3B vs Mistral 7B)

### R3 — Mise à jour des référentiels (notamment SECO)
**Risque** : l'utilisateur oublie de mettre à jour sa liste SECO et utilise une version obsolète → non-conformité.

**Mitigation** :
- Disclaimer renforcé si liste > 12 mois
- Rappel visible dans le dashboard
- Procédure de MAJ documentée
- Pack maintenance payant mis en avant

### R4 — Complexité du parseur de fichiers importés
**Risque** : les .docx et .pdf issus du monde réel ont des structures très variées. Le parseur peut échouer ou extraire des données incorrectes.

**Mitigation** :
- Jeu de fixtures de 10-15 fichiers "sales" en Phase 3
- Tolérance aux erreurs dans le parseur (pas de crash, extraction best-effort)
- Bascule claire vers "Restructurer complètement" si l'extraction est trop partielle

### R5 — Stabilité des prompts LLM entre versions de modèle
**Risque** : si l'utilisateur met à jour Qwen 3.5 9B avec une nouvelle version, le comportement peut changer.

**Mitigation** :
- Fixation de la version recommandée dans la doc
- Tests de régression sur golden set avant validation de nouvelles versions
- Messages de warning si détection d'une version non testée

### R6 — Isolation multi-entité
**Risque** : un bug permettant un accès cross-entité serait catastrophique en termes de confidentialité.

**Mitigation** :
- Repository pattern avec injection systématique d'entite_id
- Tests d'étanchéité exhaustifs
- Code review ciblée sur tous les accès DB
- Monitoring post-release (logs accès)

### R7 — Dérive de scope pendant le développement
**Risque** : tentation d'ajouter des fonctionnalités en cours de route (synchro inter-modules, copilote global, etc.).

**Mitigation** :
- Dossier de spécifications = source unique de vérité
- Règles d'autonomie dans 00_BRIEF_CLAUDE_CODE §3
- Validation utilisateur obligatoire pour tout ajout de scope
- Revues régulières avec l'utilisateur sur les choix d'implémentation

---

## 12. Jalons de validation utilisateur

Points de synchronisation recommandés avec l'utilisateur pour limiter le risque :

| Jalon | Phase | Livrable | Décision attendue |
|-------|-------|----------|-------------------|
| J0 | Fin Phase 0 | Analyse risques + approche | Go/no-go |
| J1 | Fin Phase 1 | Démo CRUD catalogue en ligne de commande | Valider design DB |
| J2 | Fin Phase 2 | Démo génération LLM sur 3 inputs vrac | Valider prompts |
| J3 | Milieu Phase 3 | Démo phase 5 (édition 3 zones) | Valider UX cœur |
| J4 | Fin Phase 3 | Démo flux complet sans garde-fous | Valider flux E2E |
| J5 | Fin Phase 4 | Démo checks qualité avec alertes | Valider pertinence |
| J6 | Fin Phase 5 | Démo multi-entité + audit | Valider intégration |
| J7 | Fin Phase 6 | Release candidate sur env propre | Validation livraison |

Chaque jalon est un point de décision où l'utilisateur peut demander des ajustements avant de continuer.

---

## 13. Estimation d'effort — synthèse

| Phase | Durée ETP (jours) | Effort critique |
|-------|------------------|-----------------|
| 0 — Setup & analyse | 2-3 | ⭐ (crucial pour éviter retours en arrière) |
| 1 — Backend & persistance | 4-5 | ⭐⭐ |
| 2 — LLM & prompts | 3-4 | ⭐⭐⭐ (cœur de valeur) |
| 3 — Frontend & UX | 6-8 | ⭐⭐⭐ (plus gros effort) |
| 4 — Qualité & checks | 3-4 | ⭐⭐ |
| 5 — Intégration Arhiane | 2-3 | ⭐ |
| 6 — Livraison & tests | 3-4 | ⭐ |
| **TOTAL** | **23-31 jours ETP** | 4-6 semaines calendaires |

Cette estimation suppose un développeur Python senior familier avec le stack Arhiane. Multiplier par 1.3 à 1.5 si le développeur découvre le stack.

Elle n'inclut pas les itérations après retours utilisateur, qui peuvent ajouter 20-30 % de temps.

---

## 14. Quand ce document s'arrête

Ce fichier est le **dernier** du dossier de spécifications. À partir de là, Claude Code a tout ce qu'il lui faut pour :

1. Répondre aux 3 questions du Brief (Phase 0)
2. Proposer son analyse et son approche
3. Démarrer le développement en autonomie
4. Livrer la V1 du module en 4-6 semaines

Les spécifications sont figées. En cas de doute, **demander** avant de coder.

Bonne construction.

---

**Fin du dossier de spécifications du module "Cahier des charges" d'Arhiane — V1.**
