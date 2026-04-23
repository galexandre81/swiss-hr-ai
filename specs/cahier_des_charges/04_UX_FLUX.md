# 04 — Flux utilisateur et UX

Spécification détaillée du flux utilisateur, de l'architecture d'écran et des interactions.

---

## 1. Architecture générale — 3 zones persistantes

Une fois entré dans le module Cahier des charges (phase 5 — édition), l'écran est structuré en **3 zones persistantes** qui ne bougent pas pendant la session.

```
┌─────────────────────┬────────────────────────────┬──────────────────────┐
│                     │                            │                      │
│                     │                            │                      │
│   ZONE GAUCHE       │      ZONE CENTRALE         │     ZONE DROITE      │
│   Navigation        │      Édition               │     Copilote         │
│   (25 %)            │      (50 %)                │     (25 %)           │
│                     │                            │                      │
│                     │                            │                      │
│                     │                            │                      │
│                     │                            │                      │
│                     │                            │                      │
└─────────────────────┴────────────────────────────┴──────────────────────┘
```

### Zone gauche — Navigation du cahier des charges (25 %)

**Contenu** :
- Titre et métadonnées du cahier des charges en cours
- Liste verticale des 11 sections avec indicateur d'état :
  - ● **vert** = renseignée
  - ◐ **orange** = partielle
  - ○ **gris** = à faire
  - ⊘ **gris barré** = marquée non-applicable
- Clic sur une section = navigation non linéaire vers cette section
- Indicateur global de complétude en haut (ex. "73 % complet · 3 sections à finaliser")
- **Actions globales en bas** :
  - 💾 Sauvegarder (sauvegarde auto toutes les 30s, ce bouton force)
  - 📋 Dupliquer
  - 🔍 Faire relire par Arhiane (self-review LLM)
  - ✅ Valider et générer les annonces
  - 📤 Exporter

### Zone centrale — Édition (50 %)

**Contenu** :
- Section active en cours d'édition
- Tous les champs éditables de cette section
- Toggle **"Cette section n'est pas applicable à ce poste"** en haut (uniquement pour les 3 sections toggables : 5, 6, 10)
- Actions au niveau de chaque bloc (petits boutons au survol) :
  - 🔄 Reformuler
  - ✂️ Raccourcir
  - 📝 Développer
  - 🎯 Plus concret
  - 🗑️ Supprimer
- Actions au niveau de la section (bouton en haut à droite) :
  - Réinitialiser la section
  - Marquer non-applicable (si toggable)
  - Comparer avec version précédente
  - Proposer une alternative complète

### Zone droite — Copilote IA (25 %)

**Contenu** :
- **Palette d'accès rapide contextuelle** en haut (selon la section active en zone centrale)
  - Ex. section Missions : "Proposer 3 variantes", "Reformuler au présent", "Ajouter une mission manquante", "Équilibrer"
  - Ex. section Compétences : "Suggérer des compétences métier", "Vérifier cohérence missions"
  - 3-4 boutons par section, contextuels
- **Zone de chat conversationnel** qui prend le reste de la hauteur
  - Historique persistant de la session (et entre sessions si même cahier des charges)
  - Le LLM a en contexte le cahier des charges complet
  - Propositions en diff visuel (vert ajout, rouge suppression) avec boutons Accepter/Refuser/Régénérer
- **Bouton de bascule** "Voir en preview .docx" qui remplace la zone par un aperçu Word du document

### Adaptation responsive

Si la largeur d'écran est < 1366px, les 3 zones deviennent des **onglets bascules** :
- Onglet "Navigation" (zone gauche)
- Onglet "Édition" (zone centrale)
- Onglet "Copilote" (zone droite)

Sur les PC PME standards (1920×1080), le layout 3 zones est idéal.

---

## 2. Flux en 8 phases — Vue d'ensemble

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   PHASE 1    │──▶│   PHASE 2    │──▶│   PHASE 3    │──▶│   PHASE 4    │
│  Dashboard   │   │  Cadrage     │   │  Capture     │   │Structuration │
│              │   │  initial     │   │  des inputs  │   │  assistée    │
└──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘
                                                                 │
                                                                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   PHASE 8    │◀──│   PHASE 7    │◀──│   PHASE 6    │◀──│   PHASE 5    │
