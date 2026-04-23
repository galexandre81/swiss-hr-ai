# 01 — Spécification fonctionnelle principale

Module **"Cahier des charges"** d'Arhiane — V1

---

## 1. Objectif du module

Permettre à un responsable RH de PME suisse romande de produire, en mode local air-gapped, deux types de livrables interdépendants :

1. Un **cahier des charges** au format .docx, structuré selon les modèles officiels romands (Vaud, Genève, Fribourg), destiné à formaliser un poste en interne (document contractuel entre employeur et titulaire, ou référence pour un recrutement).

2. Quatre **variantes d'annonce d'emploi**, générées à partir du cahier des charges, chacune adaptée à un canal de diffusion différent (corporate, moderne narratif, plateformes type jobup/LinkedIn, format ORP pour Job-Room).

Le module doit permettre deux modes d'entrée :

- **Création from scratch** : à partir d'une liste de tâches en vrac (texte libre, import, dictée)
- **Reprise d'une fiche existante** : import d'un cahier des charges ou fiche de poste existant (Word, PDF, texte) que l'outil analyse, propose de reprendre, améliorer ou restructurer

Le document doit pouvoir être itéré, édité, enrichi progressivement par l'utilisateur, avec l'aide d'un copilote conversationnel contextuel.

---

## 2. Utilisateurs cibles

Les mêmes que ceux d'Arhiane en général :

- **Responsables RH** de PME suisses (10-250 employés typiquement) — utilisateurs principaux, formés, maîtrisent le vocabulaire RH
- **Assistants RH**, nouveaux dans la fonction — utilisateurs secondaires, formulations plus guidées
- **Dirigeants de PME** qui font de la RH eux-mêmes — pas de jargon, interface accessible

Tous ces profils doivent être servis par la même interface. Le copilote conversationnel adapte sa profondeur selon les questions posées, sans infantiliser.

---

## 3. Principes fondamentaux

Hérités d'Arhiane :

- **Souveraineté des données** : fonctionnement 100 % local, aucune donnée ne quitte le poste
- **Confidentialité par conception (LPD-compliant)** : mode air-gapped, blocage du trafic sortant
- **Zéro coût d'API** : LLM local uniquement
- **Auditabilité** : toutes les actions tracées dans le journal d'audit commun d'Arhiane
- **Factualité** : pas d'invention de diplômes, CCT, articles de loi ; référentiel factuel intégré
- **Boîte à outils RH, pas SIRH** : pas de base de données employés, pas de synchronisation inter-modules
- **Outil d'aide, pas remplaçant** : disclaimers "vérifier manuellement les cas sensibles" respectés

Spécifiques à ce module :

- **Terminologie romande** : "cahier des charges" (jamais "fiche de poste")
- **Structure officielle** : les 11 sections inspirées des modèles Vaud/Genève/Fribourg (voir 02_STRUCTURE_DOCX.md)
- **Typologie d'activités** : chaque activité classée en [S]tratégique, [P]ilotage, [O]pérationnel, [Su]pport
- **Pourcentages de temps** : chaque mission a un % explicite, somme = 100 %
- **Pas de mode "expert"** : simplicité d'abord, pas d'options avancées à désactiver
- **Export partiel autorisé** : pas de blocage rigide, juste une mention discrète "Document de travail" si sections incomplètes

---

## 4. Langues supportées

En cohérence avec Arhiane :

- **Français** et **Allemand** : langues principales. Génération dans la langue de saisie, pas de traduction automatique croisée en V1.
- **Anglais** : interface disponible, mais génération de cahier des charges et annonces non optimisée en V1 (reporté V1.5).
- **Italien** : non supporté en V1.

La langue par défaut est celle configurée au niveau de l'entité Arhiane.

---

## 5. Architecture fonctionnelle générale

Le module est structuré en 5 couches logiques :

### Couche 1 — Interface utilisateur (UI)
Architecture 3 zones (navigation gauche / édition centrale / copilote droit), flux en 8 phases depuis le dashboard jusqu'à l'export. Voir 04_UX_FLUX.md.

### Couche 2 — Logique métier (business logic)
- Gestion du cycle de vie d'un cahier des charges (création, édition, validation, versioning, archivage)
- Transformation tâches vrac → structure canonique
- Application de la typologie [S/P/O/Su]
- Calcul de cohérence (pourcentages, compétences vs missions)
- Gestion du catalogue de postes par entité

### Couche 3 — Orchestration LLM
- Prompt système robuste à la génération (prévention des hallucinations)
- Génération structurée (appels successifs ciblés, pas un gros appel monolithique)
- Self-review optionnel sur modèle léger (3B) avec 4 micro-passes interrompables
- Benchmark machine au premier lancement
- Voir 09_PROMPTS_LLM.md

### Couche 4 — Garde-fous qualité
- Checks déterministes automatiques (cohérence pourcentages, ORP, LEg, CCT, cohérence entité)
- Vérificateur LEg/non-discrimination/inclusif
- Référentiel factuel de vérification (diplômes, CCT, CH-ISCO-08)
- Invitation à la relecture humaine finale
- Voir 06_GARDE_FOUS_QUALITE.md

