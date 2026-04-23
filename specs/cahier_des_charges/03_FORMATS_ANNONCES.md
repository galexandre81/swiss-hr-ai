# 03 — Les 4 formats d'annonce d'emploi

Spécification détaillée des 4 formats d'annonce générés à partir d'un cahier des charges validé. Chaque format cible un canal de diffusion distinct avec ses propres contraintes.

---

## 1. Principe général

À partir d'un cahier des charges (source de vérité), le module génère **4 variantes d'annonce d'emploi** en parallèle, que l'utilisateur peut visualiser, éditer individuellement, comparer, puis exporter.

Chaque format est généré par un **appel LLM distinct**, avec un prompt spécifique qui applique les contraintes de format, de ton et de longueur.

Les 4 formats ne sont **pas des traductions** les uns des autres : ce sont des adaptations au canal de diffusion. Un même cahier des charges peut produire 4 annonces radicalement différentes en ton et en structure.

---

## 2. Format 1 — Classique corporate sobre

### Positionnement
Format le plus répandu en Suisse romande pour les entreprises établies (banques, assurances, services publics, PME traditionnelles, études d'avocats, fiduciaires). Ton factuel, structure attendue, sans superlatifs.

### Longueur cible
800 à 1'500 mots (3'500 à 6'000 caractères)

### Structure fixe

```
[Nom de l'entreprise]
[Accroche courte : 1-2 lignes de contexte entreprise]

[Intitulé du poste]
[Taux d'activité] · [Lieu de travail] · [Type de contrat]
Entrée en fonction : [Date] (ou "À convenir")

Votre mission
[Paragraphe de 3-5 lignes reformulant la Section 2 du cahier des charges]

Vos principales responsabilités
[Liste à puces de 5-8 responsabilités, issues des missions principales Section 3]
- [Responsabilité 1]
- [Responsabilité 2]
...

Votre profil
[Formation]
- [Titre de formation] ou équivalent reconnu
[Expérience]
- [X années] d'expérience dans [domaine]
[Compétences]
- [Compétence clé 1]
- [Compétence clé 2]
...
[Langues]
- Français : [niveau]
- [Autres langues] : [niveau]

Notre offre
[2-3 phrases sur le cadre, les avantages, la culture — à enrichir par l'utilisateur]

Si ce défi professionnel vous intéresse, merci de nous adresser votre dossier
de candidature complet (lettre de motivation, CV, copies de diplômes et
certificats de travail) à [contact].

[Nom entreprise] — [Adresse] — [Site web]
```

### Règles de rédaction imposées par le prompt LLM
- Vouvoiement systématique
- Pas de "tu", pas de ton familier
- Pas d'emojis, pas d'exclamations excessives
- Verbes à l'infinitif pour les missions
- Pas de néologismes corporate ("game-changer", "disruptif")
- Pas de superlatifs répétés ("exceptionnel", "unique", "extraordinaire")
- Mention systématique "ou équivalent reconnu" pour les diplômes

### Exemple court

```
Cabinet XYZ SA

Cabinet d'avocats actif depuis 1972 dans les domaines du droit des affaires
et du contentieux, nous recherchons pour compléter notre équipe de 15
collaborateurs :

Responsable comptable et administratif / administrative
100 % · Lausanne · CDI · Entrée en fonction : 1er juillet 2026

Votre mission

Vous garantissez la tenue comptable et le respect des obligations légales
et fiscales de notre étude. Vous encadrez une équipe de deux personnes et
assurez la relation avec notre fiduciaire et notre réviseur externe.

Vos principales responsabilités

- Établir les comptes annuels conformément aux normes CO et Swiss GAAP RPC
- Instruire les déclarations fiscales et les décomptes TVA
- Encadrer l'équipe comptable (2 personnes)
- Piloter la gestion administrative du personnel (contrats, paies, assurances)
- Assurer la relation avec le fiduciaire et l'organe de révision

Votre profil

- Brevet fédéral de spécialiste en finance et comptabilité, ou équivalent reconnu
- 5 ans d'expérience minimum en comptabilité d'entreprise
- Expérience souhaitée en environnement PME et encadrement d'équipe
- Maîtrise d'Abacus ou Sage 50
- Français : langue maternelle. Allemand : B1 souhaité.

Notre offre

Nous vous proposons un poste de responsabilité au sein d'une équipe stable
et bienveillante, avec une rémunération en adéquation avec vos compétences
et la possibilité de télétravail deux jours par semaine.

Si ce défi professionnel vous intéresse, merci d'adresser votre dossier
complet à rh@cabinet-xyz.ch d'ici au 31 mai 2026.

Cabinet XYZ SA · Rue du Bourg 12 · 1003 Lausanne · www.cabinet-xyz.ch
```

---

## 3. Format 2 — Moderne narratif

### Positionnement
Format plus récent, adapté aux scale-ups, entreprises tech, cabinets jeunes, structures attachées à leur culture d'entreprise. Ton plus engagé, storytelling sobre, sans tomber dans le corporate américain.

### Longueur cible
1'000 à 2'000 mots (4'500 à 8'500 caractères)

### Structure indicative (plus libre)

```
[Titre accrocheur en 1 phrase — pas "Rejoignez notre équipe !"]

[Paragraphe "Qui sommes-nous" : 4-6 lignes sur le pourquoi de l'entreprise,
son marché, son positionnement. Personnalité assumée.]

[Paragraphe "Pourquoi on recrute" : contexte précis du recrutement —
création de poste, remplacement, croissance. Transparence appréciée.]

[Section "Votre journée type" ou "Ce qui vous attend" : descriptif narratif
des missions, en "vous". Pas de liste à puces sèche, du texte qui se lit.]

[Section "Ce qu'on cherche" : profil reformulé en "vous savez", "vous avez",
"vous aimez". Le "ou équivalent" reste la règle.]

[Section "Ce qu'on offre" : honnête sur le cadre, les avantages réels, la
culture. Télétravail, formation, équipe, salaire (fourchette transparente
si l'entreprise le souhaite).]

[Call to action court et direct. Pas de formulaire bureaucratique.]
```

### Règles de rédaction imposées par le prompt LLM
- Vouvoiement (pas de tutoiement même dans ce format — Suisse romande)
- Un peu d'humanité dans le ton autorisée : "Nous cherchons", "On est convaincus que"
- Pas d'émoticônes sauf si l'entité l'a autorisé dans ses paramètres
- Pas d'anglicismes corporate gratuits
- Transparence privilégiée : mentionner explicitement télétravail, salaire, croissance
- Mentions légales conformes LEg (pas de "jeune et dynamique", pas de critères d'âge)

### Exemple court

```
Vous aimez les chiffres qui racontent des histoires ? Rejoignez le cabinet XYZ.

Qui sommes-nous

Cabinet d'avocats actif depuis plus de 50 ans dans le droit des affaires et
le contentieux, nous accompagnons des PME, des start-ups et des entreprises
familiales en Suisse romande. Notre approche : comprendre le business avant
d'appliquer le droit. Notre équipe de 15 personnes partage cette conviction
que la technique juridique n'a de valeur que si elle résout des problèmes réels.

Pourquoi on recrute

Notre responsable comptable et administrative part à la retraite après 22
ans de service. Elle a construit une fonction solide, bien structurée, sur
laquelle nous voulons continuer à nous appuyer. Nous cherchons la personne
qui prendra le relais et qui saura faire évoluer cette fonction avec les
outils d'aujourd'hui.

Ce qui vous attend

Vous serez responsable de la tenue comptable de l'étude et de l'ensemble
des obligations fiscales et légales. Vous encadrerez une équipe de deux
personnes (un comptable confirmé et une assistante) et serez notre
interlocuteur principal face au fiduciaire et au réviseur externe.

Une grande partie de votre temps sera consacrée à la production des
comptes et à la gestion administrative du personnel : contrats, paies,
affiliations sociales. Vous aurez aussi l'espace pour proposer des
améliorations de nos processus — nous avons commencé un projet de
digitalisation des notes de frais qui vous tendra les bras.

Ce qu'on cherche

Vous avez un brevet fédéral de spécialiste en finance et comptabilité (ou
équivalent reconnu) et au moins 5 ans d'expérience, idéalement en PME.
Vous connaissez Abacus ou Sage 50 — nous utilisons actuellement Abacus.
Vous êtes à l'aise en français et en allemand (B1 minimum pour les échanges
avec certains clients de Suisse alémanique).

Ce qu'on offre

Un poste de responsabilité à 100 %, en CDI, basé à Lausanne (centre), avec
deux jours de télétravail possibles par semaine.

La fourchette salariale pour ce poste est de 95'000 à 115'000 CHF bruts
annuels selon expérience (13e salaire inclus).

Une équipe stable : nous avons un turnover de moins de 5 % sur 10 ans.

Un budget formation de 2'000 CHF par an, géré par vous-même selon vos
besoins réels.

Intéressé·e ?

Envoyez-nous votre CV et deux lignes sur ce qui vous attire dans le poste
à anne.dupont@cabinet-xyz.ch. Pas besoin de lettre de motivation
formelle — on préfère les échanges authentiques.
```

---

## 4. Format 3 — Bref plateforme (jobup.ch / LinkedIn / Indeed)

### Positionnement
Format ultra-condensé pour les plateformes de diffusion d'annonces où la concurrence est forte et où le candidat scanne rapidement. Accroche puissante, informations clés en premier, appel à l'action direct.

### Longueur cible
300 à 600 mots (1'500 à 3'000 caractères) — **contrainte dure : max 3'500 caractères pour LinkedIn**

### Structure fixe

```
[Accroche en 1-2 lignes : le titre + l'élément le plus attractif]

📍 [Lieu] · ⏱ [Taux] · 💼 [Type contrat] · 📅 [Date entrée]

🎯 VOTRE MISSION
[2-3 lignes résumant l'essentiel du poste]

✅ VOS RESPONSABILITÉS PRINCIPALES
• [3-5 puces, ultra-courtes, frappantes]

🎓 VOTRE PROFIL
• [Formation en une ligne, avec "ou équivalent"]
• [X années d'expérience en [domaine]]
• [2-3 compétences clés]
• [Langues avec niveau]

💡 CE QUE NOUS OFFRONS
• [3-4 puces : salaire si partagé, télétravail, avantages concrets]

📧 Candidature à [contact] · Plus d'infos : [lien]
```

### Règles de rédaction imposées par le prompt LLM
- **Emojis autorisés** pour structurer (📍, 🎯, ✅, 🎓, 💡, 📧) — mais pas plus de 1 par ligne
- Puces très courtes (80-100 caractères max par puce)
- Accroche optimisée pour le taux de clic (pas racoleuse, mais percutante)
- Informations factuelles en premier (où, quand, quoi)
- Mot-clé du métier dans l'accroche (pour le SEO des plateformes)

### Contraintes techniques plateforme
- Longueur totale ≤ 3'500 caractères (LinkedIn)
- Pas de formatage riche (gras/italique ignorés par certaines plateformes)
- Paragraphes courts
- Mention "h/f" ou formulation épicène dans le titre (LEg)

### Exemple court

```
Responsable comptable et administratif·ve (H/F) · Cabinet d'avocats · Lausanne

📍 Lausanne · ⏱ 100 % · 💼 CDI · 📅 Juillet 2026

🎯 VOTRE MISSION
Garantir la tenue comptable et les obligations fiscales d'un cabinet
d'avocats de 15 personnes. Encadrer une équipe de 2.

✅ VOS RESPONSABILITÉS
• Établir les comptes annuels (normes CO et Swiss GAAP RPC)
• Instruire les déclarations fiscales et décomptes TVA
• Encadrer l'équipe comptable (2 personnes)
• Piloter la gestion administrative du personnel
• Interface avec fiduciaire et réviseur externe

🎓 VOTRE PROFIL
• Brevet fédéral spécialiste finance & comptabilité (ou équivalent)
• 5 ans d'expérience minimum, idéalement en PME
• Maîtrise Abacus ou Sage 50
• Français C1, Allemand B1 souhaité

💡 NOTRE OFFRE
• CDI 100 %, CHF 95-115k bruts selon expérience
• 2 jours de télétravail possibles/semaine
• Budget formation 2'000 CHF/an
• Équipe stable, faible turnover

📧 Candidatures : rh@cabinet-xyz.ch · www.cabinet-xyz.ch
```

---

## 5. Format 4 — ORP (art. 53b OSE pour Job-Room)

### Positionnement
Format conforme à l'obligation légale d'annonce aux ORP pour les postes soumis (voir 07_CONFORMITE_SUISSE.md). Champs structurés selon l'article 53b OSE.

### Génération conditionnelle
**Ce format n'est généré que si** le check ORP en phase 6 a conclu "Soumis à l'obligation d'annonce". Sinon, la case correspondante dans la grille des 4 formats affiche un message :

> *"Ce poste n'est pas soumis à l'obligation d'annonce ORP pour 2026. Le format ORP n'est pas généré."*

L'utilisateur peut forcer la génération s'il souhaite quand même l'utiliser (double-check personnel).

### Structure fixe — champs obligatoires art. 53b OSE

Le format ORP n'est pas du texte libre : c'est un **document structuré champ par champ** pour permettre une copie facile dans les formulaires du portail Job-Room (travail.swiss).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FORMULAIRE D'ANNONCE ORP                            │
│            Conforme à l'art. 53b OSE — Obligation d'annonce             │
└─────────────────────────────────────────────────────────────────────────┘

CHAMPS OBLIGATOIRES POUR JOB-ROOM

1. Profession (nomenclature CH-ISCO-08)
   Code : [XXXXXX]
   Libellé : [Dénomination officielle]

2. Intitulé du poste (tel qu'affiché au candidat)
   [Intitulé libre]

3. Description du poste (texte)
   [Description en 500-1000 caractères, synthèse missions + profil]

4. Lieu de travail
   Canton : [XX]
   Commune : [Nom]

5. Taux d'activité
   [XX %]
   Temps minimal : [XX %]
   Temps maximal : [XX %]

6. Type de contrat
   [CDI / CDD / Stage / Apprentissage]
   Date de début : [DD.MM.YYYY]
   Date de fin : [DD.MM.YYYY si CDD, sinon "indéterminée"]

7. Exigences
   Formation : [Titre + "ou équivalent"]
   Expérience professionnelle : [X années dans [domaine]]
   Langues (niveau CEFR) :
     - Français : [niveau]
     - [Autres langues]
   Compétences techniques : [Liste courte]

8. Informations de contact
   Nom de l'entreprise : [Nom]
   Personne de contact : [Nom]
   Fonction : [Fonction]
   Adresse : [Adresse complète]
   Courriel : [Email]
   Téléphone : [+41 XX XXX XX XX]

9. Mode de candidature
   [Email / Postal / Formulaire en ligne]

┌─────────────────────────────────────────────────────────────────────────┐
│ PROCÉDURE — À RESPECTER IMPÉRATIVEMENT                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. Allez sur https://www.job-room.ch (espace employeur)                │
│ 2. Créez une nouvelle annonce avec les champs ci-dessus                │
│ 3. Conservez l'accusé de réception (date/heure = début du délai)       │
│ 4. Attendez 5 JOURS OUVRABLES minimum avant de publier ailleurs        │
│ 5. Examinez les candidats proposés par l'ORP dans les 3 jours          │
│                                                                         │
│ Non-respect : amende jusqu'à 40'000 CHF (art. 117a LEI)                │
└─────────────────────────────────────────────────────────────────────────┘

Date limite de publication externe : [Auto-calculée à J+5 ouvrables
dès confirmation de l'ORP, en tenant compte des jours fériés cantonaux]
```

### Règles spécifiques au format ORP
- **Pas d'embellissement narratif** : texte factuel, direct, sans marketing
- **Pas d'emojis** (on est dans un cadre légal)
- **Mention "ou équivalent reconnu"** obligatoire pour les diplômes (LEg + ouverture internationale)
- **Formulation épicène** obligatoire dans le titre et la description ("responsable comptable H/F" ou formulation neutre)
- **Code CH-ISCO-08** à rechercher dans le référentiel intégré (voir 07_CONFORMITE_SUISSE.md)
- **Champ "Description du poste"** : pas plus de 1000 caractères (contrainte Job-Room)

### Intégration au flux UX
Après génération, le format ORP inclut un **assistant de soumission** intégré (voir 04_UX_FLUX.md) :
- Une case à cocher "J'ai soumis l'annonce à Job-Room"
- Un champ "Date et heure de confirmation de l'ORP"
- Calcul auto de la date d'autorisation de publication externe
- Rappel affiché dans le tableau de bord : "Poste X en attente ORP jusqu'au [date]"

### Journalisation spécifique
Chaque génération d'annonce ORP est tracée dans le journal d'audit avec :
- Date de génération
- Poste concerné
- Code CH-ISCO-08 proposé
- Version de la liste SECO utilisée pour le check
- Date de confirmation ORP (si saisie)
- Date d'autorisation de publication externe (calculée)

En cas de contrôle cantonal ou d'amende, ces informations servent de preuve de conformité.

---

## 6. Écran de génération des 4 formats (phase 7 du flux UX)

### Layout
Grille 2×2 avec les 4 formats visibles simultanément :

```
┌────────────────────────────┬────────────────────────────┐
│                            │                            │
│   FORMAT 1                 │   FORMAT 2                 │
│   Classique corporate      │   Moderne narratif         │
│   [Preview 300 mots]       │   [Preview 300 mots]       │
│   📏 1'240 mots            │   📏 1'680 mots            │
│   ⏱ ~5 min lecture         │   ⏱ ~7 min lecture         │
│   [Éditer] [Exporter]      │   [Éditer] [Exporter]      │
│                            │                            │
├────────────────────────────┼────────────────────────────┤
│                            │                            │
│   FORMAT 3                 │   FORMAT 4                 │
│   Bref plateforme          │   ORP (Job-Room)           │
│   [Preview 300 mots]       │   [Preview structuré]      │
│   📏 520 mots              │   📏 Formulaire complet    │
│   ⏱ ~2 min lecture         │   ⚠️ Obligation d'annonce  │
│   [Éditer] [Exporter]      │   [Éditer] [Exporter]      │
│                            │                            │
└────────────────────────────┴────────────────────────────┘
```

### Actions disponibles sur l'écran
- **Éditer** un format : bascule en édition fine de ce format seul
- **Comparer 2 formats** côte à côte (sélection à la Shift+clic)
- **Régénérer un format** avec prompt ajusté (utilisateur peut préciser "plus court", "plus engageant", "moins formel")
- **Retour au cahier des charges** pour modifier la source (les 4 annonces seront régénérées, avec possibilité de préserver les éditions manuelles)
- **Exporter tout** en pack .docx + texte brut copiable

### Éditions manuelles préservées lors de la régénération
Quand l'utilisateur modifie manuellement une annonce puis retourne éditer le cahier des charges, et que les annonces sont régénérées : pop-up de confirmation :

> *"Tu as fait des modifications manuelles sur le Format 2 (Moderne narratif). Veux-tu (a) régénérer et écraser tes modifications, (b) fusionner intelligemment (l'outil tentera de préserver tes ajouts), (c) ne pas régénérer ce format ?"*

---

## 7. Export des annonces

### Formats d'export disponibles
- **.docx** : format éditable dans Word (pour envoyer à un responsable marketing, à une agence, pour intégration plateforme)
- **.pdf** : version figée
- **Texte brut copiable** : pour collage direct dans Job-Room, LinkedIn, jobup.ch (bouton "Copier dans le presse-papiers")

### Nommage automatique
Format : `Annonce_[Format]_[IntitulePoste]_[Entite]_[Date].[ext]`

Exemple : `Annonce_Classique_Responsable-Comptable_Cabinet-XYZ_2026-04-22.docx`

### Pack groupé
Bouton "Télécharger tout" produit un zip contenant :
- Le cahier des charges .docx et .pdf
- Les 4 annonces en .docx
- Les 4 annonces en texte brut
- Le formulaire ORP en .docx (si applicable)
- Un fichier `README.txt` expliquant le contenu et les prochaines étapes

Nommage du zip : `Pack_[IntitulePoste]_[Entite]_[Date].zip`

---

## 8. Tests d'acceptation des annonces

1. Les 4 formats sont générés en parallèle en **moins de 90 secondes** sur PC standard
2. Chaque format respecte ses **contraintes de longueur**
3. Le format ORP contient **tous les champs obligatoires** art. 53b OSE
4. Aucun format ne contient d'**anglicismes corporate** de la liste noire (game-changer, drive, mindset, etc.)
5. Aucun format ne contient de **formulation discriminatoire** (âge, genre, origine)
6. Les **titres épicènes** sont appliqués dans tous les formats (H/F ou formulation neutre)
7. Les **diplômes mentionnés** sont toujours accompagnés de "ou équivalent reconnu"
8. L'**édition manuelle** d'un format est préservée lors de modifications de la source (sauf si l'utilisateur demande explicitement la régénération)
9. Le **texte brut copiable** ne contient aucun caractère de formatage résiduel
10. Les **emojis** sont présents uniquement dans le Format 3, et de manière mesurée

---

**Fichier suivant à lire** : [04_UX_FLUX.md](04_UX_FLUX.md) — le flux utilisateur en 8 phases.
