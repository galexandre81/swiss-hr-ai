# 05 — Catalogue de postes par entité

Spécification de la persistance des cahiers des charges et du catalogue consultable.

---

## 1. Principe général

Chaque cahier des charges créé par l'utilisateur est automatiquement rangé dans un **catalogue propre à l'entité** active dans Arhiane. Le catalogue permet de retrouver, dupliquer, faire évoluer, comparer et archiver les cahiers des charges.

**Principe clé** : simplicité. Pas d'arborescence imposée, pas de dossiers, pas de workflow d'approbation, pas de structure rigide. Juste une liste plate filtrable + un regroupement optionnel par famille de métier.

---

## 2. Base de données

### Schéma SQLite (proposé)

```sql
-- Table principale : un enregistrement par version d'un poste
CREATE TABLE cahiers_des_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entite_id TEXT NOT NULL,                    -- Référence à l'entité Arhiane
    poste_id TEXT NOT NULL,                     -- Identifiant stable du poste (UUID)
    version TEXT NOT NULL,                      -- v1.0, v1.1, v2.0...
    intitule_poste TEXT NOT NULL,
    libelle_emploi_type TEXT,
    famille_metier TEXT,                        -- Administration, Finance, Commercial, etc.
    statut TEXT NOT NULL,                       -- 'brouillon', 'valide', 'archive'
    est_version_active BOOLEAN DEFAULT TRUE,    -- Une seule version active par poste_id
    contenu_json TEXT NOT NULL,                 -- Contenu complet du CdC en JSON
    cree_le DATETIME DEFAULT CURRENT_TIMESTAMP,
    cree_par TEXT NOT NULL,                     -- Utilisateur Arhiane
    modifie_le DATETIME DEFAULT CURRENT_TIMESTAMP,
    modifie_par TEXT,
    archive_le DATETIME,
    commentaire_version TEXT,                   -- Description des changements
    UNIQUE(poste_id, version)
);

CREATE INDEX idx_cdc_entite ON cahiers_des_charges(entite_id);
CREATE INDEX idx_cdc_poste ON cahiers_des_charges(poste_id);
CREATE INDEX idx_cdc_actif ON cahiers_des_charges(entite_id, est_version_active);
CREATE INDEX idx_cdc_famille ON cahiers_des_charges(entite_id, famille_metier);
CREATE INDEX idx_cdc_intitule ON cahiers_des_charges(intitule_poste);

-- Table de suppression logique (pour restauration pendant 30 jours)
CREATE TABLE cahiers_des_charges_supprimes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdc_id INTEGER NOT NULL,                    -- Référence l'ID original
    contenu_json TEXT NOT NULL,                 -- Backup complet
    supprime_le DATETIME DEFAULT CURRENT_TIMESTAMP,
    supprime_par TEXT NOT NULL,
    restaurable_jusquau DATETIME NOT NULL       -- supprime_le + 30 jours
);

-- Fichiers exportés (historique des exports)
CREATE TABLE exports_cdc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdc_id INTEGER NOT NULL REFERENCES cahiers_des_charges(id),
    type_export TEXT NOT NULL,                  -- 'cahier_des_charges', 'annonce_format_1', ..., 'pack'
    chemin_fichier TEXT NOT NULL,
    date_export DATETIME DEFAULT CURRENT_TIMESTAMP,
    exporte_par TEXT NOT NULL,
    taille_octets INTEGER
);
```

### Structure du JSON de contenu

