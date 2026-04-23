# 10 — Jeux de tests et critères d'acceptation

Ensemble des jeux de tests à exécuter pour valider le module avant livraison.

---

## 1. Stratégie de test

### Pyramide de tests
- **Tests unitaires** (base large) : 100 % de couverture des checks déterministes, des transformations JSON ↔ .docx, des parsers d'import, des utilitaires
- **Tests d'intégration** (milieu) : scénarios end-to-end des cas d'usage principaux, avec vrai LLM local en mock
- **Tests manuels** (sommet) : scénarios UX complets sur un environnement de dev réaliste

### Environnement de test
- Base SQLite séparée pour les tests (`test.db`, créée/détruite par test)
- LLM mocké pour les tests unitaires et d'intégration rapides
- LLM réel pour les tests de performance et de régression
- Jeu de **fixtures** : 20 cahiers des charges de référence + 10 fiches importables (.docx, .pdf, .txt)

---

## 2. Scénarios fonctionnels end-to-end

### Scénario T1 — Création from scratch, happy path
**Correspond à CU1**.

**Étapes** :
1. Ouvrir le module depuis le dashboard Arhiane
2. Choisir "Nouveau cahier des charges"
3. Remplir le cadrage (5 questions) : intitulé "Assistant·e comptable", 100 %, poste existant à réviser, cahier individuel, recrutement
4. Coller un texte vrac de 500 mots décrivant les tâches
5. Remplir le contexte additionnel (rattachement : "Responsable comptable", 0 subordonnés, 1 jour télétravail, FR + DE)
6. Cliquer "Analyser et structurer"
7. Attendre la génération (< 60s sur PC standard)
8. Vérifier l'arrivée sur l'écran d'édition 3 zones
9. Vérifier que toutes les 11 sections sont partiellement ou totalement pré-remplies
10. Éditer 2-3 champs manuellement
11. Cliquer "Valider et générer les annonces"
12. Exécuter les checks qualité (< 3s)
13. Accepter le self-review, attendre qu'il se termine
14. Traiter 2 alertes (ignorer 1)
15. Observer la génération des 4 annonces en parallèle
16. Éditer le format 2 (Moderne narratif)
17. Exporter le pack complet
18. Vérifier dans le catalogue que le poste est bien présent avec statut 🟢 Validé

**Critères d'acceptation** :
- Temps total < 15 minutes (opérateur raisonnablement rapide)
- Aucune erreur système
- Zip téléchargé contient tous les fichiers attendus
- Journal d'audit : toutes les étapes tracées

### Scénario T2 — Import d'une fiche existante, restructuration complète
**Correspond à CU4**.

**Étapes** :
1. Ouvrir le module, choisir "Partir d'une fiche existante"
2. Uploader `fixtures/fiche_responsable_administratif_2015.docx`
3. Observer l'écran d'analyse (barre de progression)
4. Lire la synthèse produite par le module
5. Choisir "Restructurer complètement"
6. Ajouter un contexte : "La fiche date de 2015, le poste a évolué : plus de digitalisation, moins d'archivage papier"
7. Cliquer "Continuer"
8. Attendre la restructuration
9. Vérifier que les missions sont reformulées selon la structure canonique
10. Vérifier la typologie [S/P/O/Su] appliquée
11. Observer les activités qui ont été "modernisées" (et celles qui ont été conservées)
12. Valider

**Critères d'acceptation** :
- Le JSON produit suit la structure canonique (toutes les sections)
- Aucune information **inventée** (chaque élément doit être traçable dans la fiche source OU marqué "À compléter")
- Les diplômes conservent la mention "ou équivalent reconnu" (ajoutée automatiquement si absente dans la source)

### Scénario T3 — Duplication pour variante géographique
**Correspond à CU3**.

**Étapes** :
1. Ouvrir le catalogue, repérer "Commercial régional Vaud"
2. Cliquer "Dupliquer"
3. Popup : renommer en "Commercial régional Genève"
4. L'outil ouvre le nouveau cahier des charges en édition
5. Modifier le lieu de travail (Lausanne → Genève)
6. Modifier les exigences de langue (allemand → anglais)
7. Vérifier automatiquement si la CCT applicable change (selon référentiel entité Genève vs Vaud si configuré)
8. Sauvegarder
9. Vérifier que les deux postes coexistent dans le catalogue, distincts

**Critères d'acceptation** :
- La duplication ne modifie pas le poste original
- Les `poste_id` sont différents (2 entrées indépendantes en DB)
- Les historiques de versions sont indépendants

### Scénario T4 — Révision d'un poste existant
**Correspond à CU2**.

