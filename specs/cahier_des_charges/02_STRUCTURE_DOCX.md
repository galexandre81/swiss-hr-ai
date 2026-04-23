# 02 — Structure du cahier des charges .docx

Spécification détaillée de la structure du document livré par le module. Ce fichier est la **source unique de vérité** pour la génération du .docx — Claude Code doit s'y référer strictement.

---

## 1. Principe général

Le cahier des charges .docx est composé de **11 sections canoniques** inspirées des modèles officiels romands (État de Vaud, Genève, Fribourg, UNIGE, UNIL). La structure est figée en V1 — pas d'ajout/retrait de section sans validation explicite.

Deux dimensions de structuration coexistent :

### Dimension A — Hiérarchie Word native
- **Titre 1** : sections principales (11)
- **Titre 2** : sous-sections, missions
- **Titre 3** : sous-regroupements (typologie d'activités)
- Styles natifs Word pour permettre la génération automatique de table des matières et la navigation

### Dimension B — Typologie d'activités [S/P/O/Su]
Dans la Section 4, chaque activité est préfixée par son code typologique :
- **[S] Stratégique** — décisions, arbitrages, représentation
- **[P] Pilotage** — coordination, supervision, contrôle
- **[O] Opérationnel** — exécution, cœur de métier
- **[Su] Support** — documentation, archivage, reporting transverse

Préfixe textuel entre crochets en début d'activité, en petite capitale. Option visuelle avec pastilles colorées reportée en V1.5.

---

## 2. Page de garde

Avant la Section 1, une page de garde générée automatiquement avec :

- **Logo de l'entité** (chargé depuis le référentiel d'entité Arhiane, optionnel si pas de logo)
- **Titre** : "Cahier des charges"
- **Intitulé du poste** (en gros)
- **Nom de l'entité / service**
- **Version et date** : v1.0 — 22 avril 2026
- **Mention légère discrète si document incomplet** : "Document de travail — [date]" (voir §12)

Mise en page sobre, non décorative, neutre. Pas de personnalisation esthétique par entité en V1 (reporté V1.5).

---

## 3. Section 1 — Identification

**Style Titre 1** : "1. Identification"

Tableau à deux colonnes (libellé / valeur) avec les champs suivants :

| Champ | Source | Type |
|-------|--------|------|
| Version du document | Auto | v1.0, v1.1, v2.0... |
| Date d'établissement | Auto | DD.MM.YYYY |
| Auteur (responsable hiérarchique) | Utilisateur | Texte libre |
| Version remplacée (si applicable) | Auto | v0.9, v1.0... ou "—" |
| Entité | Référentiel entité | Pré-rempli |
| Département / service | Utilisateur | Texte libre |
| Entité organisationnelle | Utilisateur | Texte libre, optionnel |
| Intitulé libre du poste | Utilisateur | Texte |
| Libellé emploi-type (si existant) | Utilisateur | Texte libre, optionnel |
| Catégorie de cadre | Sélection | Dropdown : Cadre stratégique / Cadre opérationnel / Cadre intermédiaire / Collaborateur spécialisé / Collaborateur / Apprenti |
| Lieu de travail | Utilisateur | Texte (canton + ville) |
| Taux d'activité | Utilisateur | % (100, 80, 60, 50, autre) |
| Type de contrat | Sélection | CDI / CDD (avec durée) / Stage / Apprentissage |
| Date d'entrée prévue | Utilisateur | DD.MM.YYYY, optionnel |
| Supérieur hiérarchique direct | Utilisateur | Nom ou intitulé de poste |
| Nombre de subordonnés directs | Utilisateur | Nombre (0, 1, 2, ...) |
| Suppléance : titulaire remplace | Utilisateur | Texte ou "—" |
| Suppléance : est remplacé par | Utilisateur | Texte ou "—" |

---

## 4. Section 2 — Raison d'être du poste

**Style Titre 1** : "2. Raison d'être du poste"

Paragraphe libre de 3 à 5 lignes qui synthétise la finalité du poste dans l'organisation. Répond à la question : "Si ce poste disparaissait demain, que perdrait-on ?"

**Généré par LLM** à partir du contexte et des tâches fournies. Éditable.

Contraintes de rédaction (imposées par prompt LLM) :
- Phrases complètes, pas de puces
- Verbes actifs
- Pas de superlatifs ("essentiel", "crucial", "clé")
- 300-400 caractères maximum

Exemple attendu :