```json
{
  "metadata": {
    "version_schema": "1.0",
    "cree_le": "2026-04-22T14:32:00Z",
    "cree_par": "marie.dupont@cabinet-xyz.ch",
    "langue": "fr"
  },
  "identification": {
    "version_document": "v1.0",
    "auteur": "Anne Dupont, Directrice RH",
    "version_remplacee": null,
    "entite": "Cabinet XYZ SA",
    "departement": "Direction générale",
    "entite_organisationnelle": null,
    "intitule_poste": "Responsable comptable et administratif",
    "libelle_emploi_type": null,
    "categorie_cadre": "cadre_operationnel",
    "lieu_travail": "Lausanne (VD)",
    "taux_activite": 100,
    "type_contrat": "CDI",
    "date_entree_prevue": "2026-07-01",
    "superieur_hierarchique": "Directrice générale",
    "nombre_subordonnes_directs": 2,
    "suppleance_remplace": "Directrice générale (aspects administratifs)",
    "suppleance_remplace_par": "Comptable senior"
  },
  "raison_detre": "Le ou la titulaire garantit la tenue comptable...",
  "missions_principales": [
    {
      "ordre": 1,
      "libelle": "Garantir la fiabilité des comptes et le respect des obligations légales et fiscales"
    },
    ...
  ],
  "missions_detaillees": [
    {
      "ordre": 1,
      "libelle": "Garantir la fiabilité...",
      "pourcentage_temps": 35,
      "activites": {
        "strategiques": [
          "Arbitrer les choix de provisions...",
          "Proposer à la direction..."
        ],
        "pilotage": [...],
        "operationnelles": [...],
        "support": [...]
      },
      "livrables_attendus": [...],
      "indicateurs_succes": [...]
    },
    ...
  ],
  "responsabilites_particulieres": {
    "applicable": true,
    "items": [...]
  },
  "relations": {
    "applicable": true,
    "internes": [...],
    "externes": [...]
  },
  "pouvoirs_decision": {
    "decisions_autonomes": [...],
    "decisions_proposees_validation": [...],
    "decisions_executees_instruction": [...],
    "budget_gere": "15'000 CHF/an, plafond 5'000 CHF/acte"
  },
  "profil_attendu": {
    "formation_base": [...],
    "formation_complementaire": [...],
    "experience": [...],
    "langues": [...],
    "connaissances_particulieres": "..."
  },
  "competences": {
    "socles": [...],
    "transversales": [...],
    "metier": [...],
    "managariales": [...]
  },
  "conditions_particulieres": {
    "applicable": true,
    "items": [...]
  },
  "signatures": {
    "mode_recrutement": false
  },
  "etats_completude": {
    "section_1": "complete",
    "section_2": "complete",
    ...
    "section_5": "non_applicable",
    ...
  },
  "historique_edition": [...]
}
```

---

## 3. Écran principal du catalogue

### Accès
Tuile dédiée dans le dashboard Arhiane : **"Catalogue des postes"**.

### Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  📂 Catalogue des postes · Cabinet XYZ SA                                │
│                                                                         │
│  [🔍 Rechercher un poste...]                                             │
│                                                                         │
│  Filtres : [Statut ▼] [Famille ▼] [Modifié ▼]    [Vue liste ◉ ○ Vue regroupée]│
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  12 postes dans le catalogue                                            │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 🟢 Responsable comptable et administratif                          │ │
│  │ Finance · 100 % · v1.0 · Modifié le 22.04.2026 par Marie Dupont   │ │
│  │                                 [Ouvrir] [Dupliquer] [⋯]          │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 🟡 Commercial régional Genève                                     │ │
│  │ Commercial · 100 % · v1.0 · Modifié le 18.04.2026                │ │
│  │                                 [Ouvrir] [Dupliquer] [⋯]          │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 🟢 Commercial régional Vaud                                        │ │
│  │ Commercial · 100 % · v2.0 · Modifié le 15.03.2026                │ │
│  │                                 [Ouvrir] [Dupliquer] [⋯]          │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 🟢 Assistante RH                                                   │ │
│  │ Administration · 80 % · v1.2 · Modifié le 02.03.2026              │ │
│  │                                 [Ouvrir] [Dupliquer] [⋯]          │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  [+ Nouveau cahier des charges]  [📤 Exporter la sélection]             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Colonnes visibles
- **Intitulé du poste** (cliquable → ouverture)
- **Statut** (🟢 Validé / 🟡 Brouillon / 🔴 Archivé)
- **Famille de métier**
- **Taux d'activité**
- **Version**
- **Date de dernière modification** + nom utilisateur
- **Actions** (Ouvrir, Dupliquer, Menu contextuel ⋯)

### Menu contextuel (⋯)
- Comparer avec un autre poste
- Voir l'historique des versions
- Archiver
- Supprimer (soft delete — restauration possible 30 jours)
- Exporter

### Filtres
- **Statut** : Tous / Validés / Brouillons / Archivés
- **Famille de métier** : Administration / Finance / Commercial / Technique / Support / Direction / Autre
- **Modifié** : Tous / 7 derniers jours / 30 derniers jours / Plus ancien

### Recherche
Recherche simple full-text sur l'intitulé du poste + libellé emploi-type + famille de métier. Pas besoin de recherche avancée en V1.

### Vue regroupée par famille de métier
Mode alternatif où les postes sont regroupés en accordéons par famille. Utile pour les entreprises qui structurent leur organigramme :