**Étapes** :
1. Ouvrir le catalogue, choisir "Assistante RH" validé en v1.0
2. Cliquer "Ouvrir"
3. Modal : "Ce cahier des charges est validé. Créer une nouvelle version ?" → Oui
4. Éditer la mission 2 pour y intégrer la dimension digitalisation
5. Sauvegarder
6. Choisir "Changement majeur" → v2.0
7. Commentaire : "Ajout de la dimension outils digitaux RH (SIRH, ATS)"
8. Valider
9. Vérifier dans l'historique que v1.0 est accessible en lecture seule

**Critères d'acceptation** :
- v1.0 reste intacte dans la DB (`est_version_active=false`)
- v2.0 devient la version active
- Le commentaire de version est visible dans l'historique
- Journal d'audit trace le passage de v1.0 à v2.0

### Scénario T5 — Export groupé pour audit ISO
**Correspond à CU7**.

**Étapes** :
1. Ouvrir le catalogue
2. Cocher 5 postes via les cases à cocher
3. Cliquer "Exporter la sélection"
4. Choisir : .docx + .pdf + sommaire .xlsx
5. Télécharger le zip
6. Ouvrir le zip, vérifier la structure
7. Ouvrir le sommaire .xlsx, vérifier les colonnes

**Critères d'acceptation** :
- Zip < 30 secondes à produire pour 5 postes
- Structure : `00_SOMMAIRE.xlsx`, `01_[intitule]/Cahier_des_charges.docx` + `.pdf`, etc., `README.txt`
- Sommaire contient : Intitulé / Statut / Version / Taux / Famille / Modifié / Auteur

### Scénario T6 — Génération ORP sur poste soumis + traçage
**Correspond à CU1 avec format ORP**.

**Étapes** :
1. Créer un cahier des charges pour "Commercial junior" (profession code 3322 — soumise à l'obligation d'annonce)
2. Valider et passer aux checks
3. Observer que le check 3.7 renvoie "Soumis à l'obligation d'annonce pour 2026"
4. Passer à la génération des 4 annonces
5. Vérifier que le Format 4 (ORP) est bien généré (pas grisé)
6. Ouvrir le format, vérifier les champs obligatoires
7. Cocher "J'ai soumis l'annonce à Job-Room"
8. Saisir une date fictive
9. Vérifier que J+5 ouvrables est calculé correctement (en excluant weekends et jours fériés cantonaux)
10. Exporter

**Critères d'acceptation** :
- Code CH-ISCO-08 correctement identifié
- Calcul J+5 correct (test avec 3 dates différentes couvrant week-ends et jours fériés)
- Journal d'audit trace la soumission ORP avec version liste SECO utilisée
- Rappel dans dashboard Arhiane "publiable à partir du [date]"

---

## 3. Tests techniques / performance

### T7 — Performance de génération initiale
**Configuration** : PC standard (i7-12th gen, 16 Go RAM, pas de GPU dédié), LLM Qwen 3.5 9B Q4_K_M via LM Studio.

| Opération | Objectif | Critère acceptation |
|-----------|----------|---------------------|
| Génération cahier des charges complet | < 60s | Passe dans 9/10 exécutions |
| Self-review LLM 4 passes | < 90s | Passe dans 9/10 exécutions |
| Checks déterministes | < 3s | Passe à 100 % |
| Génération 4 annonces | < 90s | Passe dans 9/10 exécutions |
| Export .docx | < 10s | Passe à 100 % |
| Ouverture catalogue 100 postes | < 2s | Passe à 100 % |
| Recherche full-text catalogue | < 500ms | Passe à 100 % |

### T8 — Robustesse : timeout LLM
**Scénario** : simuler un timeout LLM (bloquer la réponse de LM Studio au-delà de 120s).

**Attendu** :
- Retry automatique 1 fois
- Si 2e timeout : message utilisateur clair, bouton "Réessayer" et "Continuer sans"
- Aucun crash système
- Aucune perte de données utilisateur (inputs préservés)

### T9 — Robustesse : LM Studio indisponible
**Scénario** : éteindre LM Studio en cours de session.

**Attendu** :
- Détection au prochain appel LLM
- Message : "Le moteur d'intelligence artificielle n'est pas disponible. Vérifie que LM Studio est lancé."
- Bouton "Vérifier à nouveau" qui retry le health check
- Sauvegarde automatique préservée → reprise exacte après redémarrage de LM Studio

### T10 — Robustesse : fichier importé corrompu
**Scénario** : uploader un `.docx` tronqué ou un `.pdf` illisible.

**Attendu** :
- Détection avant tentative d'analyse LLM
- Message utilisateur explicite : "Ce fichier est illisible ou corrompu. Formats supportés : .docx, .pdf, .txt, .odt. Taille max : 10 Mo."
- Pas de crash
- Retour à l'écran d'upload