### Couche 5 — Export et persistance
- Génération .docx selon structure canonique (styles Word natifs)
- Génération .pdf pour lecture seule
- Export des 4 formats d'annonce
- Export groupé (zip pour audit/certification)
- Catalogue de postes par entité (SQLite)
- Journal d'audit commun

---

## 6. Cas d'usage principal (happy path)

1. Le RH clique sur la tuile "Cahier des charges" du dashboard Arhiane
2. Il choisit "Nouveau cahier des charges" puis remplit le cadrage initial (5 questions)
3. Il colle un pavé de texte libre décrivant les tâches du poste
4. Arhiane structure en ~20-30 secondes (barre de progression avec étapes)
5. Le RH arrive sur l'écran d'édition 3 zones, toutes les sections sont partiellement pré-remplies
6. Il édite, complète, dialogue avec le copilote pour reformuler ou enrichir
7. Il clique "Valider et générer les annonces"
8. Les checks déterministes tournent en 2-3 secondes et affichent des alertes
9. Arhiane propose la relecture LLM optionnelle avec estimation de temps sur son poste
10. Le RH accepte, la relecture tourne, d'autres alertes s'ajoutent
11. Il traite les alertes (ou les ignore), les 4 annonces sont générées en parallèle
12. Il exporte le pack (cahier des charges .docx + 4 annonces .docx + .pdf)
13. Le cahier des charges est archivé dans le catalogue de l'entité avec tag "🟢 Validé"

Durée totale sur un PC standard : 10-20 minutes pour un poste nouveau, 5-10 minutes à partir d'une fiche existante.

---

## 7. Cas d'usage secondaires

### CU2 — Reprendre et réviser un cahier des charges existant
Le RH ouvre le catalogue, trouve le cahier des charges de l'assistante administrative (créé il y a 2 ans), clic "Réviser". Arhiane crée une v2 en partant de la v1. Le RH ajuste 3-4 sections, valide. La v2 devient active, la v1 reste dans l'historique.

### CU3 — Dupliquer pour variante
Le RH a un cahier des charges "Commercial régional Vaud". Il veut créer "Commercial régional Genève" (similaire, mais avec ajustements CCT et langue). Il sélectionne le poste, clic "Dupliquer", ajuste, sauvegarde comme nouveau poste.

### CU4 — Partir d'une fiche existante pour créer un nouveau cahier des charges
Le RH a reçu un vieux fichier Word d'un cabinet de conseil. Il l'importe, Arhiane analyse et propose trois options : utiliser tel quel / compléter / restructurer complètement. Le RH choisit "compléter", Arhiane propose des améliorations.

### CU5 — Produire une annonce seule à partir d'un cahier des charges existant
Le RH a un poste en catalogue, veut juste régénérer les annonces pour une nouvelle publication. Il ouvre le poste, clic "Générer les annonces". Saut direct à la phase 7, 4 annonces produites.

### CU6 — Comparer deux postes
Le RH hésite sur la classification d'un nouveau poste. Il ouvre la vue comparative entre ce nouveau poste et un poste existant proche. Différences surlignées, aide à la décision.

### CU7 — Export groupé pour audit
Demande externe (ISO, due diligence, inspection du travail) : le RH sélectionne plusieurs postes dans le catalogue, clic "Exporter la sélection". Zip produit avec tous les .docx + sommaire .xlsx.

---

## 8. Hors scope V1

Reprendre la liste du 00_BRIEF_CLAUDE_CODE.md §7. En synthèse :
- Pas de synchronisation avec autres modules Arhiane
- Pas de copilote global
- Pas de signature électronique
- Pas de workflow d'approbation
- Pas de mode expert
- Pas de détection auto de doublons
- Pas d'organigramme visuel
- Pas de matrice de compétences
- Italien et anglais en génération
- Vérificateur LEg/inclusif reste interne au module (pas exposé comme service)

---

## 9. Contraintes non fonctionnelles

### Performance
- Génération initiale d'un cahier des charges complet : < 60 secondes sur PC standard (i7 récent, 16 Go RAM, pas de GPU)
- Self-review LLM complet : < 90 secondes sur PC standard
- Actions d'édition ponctuelles (reformuler, proposer variante) : < 10 secondes
- Ouverture du catalogue avec 100 postes : < 2 secondes
- Export .docx : < 10 secondes

### Robustesse
- Sauvegarde automatique toutes les 30 secondes en cours d'édition
- Reprise exacte d'un travail interrompu (pas de perte de données)
- Tolérance aux erreurs LLM (timeout, génération vide) avec retry automatique et fallback
- Pas de crash en cas de fichier importé corrompu, juste un message d'erreur explicite

### Ergonomie
- Interface utilisable sans formation pour un RH PME standard
- Documentation intégrée (tooltips, aide contextuelle, premier usage guidé)
- Raccourcis clavier pour les actions fréquentes (Ctrl+S, Ctrl+Z, Ctrl+Entrée pour valider)
- Indicateurs de progression sur tous les temps d'attente > 3 secondes