```
▼ Finance (3)
  🟢 Responsable comptable et administratif
  🟢 Comptable
  🟢 Contrôleur de gestion

▼ Commercial (4)
  🟡 Commercial régional Genève
  🟢 Commercial régional Vaud
  🟢 Responsable commercial
  🟢 Assistant commercial

▶ Administration (2)
▶ Direction (1)
▶ Support (2)
```

---

## 4. Les 4 gestes principaux détaillés

### Geste 1 — Ouvrir un cahier des charges existant

1. Clic sur l'intitulé ou bouton "Ouvrir"
2. Le module bascule en phase 5 (édition) avec le cahier des charges chargé
3. Journal d'audit : "Ouverture CdC [nom] par [user] le [date]"

Si le cahier des charges est 🟢 Validé, un message s'affiche en haut de la zone centrale :

```
⚠️ Ce cahier des charges est validé. Toute modification créera une nouvelle
   version (v1.1, v2.0...). Tu veux continuer ?
   [Annuler] [Créer une nouvelle version]
```

Si "Créer une nouvelle version" : bascule en phase 5 en mode édition, les modifications seront enregistrées comme nouvelle version au prochain save.

### Geste 2 — Dupliquer

1. Clic sur "Dupliquer"
2. Popup : "Dupliquer le poste '[nom]' ?"
3. Champ : "Nouveau nom du poste" (pré-rempli avec "[nom] — copie")
4. Bouton "Dupliquer"
5. Le module crée une nouvelle entrée au catalogue (nouveau `poste_id`) avec tout le contenu copié en v1.0
6. Bascule en phase 5 (édition) sur la nouvelle entrée
7. Journal d'audit : "Duplication de [nom original] vers [nouveau nom]"

### Geste 3 — Faire évoluer un poste (versioning)

Cas d'usage : le poste existe, ses missions ont évolué, on veut formaliser la v2.

1. Ouvrir le poste
2. Si Validé, l'outil propose "Créer une nouvelle version" (voir Geste 1)
3. L'utilisateur édite normalement en phase 5
4. À l'enregistrement, la nouvelle version devient active (`est_version_active = TRUE`), l'ancienne garde `est_version_active = FALSE` mais reste dans la DB
5. Numérotation automatique :
   - Changements mineurs (formulations, corrections) → v1.0 devient v1.1, v1.1 devient v1.2
   - Changements majeurs (nouvelles missions, réorganisation) → v1.0 devient v2.0
   - L'utilisateur choisit le type au moment de valider : "Changement mineur" / "Changement majeur"
6. Champ obligatoire lors de la création d'une nouvelle version : "Commentaire sur les changements" (libre, 1-2 lignes)

### Geste 4 — Comparer deux postes

1. Dans le catalogue, Shift+clic sur deux postes OU clic sur "Comparer" dans le menu contextuel d'un poste, puis sélection d'un second poste
2. Écran de comparaison côte à côte :

```
┌────────────────────────────────────┬────────────────────────────────────┐
│  📋 Responsable commercial          │  📋 Commercial régional             │
│  Commercial · Cadre opérationnel    │  Commercial · Collaborateur         │
│  100 % · CDI · Lausanne             │  100 % · CDI · Genève               │
├────────────────────────────────────┼────────────────────────────────────┤
│  2. Raison d'être                   │  2. Raison d'être                   │
│  Développer le portefeuille clients │  Prospecter et fidéliser des        │
│  de la région romande, manager une  │  clients PME en Suisse romande,    │
│  équipe de 4 commerciaux...         │  en autonomie...                    │
├────────────────────────────────────┼────────────────────────────────────┤
│  3. Missions (5)                    │  3. Missions (4)                    │
│  • 1. Piloter la stratégie commer-  │  • 1. Développer le portefeuille   │
│       ciale régionale               │       clients                       │
│  • 2. Encadrer l'équipe commerciale │  • 2. Prospecter de nouveaux       │
│  ...                                │       comptes                       │
├────────────────────────────────────┼────────────────────────────────────┤
│  ...                                │  ...                                │
└────────────────────────────────────┴────────────────────────────────────┘
```

Les différences sont surlignées. La comparaison est en lecture seule — pour éditer, l'utilisateur retourne au catalogue.

Utile pour décider d'une classification, d'une fourchette salariale relative, ou pour détecter des doublons non volontaires.

---

## 5. Historique des versions

Accessible via le menu contextuel ⋯ → "Voir l'historique des versions"