> Le ou la titulaire garantit la tenue comptable et le respect des obligations fiscales et légales de l'entreprise. Il ou elle encadre une équipe comptable de deux personnes et assure la relation avec le fiduciaire externe et l'organe de révision. Le poste contribue à la fiabilité des décisions de gestion en produisant une information financière rigoureuse et à jour.

---

## 5. Section 3 — Missions principales

**Style Titre 1** : "3. Missions principales"

Liste numérotée de **4 à 7 missions** formulées à l'infinitif, par ordre d'importance décroissante.

**Chaque mission** :
- Commence par un verbe à l'infinitif précis (bannir "faire", "gérer", "mettre en place" sans complément, "être responsable de")
- Tient en une ligne (80-120 caractères)
- Exprime une finalité, pas une tâche

**Verbes recommandés** (à suggérer par le LLM) : Assurer, Garantir, Développer, Coordonner, Piloter, Superviser, Élaborer, Conduire, Représenter, Instruire, Arbitrer, Négocier.

Exemple :

```
3. Missions principales

1. Garantir la fiabilité des comptes et le respect des obligations légales et fiscales
2. Piloter la gestion administrative du personnel
3. Encadrer l'équipe comptable
4. Assurer la relation avec les partenaires externes (fiduciaire, réviseur, autorités)
5. Contribuer au pilotage financier de l'entreprise
```

Pas de description développée ici — le détail vient en Section 4.

---

## 6. Section 4 — Missions et activités détaillées

**Style Titre 1** : "4. Missions et activités détaillées"

C'est la section la plus riche, structurée en sous-sections.

Pour chaque mission de la Section 3 (reprise verbatim), un bloc **Titre 2** avec :

### Structure d'un bloc mission

```
4.1 Mission 1 — [Intitulé de la mission]                    [XX % du temps]

[Sous-titre 3] Activités stratégiques
  • [S] Activité 1
  • [S] Activité 2

[Sous-titre 3] Activités de pilotage
  • [P] Activité 1
  • [P] Activité 2
  • [P] Activité 3

[Sous-titre 3] Activités opérationnelles
  • [O] Activité 1
  • [O] Activité 2
  ...

[Sous-titre 3] Activités support
  • [Su] Activité 1

[Encadré gris] Livrables attendus :
  - Livrable 1 avec délai si applicable
  - Livrable 2

[Encadré gris] Indicateurs de succès :
  - Indicateur 1 (mesurable)
  - Indicateur 2
```

### Règles de rédaction des activités
- Commencer par un verbe à l'infinitif précis
- Une ligne par activité (120-150 caractères max)
- Entre 3 et 10 activités par mission (toutes typologies confondues)
- Toutes les 4 typologies [S/P/O/Su] ne sont pas obligatoirement présentes dans chaque mission (un exécutant n'a pas d'activités [S])
- Les sous-titres "Activités stratégiques / de pilotage / opérationnelles / support" n'apparaissent que si la typologie correspondante a au moins une activité

### Règles des pourcentages de temps
- Chaque mission a un % explicite en fin de Titre 2
- **La somme des % doit faire exactement 100 %**
- Granularité : par pas de 5 % (5, 10, 15, 20, 25, 30...)
- Cohérence vérifiée par check déterministe (voir 06_GARDE_FOUS_QUALITE.md)

### Règles des livrables et indicateurs
- Toujours présents (au moins 1 livrable et 1 indicateur par mission)
- Livrables : tangibles, datés si possible ("Comptes annuels au 31 mars", "Rapport trimestriel")
- Indicateurs : mesurables et observables ("Délai moyen < 48h", "Zéro redressement TVA sur 3 ans")

### Exemple complet d'un bloc mission