│  Export &    │   │  Génération  │   │  Checks      │   │  Édition     │
│  archivage   │   │  4 annonces  │   │  qualité     │   │  (3 zones)   │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

Le cœur du travail se passe en **phase 5** (édition). Les autres phases sont des transitions.

---

## 3. Phase 1 — Entrée depuis le dashboard Arhiane

### Déclencheur
L'utilisateur clique sur la tuile **"Cahier des charges"** du dashboard Arhiane.

### Écran
Modal centré avec 3 cartes d'options visuelles (pas un dropdown) :

```
  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
  │                         │  │                         │  │                         │
  │     📝                  │  │     📂                  │  │     🗂️                  │
  │                         │  │                         │  │                         │
  │  Nouveau cahier         │  │  Partir d'une           │  │  Dupliquer un poste     │
  │  des charges            │  │  fiche existante        │  │  du catalogue           │
  │                         │  │                         │  │                         │
  │  Je pars de zéro ou     │  │  J'ai déjà un document  │  │  Je ressemble à un      │
  │  de tâches en vrac      │  │  à reprendre ou         │  │  poste déjà documenté   │
  │                         │  │  améliorer              │  │                         │
  │                         │  │                         │  │                         │
  │     [Commencer]         │  │     [Commencer]         │  │     [Commencer]         │
  │                         │  │                         │  │                         │
  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

### États particuliers
- La 3e carte "Dupliquer" est **grisée** si le catalogue de l'entité est vide, avec tooltip "Le catalogue de l'entité ne contient aucun poste — cette option sera disponible après votre premier cahier des charges."

### Journalisation
Action "Ouverture module CdC" tracée dans le journal d'audit.

---

## 4. Phase 2 — Cadrage initial

### Écran
Un formulaire court de 5 questions, affichées **dans un seul écran** (pas de stepper) :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Quelques questions pour démarrer                                       │
│                                                                         │
│  1. Pour quelle entité ce cahier des charges ?                          │
│     [Dropdown] Cabinet XYZ SA                                           │
│                                                                         │
│  2. Intitulé du poste ?                                                 │
│     [Texte libre]                                     (suggestions LLM) │
│                                                                         │
│  3. Situation                                                           │
│     ○ Poste existant à réviser                                          │
│     ○ Poste vacant à repourvoir                                         │
│     ○ Création de poste                                                 │
│                                                                         │
│  4. Type de document                                                    │
│     ○ Cahier des charges individuel (titulaire identifié)               │
│     ○ Fiche générique / emploi-type (réutilisable)                      │
│                                                                         │
│  5. Intention principale                                                │
│     ○ Je prépare un recrutement (→ 4 formats d'annonce générés)         │
│     ○ Je formalise un poste interne (→ cahier des charges seul)         │
│                                                                         │
│                      [Je préfère briefer en libre] [Commencer]          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Logique
Les 5 réponses pilotent les phases suivantes :
- Si "Je formalise un poste interne" → **saut de la phase 7** (pas de génération d'annonces)
- Si "Création de poste" → active la suggestion proactive de compétences par le LLM en phase 4
- Si "Poste existant à réviser" → force la phase 3 en sous-flux B (import fiche)
- Si "Fiche générique" → la structure générée est plus abstraite, sans signature finale

### Bouton "Je préfère briefer en libre"
Alternative à la forme structurée : ouvre directement le copilote conversationnel pour un briefing en langage naturel. Utile pour les utilisateurs avancés qui ont déjà un contexte précis à transmettre.

---

## 5. Phase 3 — Capture des inputs

Deux sous-flux selon l'option choisie en phase 1.

### Sous-flux A — Création from scratch (tâches en vrac)

**Écran** :
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Décris les tâches du poste                                             │
│                                                                         │
│  Ne te soucie ni de l'ordre, ni de la structure, ni des répétitions.   │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  [Zone de texte géante, 10 lignes visibles, extensible]           │ │
│  │                                                                   │ │
│  │  Exemple : "il va devoir gérer l'équipe de 4 personnes, faire    │ │
│  │  les plannings, traiter les demandes clients, s'occuper du       │ │
│  │  reporting mensuel pour la direction..."                          │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  [📋 Coller depuis un mail/doc]  [📁 Importer un fichier]  [🎤 Dicter]  │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Contexte supplémentaire (optionnel)                                    │
│  • Taux d'occupation : [___] %                                          │
│  • Rattachement hiérarchique : [__________]                             │
│  • Nombre de subordonnés directs : [_]                                  │
│  • Télétravail : [Aucun / 1j / 2j / 3j / 100%]                          │
│  • Langues requises : [FR] [DE] [EN] [IT]                               │
│                                                                         │
│                                    [Retour]  [Analyser et structurer]   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Notes** :
- Le bouton "Dicter" est désactivé si aucun moteur de dictée local n'est installé (air-gapped strict)
- Le contexte supplémentaire enrichit le prompt LLM mais n'est pas bloquant
- Validation minimale avant "Analyser" : au moins 100 caractères dans la zone de texte

### Sous-flux B — Import d'une fiche existante

**Écran 1 — Upload** :
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Importe ta fiche existante                                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │                  📁  Glisse-dépose ton fichier ici                │ │
│  │                                                                   │ │
│  │             Formats acceptés : .docx, .pdf, .txt, .odt            │ │
│  │                      Taille max : 10 Mo                           │ │
│  │                                                                   │ │
│  │                         [Parcourir...]                            │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Écran 2 — Analyse** : après upload, barre de progression "Analyse du document..." (5-15 secondes)

**Écran 3 — Synthèse et choix** :
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Voici ce que j'ai compris de ta fiche                                  │
│                                                                         │
│  📋 Intitulé du poste : Responsable administratif                        │
│  🎯 Missions principales identifiées : 5                                │
│  🏷️ Compétences mentionnées : 8                                          │
│  📚 Formation requise : Master en gestion                               │
│                                                                         │
│  [Détails] → (dépliable pour voir plus)                                 │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Comment veux-tu procéder ?                                             │
│                                                                         │
│  ○ Utiliser telle quelle                                                │
│    → Je passe directement à l'édition avec le contenu importé           │
│                                                                         │
│  ○ Rafraîchir / compléter                                               │
│    → Arhiane propose des améliorations en préservant le contenu         │
│                                                                         │
│  ○ Restructurer complètement                                            │
│    → Arhiane traite la fiche comme matière brute et reconstruit tout    │
│                                                                         │
│  Contexte supplémentaire (optionnel)                                    │
│  [Zone de texte : "La fiche date de 2015, le poste a évolué..."]        │
│                                                                         │
│                                              [Retour]  [Continuer]      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Phase 4 — Structuration assistée

### Écran de transition

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Arhiane analyse et structure tes informations...                       │
│                                                                         │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░  68 %                       │
│                                                                         │
│  ✓ Je lis les tâches que tu as décrites                                 │
│  ✓ Je regroupe les activités par thème                                  │
│  ⧗ Je structure les missions principales                                │
│  ⋯ Je déduis les compétences associées                                  │
│  ⋯ Je propose un profil candidat cohérent                               │
│  ⋯ Je finalise le document                                              │
│                                                                         │
│  Temps estimé restant : 12 secondes                                     │
│                                                                         │
│                                                              [Annuler]  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Traitement technique
1. Extraction des actions / verbes depuis le vrac
2. Déduplication et regroupement par thème
3. Classification en missions principales (4 à 7)
4. Pour chaque mission, décomposition en activités avec typologie [S/P/O/Su]
5. Déduction de pourcentages de temps par mission (somme = 100 %)
6. Proposition de livrables et indicateurs pour chaque mission
7. Déduction des compétences socles, transversales, métier et managériales
8. Proposition de profil (formation, expérience, langues)

### Règles
- Le LLM n'invente **jamais** de tâches non présentes dans le vrac
- Si une section manque d'information : laisser vide avec tag "À compléter — information insuffisante"
- Durée typique : 20-30 secondes sur PC standard
- Bascule automatique vers phase 5 à la fin

### Gestion d'erreur
- Si timeout LLM : message clair + bouton "Réessayer" + option "Passer à l'édition manuelle"
- Si génération vide ou corrompue : retry automatique une fois, sinon erreur avec logs

---

## 7. Phase 5 — Édition (cœur du travail)

### Architecture 3 zones active

Voir §1 ci-dessus pour le détail des 3 zones.

### Interactions clés

#### Édition d'un bloc dans la zone centrale
1. L'utilisateur clique dans un champ → le champ devient éditable (bordure bleue légère)
2. Il tape librement
3. Modification auto-sauvegardée après 30 secondes d'inactivité
4. Des boutons d'action apparaissent au survol du bloc (🔄 ✂️ 📝 🎯 🗑️)

#### Action LLM sur un bloc (exemple : "Reformuler")
1. Clic sur 🔄 → mini-popup à côté du bloc avec message "Je reformule..." + spinner
2. 3-10 secondes d'attente
3. Popup remplacé par : proposition du LLM (en vert = ajout, en rouge barré = suppression par rapport à l'original)
4. Boutons : [Accepter] [Refuser] [Régénérer]
5. Accepter → le bloc est mis à jour, popup fermé
6. Ctrl+Z reste actif pour annuler

#### Dialogue avec le copilote (zone droite)
1. L'utilisateur tape un prompt en langage naturel : *"reformule la mission 2 en insistant sur la dimension client"*
2. Le LLM reçoit en contexte :
   - Le cahier des charges complet en JSON
   - L'historique de la conversation
   - Le prompt utilisateur
3. Réponse affichée dans le chat + proposition de modification en diff
4. Boutons [Accepter] [Refuser] [Régénérer]

#### Palette d'accès rapide contextuelle
Selon la section active, 3-4 boutons préformulés s'affichent au-dessus du chat. Exemples :

| Section active | Boutons de la palette |
|----------------|----------------------|
| 2 — Raison d'être | "Rendre plus concis" · "Insister sur l'impact" · "Reformuler au présent" |
| 3 — Missions | "Proposer 3 variantes" · "Équilibrer les formulations" · "Ajouter une mission manquante" |
| 4 — Activités | "Vérifier la typologie [S/P/O/Su]" · "Équilibrer les pourcentages" · "Développer les livrables" |
| 8 — Profil | "Ouvrir aux équivalences internationales" · "Vérifier LEg" |
| 9 — Compétences | "Suggérer compétences métier" · "Vérifier cohérence missions" · "Détecter stéréotypes de genre" |

Chaque bouton envoie un **prompt pré-écrit** au copilote, qui apparaît dans le chat comme une question posée par l'utilisateur. Formation par l'exemple.

#### Mode "Consultation titulaire"
Bouton accessible depuis la barre d'outils : **"Consulter le titulaire actuel"**

Si activé :
1. Popup avec explication + champ "À qui envoyer le questionnaire ?"
2. Génération d'un questionnaire PDF adapté au poste (questions simples : "Quelles sont les 3 activités qui prennent le plus de temps dans votre poste ?", "Quelles sont les compétences que vous avez dû acquérir pour ce poste ?", etc.)
3. Option : envoyer par email (si module email connecté, sinon bouton "Télécharger" + envoi manuel)
4. Bouton "Importer le questionnaire rempli" dans l'écran d'édition pour intégrer les réponses dans la fiche

Fonctionnalité cohérente avec le principe suisse romand de participation du titulaire à la rédaction du cahier des charges.

### Indicateurs en temps réel
- Compteur de complétude en haut à gauche : "73 %"
- Dernière sauvegarde : "Il y a 12 secondes" en bas à droite
- Nombre de sections marquées "Non applicable" : "2/11"

### Reprise d'un travail interrompu
Quand l'utilisateur revient dans le module, l'écran d'accueil du module (avant la phase 1) affiche :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Bienvenue dans le module Cahier des charges                            │
│                                                                         │
│  Tu as 3 travaux en cours :                                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 📝 Responsable comptable · Brouillon · 73 % · Modifié hier        │ │
│  │                                                  [Reprendre] [×]  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 📝 Commercial régional Genève · Brouillon · 45 % · Modifié il y a │ │
│  │ 5 jours                                         [Reprendre] [×]   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 📝 Assistante RH · Validé · 100 % · Modifié le 15.04.2026         │ │
│  │                                                  [Ouvrir] [×]     │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│                                  [+ Nouveau cahier des charges]         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Phase 6 — Vérifications qualité

### Écran dédié après clic "Valider et générer les annonces"

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Vérifications en cours                                   3/6 terminées │
│                                                                         │
│  ✓ Cohérence interne du document                         [Terminé - OK] │
│  ✓ Pourcentages de temps par mission                     [Terminé - OK] │
│  ✓ Cohérence avec le profil de ton entreprise            [Terminé - OK] │
│  ⧗ Détection de stéréotypes de genre                     [En cours - 8s]│
│  ⋯ Conformité anti-discrimination (LEg)                  [En attente]   │
│  ⋯ Obligation d'annonce ORP                              [En attente]   │
│                                                                         │
│  Estimation totale : 45 secondes                                        │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Alertes déjà identifiées (2)                                           │
│                                                                         │
│  ⚠️ Incohérence : le poste mentionne l'encadrement de 3 personnes       │
│     dans la mission 2, mais le champ "Subordonnés directs" est à 0.    │
│     [Voir] [Ignorer]                                                    │
│                                                                         │
│  ⚠️ Formulation vague : "Gérer les dossiers clients" en mission 3 est  │
│     trop générique.  Suggestion : "Instruire les demandes clients      │
│     entrantes, qualifier les besoins, proposer des solutions."         │
│     [Appliquer] [Voir] [Ignorer]                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Proposition de relecture LLM (self-review)

À la fin des checks déterministes (rapides), si l'utilisateur n'a pas désactivé cette option dans les paramètres entité, une fenêtre propose :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  💡 Tu veux que je relise ton cahier des charges en profondeur ?        │
│                                                                         │
│  Je peux vérifier les incohérences subtiles, les formulations vagues,  │
│  les stéréotypes, les anglicismes inutiles.                             │
│                                                                         │
│  ⏱ Estimation sur ton poste : 30-45 secondes                             │
│                                                                         │
│  Tu pourras interrompre à tout moment si tu en as vu assez.             │
│                                                                         │
│                                       [Non, je passe] [Oui, relis]      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Message adaptatif selon la vitesse machine mesurée :
- Rapide (< 30s) : "C'est rapide sur ton poste."
- Moyen (30-90s) : "Ça prend environ [X] secondes sur ton poste."
- Lent (> 90s) : "⚠️ Sur ton poste, ça prendra environ [X]. Tu peux préférer relire toi-même."

### Si relecture acceptée — écran de progression par passes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Relecture en cours                                                     │
│                                                                         │
│  ✓ Cohérence inter-sections                              [Terminé]      │
│  ⧗ Détection de formulations vagues                      [En cours - 10s]│
│  ⋯ Détection de stéréotypes et biais                     [En attente]   │
│  ⋯ Détection d'anglicismes et blabla corporate           [En attente]   │
│                                                                         │
│                                              [Interrompre la relecture] │
│                                                                         │
│  Les alertes arrivent au fur et à mesure dans le panneau de droite.    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

L'utilisateur peut **interrompre à tout moment** — les alertes déjà détectées sont conservées.

### Écran de synthèse des alertes

Une fois toutes les vérifications terminées (ou interrompues), écran de synthèse :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Vérifications terminées                                                │
│                                                                         │
│  ✓ 4 vérifications passées sans alerte                                  │
│  ⚠️ 3 alertes informatives                                               │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Alertes à examiner                                                     │
│                                                                         │
│  1. [Cohérence] Le poste mentionne l'encadrement...                     │
│     [Corriger] [Ignorer]                                                │
│                                                                         │
│  2. [Formulation] "Gérer les dossiers clients" est trop vague...        │
│     [Appliquer suggestion] [Voir] [Ignorer]                             │
│                                                                         │
│  3. [Stéréotype] Les compétences du profil tendent à être...            │
│     [Voir suggestions] [Ignorer]                                        │
│                                                                         │
│                                                                         │
│  [← Retour à l'édition]  [Poursuivre vers la génération des annonces]   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Important** : aucune alerte ne bloque le passage à la suite. L'utilisateur décide.

---

## 9. Phase 7 — Génération des 4 formats d'annonce

Voir **03_FORMATS_ANNONCES.md §6** pour le layout de l'écran de génération en grille 2×2 et les interactions d'édition fine.

Phase omise si l'utilisateur a choisi "Je formalise un poste interne" en phase 2.

---

## 10. Phase 8 — Export et archivage

### Écran de confirmation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  📦 Exporter ton pack                                                    │
│                                                                         │
│  Cahier des charges                                                     │
│  ☒ .docx (éditable)                                                     │
│  ☒ .pdf (lecture seule)                                                 │
│                                                                         │
│  Annonces                                                               │
│  ☒ Format 1 - Classique corporate (.docx + texte brut)                  │
│  ☒ Format 2 - Moderne narratif (.docx + texte brut)                     │
│  ☒ Format 3 - Bref plateforme (.docx + texte brut)                      │
│  ☒ Format 4 - ORP / Job-Room (.docx)                                    │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Archivage au catalogue                                                 │
│  ☒ Sauvegarder ce cahier des charges au catalogue de l'entité          │
│  Statut : ○ Validé ● Brouillon                                          │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│                           [← Retour] [Télécharger le pack]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Génération et téléchargement
1. Clic sur "Télécharger le pack" → barre de progression "Je prépare les fichiers... (5-10 secondes)"
2. Zip produit : `Pack_[IntitulePoste]_[Entite]_[Date].zip`
3. Téléchargement automatique via le navigateur (ou bouton explicite selon la plateforme)
4. Confirmation à l'écran : "✓ Pack téléchargé · [Lien] Voir dans le catalogue"

### Mise à jour du catalogue
- Le cahier des charges est ajouté (si nouveau) ou mis à jour (si révision)
- Version incrémentée automatiquement
- Tag de statut selon choix utilisateur (Validé / Brouillon)
- Journal d'audit mis à jour

---

## 11. Règles UX transverses

### Sauvegarde automatique
Toutes les 30 secondes pendant l'édition, sans action utilisateur. Aucune perte de données possible en cas de crash.

### Bouton "Annuler" sur toutes les actions longues
Toute opération de plus de 15 secondes doit avoir un bouton d'annulation visible.

### Feedback après 0,5 seconde
Dès qu'une action prend plus d'une demi-seconde, quelque chose bouge à l'écran. Jamais d'écran figé sans feedback.

### Raccourcis clavier globaux
- Ctrl+S : forcer la sauvegarde
- Ctrl+Z : annuler la dernière modification
- Ctrl+Shift+Z : rétablir
- Ctrl+K : ouvrir la palette de recherche rapide (sauter à une section)
- Échap : fermer le popup/modal en cours

### Tooltips et aide contextuelle
Bouton "?" en haut à droite de chaque écran qui ouvre une aide courte et actionnable. Pas de manuel de 40 pages.

### Mode "Première utilisation"
Quand un utilisateur ouvre le module pour la première fois, un walkthrough court (3-4 étapes) présente les zones principales. Saut possible à tout moment. Jamais réaffiché une fois dismissed.

### Accessibilité
- Navigation au clavier complète (Tab, Shift+Tab, Enter)
- Contraste WCAG AA
- Tailles de police minimum 11pt pour le corps
- Pas de rouge/vert uniquement pour signaler (toujours un pictogramme ou un texte)

---

**Fichier suivant à lire** : [05_CATALOGUE_POSTES.md](05_CATALOGUE_POSTES.md) — la persistance et le catalogue.
