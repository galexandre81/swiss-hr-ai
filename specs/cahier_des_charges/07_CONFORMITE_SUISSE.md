# 07 — Conformité suisse

Détail des exigences légales et du référentiel factuel sur lesquels s'appuient les garde-fous qualité.

---

## 1. Panorama des cadres juridiques à respecter

Le module produit des documents (cahiers des charges et annonces d'emploi) qui sont sujets à plusieurs cadres juridiques suisses :

| Cadre | Portée | Risque si non conforme |
|-------|--------|------------------------|
| **Art. 53b OSE** (Ordonnance sur le service de l'emploi) | Obligation d'annonce ORP | Amende jusqu'à 40'000 CHF (art. 117a LEI) |
| **LEg** (Loi sur l'égalité) | Non-discrimination en raison du sexe | Action civile du candidat·e, jusqu'à 6 mois de salaire |
| **CO art. 328** | Protection de la personnalité (non-discrimination large) | Action civile, dommages-intérêts |
| **CCT étendue** (selon secteur) | Respect des conditions minimales salaire/horaires | Amende, contrôle |
| **LTr** (Loi sur le travail) | Durée du travail, protection santé | Amende, contrôle |
| **LPD** (Loi sur la protection des données) | Données personnelles des candidats | Amende (jusqu'à 250'000 CHF pour les personnes physiques) |

Le module ne prétend pas se substituer à un conseil juridique, mais il doit **prévenir les erreurs les plus courantes** et **signaler les cas sensibles** à la relecture humaine.

---

## 2. Obligation d'annonce ORP (art. 53b OSE)

### Contexte
Depuis le 1er juillet 2018, certaines professions à fort taux de chômage (seuil fixé par le Conseil fédéral) doivent être annoncées en priorité aux Offices régionaux de placement (ORP) avant toute publication externe. Le seuil est actuellement de **5 %** de chômage national dans la profession. La liste est mise à jour **annuellement** par le SECO.

### Procédure complète
Le module doit permettre à l'utilisateur de respecter cette procédure :

1. **Vérification préalable** : le poste est-il soumis ?
   - Matching de l'intitulé du poste avec la liste SECO (nomenclature CH-ISCO-08)
   - Résultat : "Oui / Non / À vérifier manuellement"

2. **Si soumis** : génération du Format 4 (ORP) selon spec 03_FORMATS_ANNONCES.md §5

3. **Soumission à Job-Room** (action utilisateur hors Arhiane) :
   - Via le portail https://www.job-room.ch (espace employeur)
   - Création d'une annonce avec les champs exacts du Format 4
   - Conservation de l'accusé de réception (date/heure = début du délai)

4. **Période d'exclusivité de 5 jours ouvrables**
   - Pendant ces 5 jours, **interdiction de publier l'annonce ailleurs**
   - 5 jours ouvrables = jours ouvrés excluant samedi, dimanche et jours fériés **cantonaux**
   - Calcul automatique proposé par l'outil avec rappel du canton d'application

5. **Examen des candidats ORP** (dans les 3 jours ouvrables suivant leur proposition)
   - L'ORP envoie des dossiers de candidats inscrits au chômage
   - L'employeur doit examiner et répondre dans les 3 jours

6. **Publication externe possible après J+5**
   - L'outil peut proposer un rappel dans le dashboard : "Ton annonce X sera publiable sur le marché externe le [date]"

### Liste SECO des professions soumises

**Structure du fichier `liste_orp_[annee].csv`** :

```csv
code_ch_isco_08,libelle_profession_fr,libelle_profession_de,libelle_profession_it,annee_applicable
1221,Directeurs des ventes et du marketing,Führungskräfte Vertrieb und Marketing,Dirigenti vendite e marketing,2026
3411,Professions intermédiaires en finance et comptabilité,Kaufmännische Sachbearbeiter,Tecnici contabili,2026
5221,Commerçants et marchands,Kaufleute,Commercianti,2026
...
```

### Procédure de mise à jour de la liste SECO

Chaque automne (vers novembre), le SECO publie la liste pour l'année suivante sur travail.swiss.

**Option A — Pack maintenance Arhiane** (payant) : Arhiane livre la nouvelle liste chaque janvier, automatiquement chargée.

**Option B — Mise à jour manuelle par l'utilisateur** :
1. L'utilisateur télécharge la liste officielle depuis https://www.arbeit.swiss (selon format fourni par le SECO, à adapter au CSV attendu par Arhiane)
2. Un script de conversion est fourni dans le dossier `references/tools/convert_seco_list.py` pour transformer le format officiel en format Arhiane
3. L'utilisateur dépose le fichier dans `references/liste_orp_[annee].csv`
4. Au prochain démarrage, Arhiane détecte la nouvelle liste et l'utilise

**Disclaimer obligatoire à afficher** dans le module si la liste a plus de 12 mois :
> ⚠️ Ta liste SECO date de [date]. Une version plus récente est peut-être disponible. Avant toute publication, vérifie-la directement sur https://www.arbeit.swiss (Check-Up). La responsabilité de la conformité ORP t'incombe.

### Interface spécifique ORP

Dans l'écran de génération des 4 formats (phase 7), le bloc Format 4 contient un **assistant de soumission** :

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Format ORP (Job-Room)                                                  │
│                                                                         │
│  ✅ Poste soumis à l'obligation d'annonce pour 2026                      │
│     Code CH-ISCO-08 proposé : 3411 - Professions intermédiaires en      │
│     finance et comptabilité                                             │
│                                                                         │
│  📋 Formulaire prêt à être copié dans Job-Room                          │
│  [Voir le formulaire] [Télécharger .docx]                               │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Suivi de la procédure                                                  │
│                                                                         │
│  ☐ J'ai soumis l'annonce à Job-Room                                     │
│    Date et heure de confirmation : [________________]                   │
│                                                                         │
│  → Date minimum de publication externe (J+5 ouvrables) : calcul auto    │
│                                                                         │
│  🌐 https://www.job-room.ch                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Quand l'utilisateur coche et saisit la date de confirmation ORP :
- L'outil calcule automatiquement la date J+5 ouvrables en tenant compte du canton
- Affiche un rappel dans le dashboard Arhiane
- Trace dans le journal d'audit

---

## 3. LEg et CO art. 328 — Non-discrimination

### Cadre juridique
- **LEg (Loi fédérale sur l'égalité entre femmes et hommes)** : interdit toute discrimination directe ou indirecte en raison du sexe dans l'emploi, y compris à l'embauche
- **CO art. 328** : protection générale de la personnalité du travailleur, interdit les discriminations plus largement (âge, origine, religion, santé, orientation sexuelle, état civil)

### Patterns interdits à détecter

Le module maintient une liste de patterns (expressions régulières + termes exacts) catégorisés :

#### Discrimination de genre
```python
patterns_genre = [
    r"\bmère de famille\b",
    r"\bpère de famille\b",
    r"\bmademoiselle\b",
    r"\bMlle\.",
    r"\bjeune femme\b",
    r"\bjeune homme\b",
    # + règle : si intitulé de poste sans H/F ni forme épicène
]
```

#### Discrimination d'âge
```python
patterns_age = [
    r"\bjeune\s+(?:diplômé|cadre|commercial|professionnel)",
    r"\b(?:moins|maximum)\s+de\s+\d+\s+ans\b",
    r"\b\d{2}\s*[-–à]\s*\d{2}\s+ans\b",
    r"\bdébutant(?:e)?\s+motivé(?:e)?\b",
    r"\bsenior\s+expérimenté\b",  # OK en formation, pas en qualificatif global
]
```

#### Discrimination d'origine
```python
patterns_origine = [
    r"\bde\s+langue\s+maternelle\s+\w+",
    r"\bnationalité\s+(?:suisse|européenne)\s+requise\b",
    # Exception : si poste diplomatique ou à habilitation gouvernementale
]
```

#### Discrimination santé/handicap
```python
patterns_sante = [
    r"\ben\s+(?:bonne|parfaite)\s+santé\b",
    r"\baucun\s+problème\s+de\s+santé\b",
    r"\bapte\s+physiquement\b",
    # Exception : si poste physique justifié (métier BTP, pompier, etc.)
]
```

### Suggestions de reformulation

Pour chaque pattern détecté, le module propose 2-3 reformulations alternatives :

| Original | Suggestion(s) |
|----------|---------------|
| "jeune commercial dynamique" | "commercial motivé et énergique" · "profil engagé" |
| "maximum 40 ans" | *(à supprimer — critère d'âge interdit)* |
| "de langue maternelle française" | "français C1 (maîtrise courante)" · "excellent niveau en français" |
| "en parfaite santé" | *(à supprimer sauf justification métier — reformuler la contrainte physique spécifique)* |
| "mère de famille" | *(à supprimer — aucun besoin de mentionner la situation familiale)* |

### Formulations épicènes recommandées

Dans la zone droite (copilote), un bouton "Proposer une formulation épicène" est actif sur toute sélection de texte contenant une forme genrée.

Trois styles disponibles (selon paramétrage entité) :
1. **Doublets** : "le ou la collaborateur·trice", "le candidat ou la candidate"
2. **Formules neutres** : "la personne titulaire", "les membres de l'équipe"
3. **Point médian** : "le·la collaborateur·trice" (style plus militant, moins répandu en Suisse)

Par défaut, recommander le style 2 (formules neutres) qui est le plus lu dans les documents officiels suisses romands (modèles Canton de Vaud).

---

## 4. Référentiel des familles de titres suisses

### Principe de conception
Le référentiel ne cherche pas à lister **tous** les titres individuels (impossible et redondant), mais les **familles** qui permettent un matching et une suggestion d'équivalence.

### Structure détaillée

#### Familles primaires (ordre décroissant de niveau)
1. **Doctorat / PhD** (niveau 8 CEC)
2. **Master** (niveau 7 CEC)
   - Master universitaire (5 ans)
   - Master HES / Master of Advanced Studies (MAS)
3. **Bachelor** (niveau 6 CEC)
   - Bachelor universitaire (3 ans)
   - Bachelor HES (3 ans)
4. **Diplôme fédéral** (niveau 6-7 CEC, tertiaire B)
5. **Brevet fédéral** (niveau 5-6 CEC, tertiaire B)
6. **École supérieure (ES)** (niveau 6 CEC, tertiaire B)
7. **Maturité** (niveau 4 CEC)
   - Maturité professionnelle (MP)
   - Maturité professionnelle spécialisée (MPS)
   - Maturité gymnasiale (MG)
8. **CFC** — Certificat fédéral de capacité (niveau 4 CEC, secondaire II)
9. **AFP** — Attestation fédérale de formation professionnelle (niveau 3 CEC)
10. **Scolarité obligatoire**

#### Fichier JSON complet
Fichier à produire : `references/diplomes_suisses.json` — structure proposée en 06_GARDE_FOUS_QUALITE.md §8.1.

### Équivalences internationales

Le fichier `references/equivalences_international.json` fait le lien entre familles suisses et titres internationaux courants. Il sert à :
- **Suggérer une formulation ouverte** (ex. "Bachelor en économie, HES ou équivalent reconnu")
- **Détecter un diplôme étranger potentiellement équivalent** dans une fiche importée
- **Bannir certaines formulations fermées** (ex. interdire "Bac+5 français requis" qui exclut les profils suisses et étrangers non-français)

**Règle absolue** : toute exigence de diplôme dans un cahier des charges **doit** être accompagnée de la mention "ou équivalent reconnu". Cette règle est :
- Forcée par le prompt système (Couche 1)
- Vérifiée par check déterministe 3.4 (Couche 3)

### Cas des diplômes étrangers : reconnaissance officielle

Pour information à afficher dans l'aide du module (infobulle ou page d'aide) :

> En Suisse, la reconnaissance officielle des diplômes étrangers est gérée par :
> - **SEFRI** (Secrétariat d'État à la formation, à la recherche et à l'innovation) pour les diplômes professionnels et les hautes écoles spécialisées
> - **Swissuniversities** pour les diplômes universitaires
>
> Un candidat qui dépose un diplôme étranger peut obtenir une attestation d'équivalence. L'employeur n'a pas l'obligation de la demander à l'embauche, mais elle peut être requise pour certaines professions réglementées (santé, enseignement, métiers de la loi).
>
> **Bonne pratique** : utiliser systématiquement "ou équivalent reconnu" dans les cahiers des charges pour ne pas fermer la porte à des candidats étrangers qualifiés.

---

## 5. CCT étendues — Conventions collectives

### Cadre
Certains secteurs d'activité sont soumis à une **convention collective étendue** (CCT étendue) par le Conseil fédéral, applicable à toutes les entreprises du secteur, même non-signataires.

**Exemples courants** :
- CCT Construction (bâtiment, génie civil)
- CCT Hôtellerie-Restauration
- CCT Nettoyage
- CCT Location de services (personnel temporaire)
- CCT Coiffure
- CCT Ferblanterie
- CCT Isolation

Liste officielle à jour : https://www.seco.admin.ch (Conventions collectives de travail)

### Implications pour le cahier des charges

Une CCT étendue impose typiquement :
- Salaire minimum par classe de fonction
- Durée maximale du travail
- Nombre de jours de vacances minimal
- 13e salaire obligatoire
- Indemnités spécifiques (déplacements, intempéries, heures supplémentaires)

### Référentiel CCT (`cct_etendues.json`)

Structure attendue :
```json
{
  "cct": [
    {
      "code": "CCT_CONSTRUCTION_2025",
      "libelle": "CCT nationale secteur principal construction",
      "secteurs_ch_isco_08": ["7111", "7112", "7113", "7114", "7115", "7119", "7120"],
      "cantons_applicables": "TOUS",
      "date_debut": "2025-01-01",
      "date_fin": "2028-12-31",
      "source_officielle": "https://www.seco.admin.ch/...",
      "grille_classification": [
        {
          "classe": "A",
          "libelle": "Chef de chantier",
          "salaire_mensuel_min_2025": 6800
        },
        {
          "classe": "C",
          "libelle": "Maçon qualifié",
          "salaire_mensuel_min_2025": 5900
        }
      ]
    }
  ]
}
```

### Check automatique de cohérence (Check 3.8)
Si l'entité a déclaré une CCT applicable dans ses paramètres, croiser :
- Le code CH-ISCO-08 du poste → inclus dans le périmètre de la CCT ?
- La classification proposée (si saisie) → cohérente avec les classes de la CCT ?
- Le salaire indicatif mentionné (si présent) → au-dessus du minimum de la CCT ?

Alerte informative, jamais bloquante.

### En V1 : périmètre restreint
Le référentiel CCT en V1 ne couvre que les **4-5 CCT les plus courantes** (Construction, Hôtellerie-Restauration, Nettoyage, Location de services). Pour les autres secteurs :
- Afficher un rappel générique : "Vérifie la cohérence avec ta CCT applicable, si elle existe"
- Pas de check automatique

Extension du référentiel : V1.5.

---

## 6. Nomenclature CH-ISCO-08

### Source
Classification suisse des professions, dérivée de ISCO-08 (International Standard Classification of Occupations). Source officielle : OFS (Office fédéral de la statistique).

### Structure hiérarchique
4 niveaux :
- Niveau 1 : Grand groupe (1 chiffre, 10 catégories)
- Niveau 2 : Sous-grand groupe (2 chiffres)
- Niveau 3 : Groupe de base (3 chiffres)
- Niveau 4 : Profession (4 chiffres, environ 400 professions)

### Utilisations dans le module
1. **Suggestion du code profession** pour le Format 4 (ORP)
2. **Matching** pour vérifier l'obligation d'annonce ORP
3. **Suggestion de famille de métier** dans le catalogue

### Format du référentiel (`ch_isco_08.json`)

```json
{
  "professions": [
    {
      "code": "3411",
      "libelle_fr": "Professions intermédiaires en finance et comptabilité",
      "libelle_de": "Kaufmännische Sachbearbeiter",
      "libelle_it": "Tecnici contabili",
      "niveau": 4,
      "parent_code": "341",
      "famille_metier_arhiane": "Finance"
    },
    ...
  ]
}
```

---

## 7. Disclaimers à afficher dans l'outil

### Disclaimer général du module
Affiché au premier lancement + lien permanent dans le menu d'aide :

> Arhiane — Module Cahier des charges
>
> Ce module t'aide à rédiger des cahiers des charges et des annonces
> d'emploi conformes aux standards suisses romands et aux obligations
> légales courantes. Il ne remplace pas un conseil juridique.
>
> Les documents produits doivent être relus et validés avant usage.
> La responsabilité éditoriale et juridique t'incombe.
>
> Pour les cas sensibles (licenciements, mobilité, contentieux), consulte
> un avocat spécialisé en droit du travail.

### Disclaimer conformité ORP
Affiché dans l'écran de vérification ORP (phase 6) et dans le format 4 :

> La vérification d'obligation d'annonce se base sur la liste SECO installée
> localement (version : [date]). Avant toute publication, vérifie la version
> actuelle sur travail.swiss. La responsabilité de la conformité ORP
> t'incombe. En cas de non-respect, l'amende peut atteindre 40'000 CHF
> (art. 117a LEI).

### Disclaimer LEg / non-discrimination
Affiché en contexte dans les alertes de checks 3.5 :

> Cette formulation peut être perçue comme discriminatoire au sens de la
> Loi sur l'égalité (LEg) ou de l'art. 328 CO. Un candidat peut intenter
> une action civile s'il estime avoir été écarté pour ce motif.

### Disclaimer référentiels obsolètes
Affiché si le référentiel a plus de 12 mois :

> ⚠️ Ton référentiel [X] date de [date]. Il est peut-être obsolète.
> Mets-le à jour via le pack maintenance ou manuellement depuis les sources
> officielles.

---

## 8. Protection des données (LPD)

### Application dans le module
Le module traite principalement des **données métier** (descriptions de postes, compétences, missions), pas des données personnelles au sens strict.

**Exceptions** :
- Le nom du signataire dans la section 11 du cahier des charges
- Le nom du titulaire (si identifié)
- Les noms des supérieurs hiérarchiques mentionnés

**Règles du module** :
- Ces données restent **locales** (air-gapped Arhiane)
- Aucun envoi réseau sortant
- Export contrôlé par l'utilisateur (fichiers .docx téléchargés sur son poste)
- Suppression avec corbeille 30 jours, puis suppression définitive

Pas de disclaimer LPD spécifique dans le module — le disclaimer général Arhiane suffit.

---

## 9. Cas particuliers cantonaux

### Genève — Communication des offres d'emploi (CCOE)
Depuis janvier 2021, Genève impose que certaines offres d'emploi soient communiquées à l'Office cantonal de l'emploi (OCE) **en plus** de l'ORP fédéral, pour certains secteurs.

**En V1** : mentionner cette particularité dans la documentation d'aide sans la gérer automatiquement. Extension V1.5 possible.

### Vaud — Préférence cantonale
Pas d'obligation supplémentaire par rapport au fédéral pour les annonces, mais recommandation d'indiquer les équivalences pour les formations cantonales (écoles professionnelles vaudoises).

### Autres cantons
Principalement alignés sur le cadre fédéral. Pas de spécificité gérée en V1.

---

## 10. Tests de conformité

### Test battery LEg
Jeu de 30 phrases "pièges" (avec et sans discrimination) → le module doit détecter correctement au moins 28 sur 30.

### Test battery ORP
Jeu de 20 intitulés de postes (mix de professions soumises et non-soumises) → le module doit classifier correctement au moins 18 sur 20.

### Test battery CCT
Jeu de 10 combinaisons poste / CCT → cohérence détectée correctement au moins 9 sur 10.

### Test de conformité .docx
Le .docx généré doit passer un **Accessibility Checker** de Word sans alerte critique (uniquement des warnings mineurs acceptables).

---

**Fichier suivant à lire** : [08_INTEGRATION_ARHIANE.md](08_INTEGRATION_ARHIANE.md) — intégration minimale avec Arhiane.