```
4.1 Mission 1 — Garantir la fiabilité des comptes et le respect des obligations
    légales et fiscales                                              [35 % du temps]

Activités stratégiques
  • [S] Arbitrer les choix de provisions et d'évaluations comptables en
        coordination avec la direction et le réviseur externe
  • [S] Proposer à la direction les évolutions de la politique comptable
        et fiscale de l'entreprise

Activités de pilotage
  • [P] Superviser le travail du comptable junior : revue mensuelle des
        écritures, validation des clôtures intermédiaires
  • [P] Coordonner le processus de clôture annuelle avec le fiduciaire
        et l'organe de révision

Activités opérationnelles
  • [O] Établir les comptes annuels selon les normes CO (art. 957 ss) et
        Swiss GAAP RPC applicables
  • [O] Instruire les déclarations d'impôt et décomptes TVA trimestriels
  • [O] Traiter les opérations comptables complexes (leasings, produits
        financiers, immobilisations)

Activités support
  • [Su] Documenter les procédures comptables dans le manuel qualité interne
  • [Su] Archiver les pièces justificatives selon la durée légale (10 ans)

┌─ Livrables attendus ──────────────────────────────────────────────────┐
│ • Comptes annuels clôturés au 31 mars N+1                            │
│ • Déclarations TVA déposées dans les délais légaux                   │
│ • Dossier de révision remis 15 jours avant l'AG                      │
└──────────────────────────────────────────────────────────────────────┘

┌─ Indicateurs de succès ───────────────────────────────────────────────┐
│ • Zéro redressement TVA sur 3 ans                                    │
│ • Délai moyen de clôture mensuelle < 10 jours ouvrables              │
│ • Rapport de révision sans réserve                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Section 5 — Responsabilités particulières

**Style Titre 1** : "5. Responsabilités particulières"

Liste d'éventuelles responsabilités complémentaires hors cadre opérationnel standard :

- Mandats spécifiques (participation au comité de direction, au COPIL d'un projet)
- Représentation externe (associations professionnelles, événements clients)
- Fonctions transverses (référent QHSE, représentant du personnel, gestionnaire de l'apprentissage)
- Participation à des groupes de travail inter-services

Format : puces courtes, une ligne par responsabilité.

Section toggable **"Non applicable"** si le poste n'en a pas — alors la section est marquée "—" et exclue de la Table des matières.

---

## 8. Section 6 — Relations et interactions

**Style Titre 1** : "6. Relations et interactions"

Deux sous-sections Titre 2 :

### 6.1 Relations internes

Tableau à trois colonnes : **Interlocuteur / Fréquence / Objet**

Exemple :
| Interlocuteur | Fréquence | Objet |
|---------------|-----------|-------|
| Direction générale | Mensuelle | Reporting financier, arbitrages stratégiques |
| Chefs de département | Mensuelle | Suivi budgétaire, validations achats |
| Équipe comptable (2 pers.) | Quotidienne | Encadrement, coordination |
| Service RH | Hebdomadaire | Paies, affiliations sociales |

### 6.2 Relations externes

Tableau identique : **Interlocuteur / Fréquence / Objet**

Exemple :
| Interlocuteur | Fréquence | Objet |
|---------------|-----------|-------|
| Fiduciaire externe | Mensuelle | Clôtures, déclarations fiscales |
| Organe de révision | Annuelle | Révision des comptes |
| Administration fiscale | Ponctuelle | Déclarations, contrôles |
| Caisse AVS / LPP | Ponctuelle | Affiliations, questions techniques |

Section toggable "Non applicable" si hors propos (rare — applicable à presque tous les postes).

---

## 9. Section 7 — Pouvoirs de décision et autonomie

**Style Titre 1** : "7. Pouvoirs de décision et autonomie"

**Section non négociable** dans un cahier des charges romand de qualité. Elle explicite l'équilibre responsabilités ↔ pouvoirs décisionnels.

Trois sous-sections Titre 2 :

### 7.1 Décisions autonomes
Ce sur quoi le titulaire décide seul, sans validation.
*Exemple : "Planification hebdomadaire de l'équipe comptable", "Réponse aux demandes courantes du personnel sur la paie", "Validation des factures fournisseurs jusqu'à 5'000 CHF"*

### 7.2 Décisions proposées à validation
Ce que le titulaire prépare et soumet pour validation hiérarchique.
*Exemple : "Provisions comptables significatives", "Changement de méthode de valorisation des stocks", "Recrutement au sein de l'équipe comptable"*

### 7.3 Décisions exécutées sur instruction
Ce que le titulaire met en œuvre sur décision d'un niveau supérieur.
*Exemple : "Arbitrages fiscaux majeurs (> 50'000 CHF d'impact)", "Décisions de politique salariale"*

### 7.4 Budget géré (si applicable)
Montant et périmètre du budget dont le titulaire a la responsabilité.
*Exemple : "Budget achats comptabilité : 15'000 CHF/an. Plafond d'engagement par acte : 5'000 CHF."*

---

## 10. Section 8 — Profil attendu

**Style Titre 1** : "8. Profil attendu"

Cinq sous-sections Titre 2 :

### 8.1 Formation de base
| Titre | Exigé | Souhaité |
|-------|-------|----------|
| [Titre de formation] **ou équivalent reconnu** | ☐ | ☐ |
| [Titre alternatif] **ou équivalent reconnu** | ☐ | ☐ |

**Règle absolue** : toujours ajouter "ou équivalent reconnu" derrière un titre spécifique. Ne jamais exiger un diplôme strict qui exclurait les candidats formés à l'étranger (voir 07_CONFORMITE_SUISSE.md).

### 8.2 Formation complémentaire
Mêmes colonnes qu'au 8.1, pour formations continues, brevets, certifications.

### 8.3 Expérience professionnelle
Tableau : **Domaine ou activité / Années minimum**
| Domaine | Années |
|---------|--------|
| Comptabilité en entreprise | 5 ans |
| Encadrement d'équipe | 2 ans |
| Environnement PME (< 100 collaborateurs) | Souhaité |

### 8.4 Langues
Tableau : **Langue / Niveau CEFR / Exigé / Souhaité**
| Langue | Niveau | Exigé | Souhaité |
|--------|--------|-------|----------|
| Français | C1 (maîtrise courante) | ☒ | ☐ |
| Allemand | B1 (intermédiaire) | ☐ | ☒ |
| Anglais | B2 (bon niveau) | ☐ | ☒ |

### 8.5 Connaissances et capacités particulières
Texte libre : logiciels métier, permis, habilitations, certifications.
*Exemple : "Maîtrise d'Abacus ou Sage 50. Connaissance souhaitée des normes Swiss GAAP RPC. Permis de conduire catégorie B."*

---

## 11. Section 9 — Compétences

**Style Titre 1** : "9. Compétences"

**Structuration en 4 sous-sections Titre 2**, inspirée du modèle vaudois :

### 9.1 Compétences socles
Compétences communes à tous les postes de l'entité (pré-remplies depuis le référentiel d'entité si configuré, sinon proposition LLM).
*Exemples : "Sens des responsabilités et éthique professionnelle", "Capacité d'adaptation", "Écoute et communication"*

### 9.2 Compétences transversales
Compétences spécifiques au poste, à sélectionner dans un référentiel commun.
- Entre 3 et 5 compétences
- Format puce courte
*Exemples : "Organisation et gestion du temps", "Vision globale et sens de la perspective", "Gestion de conflits"*

### 9.3 Compétences métier
Rédaction libre, spécifique au domaine du poste.
- Entre 3 et 8 compétences métier
*Exemples : "Maîtrise approfondie de la comptabilité financière CO", "Expertise en fiscalité des entreprises suisses", "Capacité à dialoguer avec des auditeurs externes"*

### 9.4 Compétences managériales
**Section conditionnelle** : apparaît uniquement si le champ "Nombre de subordonnés directs" en Section 1 est > 0.
- Sinon, sous-section absente du document
*Exemples : "Leadership bienveillant", "Capacité de délégation", "Esprit de décision", "Gestion de la performance individuelle"*

---

## 12. Section 10 — Conditions particulières

**Style Titre 1** : "10. Conditions particulières"

Liste des contraintes et astreintes éventuelles :

- **Horaires** : travail en soirée, nuit, weekends, piquets
- **Déplacements** : fréquence, destinations, véhicule requis
- **Charge physique** : port de charges, station debout prolongée
- **Environnement** : travail en plein air, en entrepôt, en atelier
- **Confidentialité renforcée** : accès à données sensibles
- **Service de piquet** : conditions et rémunération si applicable
- **Contraintes vestimentaires ou d'hygiène** : uniforme, EPI

Format : puces courtes.
Section toggable "Non applicable" si aucune condition particulière.

---

## 13. Section 11 — Signatures

**Style Titre 1** : "11. Signatures"

Deux blocs de signature :

### Employeur
```
Pour l'employeur :