Écran :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Historique — Responsable comptable et administratif                    │
│                                                                         │
│  🟢 v1.2 (active) · 22.04.2026 · Marie Dupont                           │
│     Changement mineur · "Correction typo et ajout télétravail"         │
│     [Ouvrir] [Comparer avec v1.1]                                       │
│                                                                         │
│  v1.1 · 15.03.2026 · Marie Dupont                                       │
│     Changement mineur · "Ajout de la mission reporting financier"      │
│     [Ouvrir en lecture seule] [Restaurer comme version active]         │
│                                                                         │
│  v1.0 · 10.01.2026 · Marie Dupont                                       │
│     Création initiale                                                   │
│     [Ouvrir en lecture seule] [Restaurer comme version active]         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Restauration d'une ancienne version
Clic "Restaurer comme version active" → popup de confirmation → la version ciblée devient active, la version actuellement active passe en inactive mais reste dans l'historique.

Tout est tracé dans le journal d'audit.

---

## 6. Archivage

### Action "Archiver"
Accessible via le menu contextuel ⋯ → "Archiver"

1. Popup de confirmation : "Archiver le poste '[nom]' ?"
2. Champ optionnel : "Motif de l'archivage" (ex. "Poste supprimé en mars 2026")
3. Confirmation → statut passe à 🔴 Archivé
4. Le poste disparaît du catalogue par défaut
5. Accessible via le filtre "Statut = Archivé"
6. Toujours ouvrable en lecture seule, toujours restaurable