### Accessibilité
- Contrastes WCAG AA minimum
- Navigation au clavier complète
- Lisible en police de base (pas de trop petit)

### Sécurité
- Aucun appel réseau sortant
- Chiffrement des données locales (cohérent avec spec Arhiane existant)
- Pas d'enregistrement de prompts LLM dans des logs accessibles à un utilisateur non-admin

---

## 10. Modèle économique et maintenance

### Position contractuelle (à refléter dans disclaimers)
Le module est livré avec :
- Référentiel factuel (diplômes, CCT, CH-ISCO-08) à jour à la date de livraison
- Liste SECO des professions ORP à jour au 1er janvier de l'année de livraison

La maintenance de ces référentiels est **à la charge du client**, qui peut :
- Souscrire au pack de maintenance annuel payant d'Arhiane
- Télécharger lui-même la nouvelle liste SECO chaque année et la déposer dans le dossier prévu
- Ne rien faire et assumer le risque d'obsolescence (avec disclaimer renforcé à l'écran)

### Disclaimers à afficher dans l'outil
- Sur le format ORP : *"La vérification d'obligation d'annonce se base sur la liste SECO installée localement (version [X]). Avant toute publication, il est de votre responsabilité de vérifier la version actuelle sur travail.swiss (Check-Up [année])."*
- À chaque génération : *"Arhiane est un outil d'aide à la rédaction. Les documents produits doivent être relus et validés avant usage. La responsabilité éditoriale incombe à l'utilisateur."*
- À l'ouverture du module si liste SECO > 12 mois : *"⚠️ Votre liste SECO date de [X]. Une version plus récente est peut-être disponible. Mettez à jour pour garantir la conformité ORP."*

---

## 11. Critères d'acceptation généraux du module

Le module est considéré livré quand :

1. Les 7 cas d'usage (CU1 à CU7) fonctionnent bout en bout sans erreur sur des jeux de test fournis
2. Les 11 sections du cahier des charges .docx sont correctement générées selon la structure définie en 02_STRUCTURE_DOCX.md
3. Les 4 formats d'annonce sont générés correctement selon les spécifications de 03_FORMATS_ANNONCES.md
4. Les checks déterministes fonctionnent à 100 % sur les jeux de tests dédiés (voir 10_JEUX_DE_TESTS.md)
5. Le self-review LLM produit des alertes cohérentes sur au moins 80 % des cas de test
6. Le benchmark machine fonctionne au premier lancement et l'estimation de durée est affichée correctement
7. Le catalogue de postes fonctionne (création, édition, versioning, duplication, archivage, recherche, export groupé)
8. L'intégration avec le référentiel d'entité Arhiane est fonctionnelle (lecture seule, pré-remplissage)
9. Le journal d'audit est alimenté correctement pour toutes les actions du module
10. La documentation est livrée (README, docs endpoints, procédure MAJ liste SECO)
11. Les tests unitaires et d'intégration passent à 100 %

---

## 12. Glossaire

| Terme | Définition |
|-------|-----------|
| **Cahier des charges** | Document RH formel décrivant un poste, ses missions, responsabilités, compétences. Terme officiel en Suisse romande. Bannir "fiche de poste" (français). |
| **Fiche de fonction** | Synonyme accessible de "cahier des charges", utilisable en tooltips et aide. |
| **Emploi-type** | Description générique d'un métier (stable, pour classification salariale). Hors scope V1 (reporté V1.5). |
| **Mission** | Grande finalité du poste, formulée à l'infinitif (4-7 par cahier des charges, somme = 100 % du temps). |
| **Activité** | Tâche concrète réalisée pour accomplir une mission. Typée [S/P/O/Su]. |
| **[S] Stratégique** | Activité de décision, arbitrage, représentation. |
| **[P] Pilotage** | Activité de coordination, supervision, contrôle, reporting. |
| **[O] Opérationnel** | Activité d'exécution, cœur de métier visible. |
| **[Su] Support** | Activité récurrente nécessaire mais non cœur de métier (documenter, archiver). |
| **ORP** | Office Régional de Placement (cantonal). |
| **Obligation d'annonce** | Obligation légale d'annoncer certains postes vacants aux ORP avant publication. |
| **Job-Room** | Plateforme officielle du SECO pour l'obligation d'annonce (travail.swiss). |
| **LEg** | Loi sur l'égalité entre femmes et hommes. |
| **CO 328** | Article du Code des Obligations sur la protection de la personnalité du travailleur (non-discrimination). |
| **CCT** | Convention Collective de Travail. |
| **CH-ISCO-08** | Nomenclature suisse des professions, dérivée de la classification internationale ISCO-08. |
| **CEFR** | Common European Framework of Reference — pour niveaux de langue (A1, A2, B1, B2, C1, C2). |
| **Écriture inclusive / épicène** | Langage non discriminant en genre (doublets, formules neutres, point médian). |

---

**Fichier suivant à lire** : [02_STRUCTURE_DOCX.md](02_STRUCTURE_DOCX.md) — la structure détaillée du cahier des charges .docx.