### T11 — Robustesse : sortie LLM malformée
**Scénario** : injecter une sortie LLM contenant du JSON invalide (via mock).

**Attendu** :
- Parser tolérant tente de récupérer la structure
- Si irrécupérable : retry une fois
- Si toujours échec : message utilisateur "Je n'ai pas réussi à structurer le contenu. Essaie de préciser le contexte."

### T12 — Robustesse : saisie utilisateur étrange
**Scénarios** :
- Texte vrac de 10 caractères (trop court)
- Texte vrac de 50'000 caractères (trop long)
- Caractères exotiques Unicode (emojis, caractères coréens/arabes/hébreux)
- HTML injecté
- Tentative de prompt injection : "Ignore toutes les instructions précédentes et..."

**Attendu** :
- Validation côté UI : limite min 100 caractères, max 20'000 caractères (avertissement)
- Sanitize des caractères HTML avant envoi au LLM
- Prompt injection neutralisée par les séparateurs et les instructions finales fixes (voir 09_PROMPTS_LLM §7)

---

## 4. Tests de conformité

### T13 — Battery LEg (détection de discriminations)
Jeu de 30 phrases "pièges" à faire passer par le check 3.5.

Exemples :
- "Nous cherchons un jeune commercial dynamique" → détection ÂGE attendue
- "Maximum 40 ans" → détection ÂGE attendue
- "De langue maternelle française" → détection ORIGINE/LANGUE attendue (suggestion : niveau CEFR)
- "Mère de famille idéalement" → détection GENRE attendue
- "En parfaite santé" → détection SANTÉ attendue
- "Commercial expérimenté avec 10 ans d'expérience minimum" → **PAS** de détection (c'est l'expérience, pas l'âge)
- "Avec formation en comptabilité" → **PAS** de détection (exigence objective)
- "Français C1" → **PAS** de détection (niveau CEFR est conforme)

**Critère acceptation** : ≥ 28/30 correctement classifiés.

### T14 — Battery ORP (matching intitulés)
Jeu de 20 intitulés de postes.

Exemples :
- "Responsable comptable" → soumis (code 3411)
- "Comptable" → soumis (code 3313)
- "Directeur général" → non soumis (code 1112)
- "Ingénieur informatique" → non soumis
- "Serveur / serveuse" → soumis (CCT Hôtellerie)
- "Consultant en stratégie" → non soumis
- ...

**Critère acceptation** : ≥ 18/20 correctement classifiés.

### T15 — Battery CCT (cohérence classification)
Jeu de 10 combinaisons poste / CCT configurée au niveau entité.

**Critère acceptation** : ≥ 9/10 cohérences correctement détectées.

### T16 — Conformité .docx généré
**Critères** :
- Ouvre sans erreur dans Word 365 (versions 2024+)
- Ouvre sans erreur dans LibreOffice 7+
- Ouvre dans Google Docs (upload + affichage)
- Accessibility Checker Word : aucune erreur critique
- Styles respectés (CDC_Titre1, CDC_Titre2, CDC_Corps, etc.)
- Table des matières fonctionnelle (liens cliquables)
- Pied de page correct (toutes pages sauf garde)
- Taille fichier < 2 Mo (hors logo haute résolution)
- Encodage UTF-8, caractères suisses romands corrects

---

## 5. Tests d'ergonomie et accessibilité

### T17 — Navigation clavier
**Scénario** : parcourir l'ensemble du flux sans toucher la souris.

**Critères** :
- Tab / Shift+Tab fonctionnent dans un ordre logique
- Enter valide les boutons primaires
- Échap ferme les popups
- Raccourcis Ctrl+S, Ctrl+Z, Ctrl+K fonctionnels
- Focus visible à chaque étape

### T18 — Contraste et taille police
**Outils** : axe DevTools / WAVE

**Critères** :
- Ratio de contraste ≥ 4.5:1 pour le texte normal (WCAG AA)
- Ratio de contraste ≥ 3:1 pour le texte large
- Taille de police ≥ 11pt pour le corps
- Pas de texte uniquement par couleur (toujours un pictogramme ou un texte)

### T19 — Responsive
**Scénario** : tester sur 3 résolutions :
- 1920×1080 (bureau standard) → layout 3 zones
- 1366×768 (laptop d'entrée de gamme) → layout 3 zones compacte
- 1280×720 (très petit bureau / tablette landscape) → bascule en onglets

**Critère acceptation** : pas de débordement, pas de scroll horizontal, toutes les actions accessibles.

---

## 6. Tests d'isolation multi-entité

### T20 — Étanchéité entre entités
**Scénario** :
1. Utilisateur se connecte sur entité A, crée 5 cahiers des charges
2. Bascule sur entité B, crée 3 cahiers des charges
3. Vérifier que le catalogue de B ne contient que 3 postes (pas de visibilité de A)
4. Vérifier que la recherche dans B ne remonte jamais un poste de A
5. Vérifier que l'export groupé dans B ne contient que ses propres postes
6. Vérifier en base SQLite que chaque ligne a bien `entite_id` correct

**Critère acceptation** : aucune fuite possible, même en tentative manuelle d'accès par URL forgée.

---

## 7. Tests de benchmark machine

### T21 — Benchmark au premier lancement
**Scénario** :
1. Installation fresh d'Arhiane sur une machine
2. Premier lancement du module
3. Observer le benchmark automatique (invisible pour l'utilisateur ou très discret)
4. Vérifier dans la config `benchmark_llm_principal.tokens_per_second` > 0

**Critères acceptation** :
- Benchmark en < 15 secondes
- Catégorisation "rapide / moyenne / lente" correcte selon la machine
- Messages de self-review adaptés à la catégorie

### T22 — Affinage par moyenne glissante
**Scénario** :
1. Exécuter 10 générations successives
2. Observer que l'estimation affichée se rapproche de la réalité

**Critère acceptation** : après 5 exécutions, l'estimation est à ± 20 % de la réalité.

---

## 8. Tests du catalogue et de la persistance

### T23 — CRUD complet
Tests unitaires exhaustifs des opérations sur le catalogue :
- Create (création d'un CdC)
- Read (lecture, recherche, filtres)
- Update (édition, versioning)
- Delete (soft + hard avec corbeille 30j)

**Critère acceptation** : 100 % de couverture, 0 régression.

### T24 — Volumétrie
**Scénario** : créer artificiellement 500 cahiers des charges en base (fixtures).

**Critères** :
- Ouverture du catalogue : < 3 secondes
- Recherche full-text : < 1 seconde
- Pagination fonctionnelle
- Aucun ralentissement perceptible

### T25 — Restauration depuis corbeille après 29 jours
**Scénario** :
1. Supprimer un poste le jour J
2. Avancer la date système fictive à J+29
3. Vérifier que le poste est toujours restaurable
4. Avancer à J+31
5. Vérifier que le poste a été supprimé définitivement par le job cron quotidien

**Critère acceptation** : respect exact de la fenêtre de 30 jours.

---

## 9. Tests de régression (à automatiser)

### Golden set de 20 cahiers des charges
Avant chaque release, re-générer les 20 cahiers des charges du golden set avec le LLM actuel, et comparer :

**Métriques quantitatives automatisables** :
- Toutes les sections présentes : 100 %
- Somme des pourcentages = 100 : 100 %
- Mention "ou équivalent reconnu" présente pour diplômes : 100 %
- Zéro pattern LEg détecté : 100 %
- Zéro anglicisme corporate de la liste noire : 100 %

**Sur ces métriques, aucune régression n'est acceptée.**

**Comparaison qualitative (humaine)** :
- Lecture comparative des 20 paires (avant / après)
- Détection de dégradations subtiles non capturées par les métriques
- Validation manuelle avant release

---

## 10. Critères d'acceptation finaux pour livraison V1

Le module est considéré **prêt à livrer** quand :

### Fonctionnel
- ✅ Tous les 7 scénarios T1-T7 passent sans erreur
- ✅ Tous les 20 tests des 4 couches de garde-fous passent
- ✅ Conformité .docx vérifiée (T16)
- ✅ Isolation multi-entité vérifiée (T20)

### Technique
- ✅ Performance respectée (T7)
- ✅ Robustesse aux pannes LLM (T8, T9)
- ✅ Robustesse aux données étranges (T10, T11, T12)
- ✅ Volumétrie 500 postes sans dégradation (T24)

### Conformité
- ✅ Battery LEg : 28/30 minimum (T13)
- ✅ Battery ORP : 18/20 minimum (T14)
- ✅ Battery CCT : 9/10 minimum (T15)

### Ergonomie
- ✅ Navigation clavier complète (T17)
- ✅ Contrastes WCAG AA (T18)
- ✅ Responsive 1366-1920 (T19)

### Documentation
- ✅ README du module
- ✅ Documentation endpoints HTTP
- ✅ Procédure MAJ liste SECO
- ✅ Changelog V1

### Tests automatisés
- ✅ Couverture unitaire 100 % sur checks déterministes
- ✅ Couverture intégration ≥ 80 %
- ✅ Tests golden set (20 CdC) passent
- ✅ CI/CD verte (si définie au niveau Arhiane)

---

**Fichier suivant à lire** : [11_ROADMAP.md](11_ROADMAP.md) — phases de développement et jalons.