### Action "Restaurer de l'archive"
Depuis un poste archivé, menu contextuel → "Restaurer"
1. Confirmation
2. Statut repasse à 🟢 Validé (ou 🟡 Brouillon selon son statut d'origine)
3. Poste réapparaît dans le catalogue principal

---

## 7. Suppression (soft delete avec restauration 30 jours)

### Action "Supprimer"
Accessible via le menu contextuel ⋯ → "Supprimer"

1. Popup de **double confirmation** :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ⚠️ Supprimer le poste "[nom]" ?                                         │
│                                                                         │
│  Le poste sera supprimé du catalogue. Toutes ses versions (v1.0, v1.1,  │
│  v1.2) disparaîtront.                                                   │
│                                                                         │
│  Tu pourras le restaurer pendant 30 jours en allant dans                │
│  "Paramètres > Corbeille".                                              │
│                                                                         │
│  Tape "SUPPRIMER" pour confirmer :                                      │
│  [________]                                                             │
│                                                                         │
│                                      [Annuler] [Supprimer définitivement]│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

2. L'utilisateur tape "SUPPRIMER" puis clique
3. Le poste est déplacé dans `cahiers_des_charges_supprimes` avec `restaurable_jusquau = now + 30 jours`
4. Il n'apparaît plus nulle part dans le catalogue
5. Job de nettoyage (cron quotidien) supprime définitivement les entrées dont `restaurable_jusquau < now`

### Corbeille (accessible depuis les paramètres du module)
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  🗑️ Corbeille                                                            │
│                                                                         │
│  3 postes supprimés, restaurables jusqu'à leur date limite              │
│                                                                         │
│  🗑️ Stagiaire communication · Supprimé le 15.04.2026 ·                 │
│      Restaurable jusqu'au 15.05.2026                                    │
│      [Restaurer] [Supprimer définitivement]                             │
│                                                                         │
│  🗑️ Chauffeur-livreur · Supprimé le 02.04.2026 ·                       │
│      Restaurable jusqu'au 02.05.2026                                    │
│      [Restaurer] [Supprimer définitivement]                             │
│                                                                         │
│  🗑️ Responsable marketing digital · Supprimé le 20.03.2026 ·           │
│      Restaurable jusqu'au 20.04.2026 (⚠️ 2 jours restants)             │
│      [Restaurer] [Supprimer définitivement]                             │
│                                                                         │
│                                                                         │
│  [Vider la corbeille définitivement]                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Export groupé

### Accès
Depuis le catalogue, cases à cocher sur chaque ligne + bouton "Exporter la sélection" en bas.

### Options d'export groupé

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  📤 Exporter la sélection (5 postes)                                    │
│                                                                         │
│  Formats à inclure                                                      │
│  ☒ Cahier des charges (.docx)                                           │
│  ☒ Cahier des charges (.pdf)                                            │
│  ☐ Annonces (tous formats)                                              │
│                                                                         │
│  Fichier récapitulatif                                                  │
│  ☒ Sommaire (.xlsx) avec colonnes : Poste · Statut · Version · Taux ·  │
│    Famille · Date modif · Auteur                                        │
│                                                                         │
│  Nom du fichier zip : [Export_Catalogue_2026-04-22.zip]                 │
│                                                                         │
│                                          [Annuler] [Télécharger]        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Contenu du zip
```
Export_Catalogue_2026-04-22.zip
├── 00_SOMMAIRE.xlsx
├── 01_Responsable-comptable/
│   ├── Cahier_des_charges.docx
│   └── Cahier_des_charges.pdf
├── 02_Commercial-regional-Vaud/
│   ├── Cahier_des_charges.docx
│   └── Cahier_des_charges.pdf
├── 03_Assistante-RH/
│   └── ...
└── README.txt
```

### Cas d'usage
- Audit ISO / certification
- Due diligence (acquisition, cession)
- Inspection du travail
- Revue annuelle de l'organisation RH
- Transmission à un cabinet externe

---

## 9. Interaction avec le référentiel d'entité Arhiane

### Isolation multi-entité
Chaque entité Arhiane a son **propre catalogue isolé**. Impossible de voir les postes d'une autre entité même pour un admin.

Quand l'utilisateur bascule d'entité via le menu Arhiane (cohérent avec le spec existant), le catalogue affiché change automatiquement.

### Pré-remplissage depuis le référentiel d'entité

À la création d'un nouveau cahier des charges, les champs suivants sont pré-remplis depuis le référentiel d'entité :
- Logo (pour la page de garde du .docx)
- Nom de l'entité
- Canton (pour le lieu de travail par défaut)
- CCT applicable (pour le check de classification)
- Politique d'écriture inclusive (activée / désactivée par défaut)
- Langue principale
- Compétences socles (liste commune à tous les postes de l'entité, configurable dans les paramètres de l'entité)

---

## 10. Paramètres du module (au niveau entité)

Accessible depuis les paramètres Arhiane de l'entité :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ⚙️ Paramètres du module Cahier des charges                             │
│                                                                         │
│  Proposer la relecture LLM par défaut                                   │
│  ◉ Oui — proposer systématiquement                                      │
│  ○ Non — ne pas proposer automatiquement                                │
│                                                                         │
│  Écriture inclusive                                                     │
│  ◉ Activée                                                              │
│  ○ Désactivée                                                           │
│                                                                         │
│  Style d'écriture inclusive                                             │
│  ○ Doublets ("collaborateur·trice", "le/la")                           │
│  ◉ Formules neutres ("la personne titulaire")                          │
│  ○ Point médian ("collaborateur·trice")                                │
│                                                                         │
│  Ton par défaut des annonces                                            │
│  ◉ Formel                                                               │
│  ○ Moderne autorisé                                                     │
│                                                                         │
│  Compétences socles de l'entité (appliquées à tous les postes)          │
│  [+ Ajouter] Sens des responsabilités et éthique professionnelle        │
│             Capacité d'adaptation et flexibilité                        │
│             Écoute et communication                                     │
│                                                                         │
│  CCT applicable                                                         │
│  [Dropdown] Aucune / CCT Construction / CCT Hôtellerie / ... (à confi- │
│  gurer depuis le référentiel CCT d'Arhiane)                             │
│                                                                         │
│                                                     [Enregistrer]       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Performance attendue

- **Affichage du catalogue** (100 postes) : < 2 secondes
- **Recherche full-text** : < 500 ms
- **Ouverture d'un cahier des charges** : < 1 seconde
- **Sauvegarde d'une version** : < 500 ms
- **Duplication** : < 2 secondes
- **Export zip d'un catalogue complet** (50 postes) : < 30 secondes

---

## 12. Tests d'acceptation du catalogue

1. Création → édition → validation → retrouvaille dans le catalogue
2. Duplication d'un poste validé et ajustement → nouveau poste indépendant
3. Création d'une v2 d'un poste existant → v1 toujours accessible dans l'historique
4. Archivage → poste disparaît du catalogue par défaut, réapparaît avec filtre
5. Suppression → corbeille 30 jours, restauration possible
6. Recherche par mot-clé → résultats pertinents
7. Vue regroupée par famille de métier → accordéons fonctionnels
8. Export groupé de 5 postes → zip correctement structuré
9. Multi-entité : isolation stricte, aucun mélange possible
10. Pré-remplissage depuis référentiel d'entité : logo, nom, canton, CCT, compétences socles

---

**Fichier suivant à lire** : [06_GARDE_FOUS_QUALITE.md](06_GARDE_FOUS_QUALITE.md) — self-review LLM + checks déterministes.