Nom : ________________________________

Fonction : ____________________________

Date : _______________________________

Signature : ___________________________
```

### Titulaire
```
Le ou la titulaire atteste avoir pris connaissance du présent cahier
des charges et en accepte les termes.

Nom : ________________________________

Date : _______________________________

Signature : ___________________________
```

**Cas particulier** : si le cahier des charges est généré pour un recrutement (titulaire non encore identifié), remplacer le second bloc par la mention :

> *"Cahier des charges établi dans le cadre d'un processus de recrutement. Sera signé par le ou la titulaire à l'engagement."*

---

## 14. Pied de page et en-tête

### Pied de page (toutes les pages sauf page de garde)
Format : *"Cahier des charges — [Intitulé du poste] — v[X.Y] — [Date] — Page Y/Z"*
Police : 9pt, gris foncé
Alignement : centré

### En-tête (toutes les pages sauf page de garde)
Logo de l'entité à gauche (si disponible) + mention "Cahier des charges" à droite.
Police : 9pt, gris foncé.

---

## 15. Mention "Document de travail" (document incomplet)

Si au moins une section est en état "à faire" ou "partielle" au moment de l'export :

**En haut de la première page** (après page de garde), avant la Section 1 :

```
Document de travail — [date au format DD.MM.YYYY]
```

- Police : italique, taille 9pt, gris (pas rouge, pas alarmant)
- Style Word dédié : **`CDC_MentionBrouillon`**
- Facilement supprimable par l'utilisateur dans Word (un simple clic sur le paragraphe + Delete)

**Aucun filigrane diagonal**, pas de bandeau coloré sur les annonces, pas de mention récurrente en pied de page. On respecte le choix de l'utilisateur qui peut décider d'exporter un document incomplet.

---

## 16. Styles Word à définir (via python-docx)

Pour permettre une édition cohérente dans Word et une génération propre, définir explicitement les styles suivants :

| Style | Basé sur | Taille | Couleur | Gras | Italique |
|-------|----------|--------|---------|------|----------|
| `CDC_Titre1` | Heading 1 | 14pt | Noir | Oui | Non |
| `CDC_Titre2` | Heading 2 | 12pt | Noir | Oui | Non |
| `CDC_Titre3` | Heading 3 | 11pt | Gris foncé | Non | Oui |
| `CDC_Corps` | Normal | 11pt | Noir | Non | Non |
| `CDC_Puce` | List Bullet | 11pt | Noir | Non | Non |
| `CDC_Pourcentage` | Normal | 11pt | Noir | Oui | Non (aligné droite) |
| `CDC_Encadre` | Normal | 10pt | Gris foncé | Non | Non (fond gris clair) |
| `CDC_MentionBrouillon` | Normal | 9pt | Gris | Non | Oui |
| `CDC_PiedDePage` | Footer | 9pt | Gris foncé | Non | Non |

Polices : Calibri (corps) et Calibri (titres), conformément aux standards Word modernes.

---

## 17. Table des matières

Générer automatiquement une table des matières après la page de garde, basée sur les styles `CDC_Titre1` et `CDC_Titre2`. Niveau de profondeur : 2. Titre de la TDM : "Table des matières".

La TDM n'inclut **pas** la mention "Document de travail" ni les sections marquées "Non applicable".

---

## 18. Gestion des sections "Non applicable"

Certaines sections peuvent être marquées "Non applicable" par l'utilisateur (voir 04_UX_FLUX.md §édition). Dans ce cas :

- La section est **exclue de la table des matières**
- Le numéro de section est **préservé** (ex. si 5 est Non applicable, on voit 1, 2, 3, 4, 6, 7... dans la TDM)
- Dans le corps du document, la section n'apparaît pas du tout

Sections toggables "Non applicable" :
- Section 5 — Responsabilités particulières
- Section 6 — Relations et interactions (rare)
- Section 10 — Conditions particulières

Sections **non toggables** (toujours présentes) :
- 1 — Identification
- 2 — Raison d'être
- 3 — Missions principales
- 4 — Missions et activités détaillées
- 7 — Pouvoirs de décision
- 8 — Profil attendu
- 9 — Compétences
- 11 — Signatures

---

## 19. Tests d'acceptation de la génération .docx

Le .docx généré doit :

1. **Ouvrir sans erreur** dans Microsoft Word 365 (version 2024+), LibreOffice 7+ et Google Docs
2. **Conserver la navigation** : la TDM est cliquable, les styles sont correctement appliqués
3. **Respecter les styles définis** (voir §16)
4. **Avoir un pied de page** correct sur toutes les pages sauf page de garde
5. **Être éditable** : toutes les sections sont en texte normal modifiable, pas de zones verrouillées
6. **Gérer correctement les caractères spéciaux** suisses romands (accents, apostrophes typographiques)
7. **Être exportable en PDF** avec même rendu visuel
8. **Faire moins de 2 Mo** pour un cahier des charges standard (hors logo haute résolution)

---

**Fichier suivant à lire** : [03_FORMATS_ANNONCES.md](03_FORMATS_ANNONCES.md) — les 4 formats d'annonce d'emploi.
