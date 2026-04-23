# 06 — Garde-fous qualité

Spécification de l'ensemble des mécanismes de contrôle qualité du document généré.

---

## 1. Philosophie générale

Un LLM local comme Qwen 3.5 9B est capable de produire des cahiers des charges présentables — et c'est précisément ce qui est dangereux. Un document qui *semble* bon peut contenir des défauts subtils que le RH ne repère pas : incohérences, formulations vagues, stéréotypes, anglicismes, hallucinations factuelles.

Les garde-fous qualité sont l'ensemble des mécanismes qui détectent ces défauts avant qu'ils ne sortent de l'outil.

**Principe directeur** : toutes les alertes sont **informatives, jamais bloquantes**. L'utilisateur décide. L'outil signale, propose, suggère. Il ne censure jamais.

---

## 2. Architecture à 4 couches

```
┌────────────────────────────────────────────────────────────────────────┐
│  Couche 1 — Prompt système renforcé à la génération                    │
│  (Préventif : on dit au LLM ce qu'il ne doit pas faire dès le départ)  │
├────────────────────────────────────────────────────────────────────────┤
│  Couche 2 — Self-review LLM optionnel                                  │
│  (Détectif : on demande au LLM de relire et signaler ses erreurs)      │
├────────────────────────────────────────────────────────────────────────┤
│  Couche 3 — Checks déterministes (code non-LLM)                        │
│  (Vérification : faits vérifiables contre référentiel, cohérence)      │
├────────────────────────────────────────────────────────────────────────┤
│  Couche 4 — Invitation à la relecture humaine                          │
│  (Final : l'utilisateur décide, sa responsabilité éditoriale)          │
└────────────────────────────────────────────────────────────────────────┘
```

Chaque couche a un rôle précis et elles sont complémentaires.

---

## 3. Couche 1 — Prompt système renforcé

### Principe
Le prompt système qui instruit le LLM à la génération initiale contient explicitement une liste d'interdits et d'exigences. Première ligne de défense, préventive.

### Éléments clés du prompt (détails complets en 09_PROMPTS_LLM.md)

Extraits illustratifs :

```
Tu es un expert en rédaction de cahiers des charges pour PME suisses romandes.

RÈGLES ABSOLUES :

1. FACTUALITÉ
   - Ne jamais inventer de diplôme. Si tu ne connais pas le nom exact
     d'une formation, utilise une formulation générique (ex. "Bachelor HES
     ou équivalent reconnu" au lieu d'inventer "Bachelor HES en management
     des PME de Lausanne")
   - Toujours accompagner un titre de formation de "ou équivalent reconnu"
   - Ne jamais citer un article de loi (CO, LTr, LPD) si tu n'es pas sûr
     de son numéro exact et de son contenu

2. FORMULATION
   - Verbes à l'infinitif : "Garantir", "Coordonner", "Élaborer"
   - Verbes INTERDITS sans complément précis : "faire", "gérer" (seul),
     "mettre en place" (seul), "être responsable de" (seul),
     "être force de proposition"
   - Bannir les superlatifs répétitifs : "essentiel", "crucial", "clé"
   - Bannir les anglicismes corporate : "game-changer", "driver",
     "mindset", "synergies cross-fonctionnelles", "best practices"

3. NON-DISCRIMINATION (LEg / CO art. 328)
   - Ne JAMAIS mentionner : âge, sexe, origine, religion, orientation,
     état civil, santé (sauf exigence objective justifiée)
   - Formulations INTERDITES : "jeune et dynamique", "mère de famille",
     "junior motivé" (peuvent être vus comme âgiste ou genrés)

4. ÉQUITÉ DE GENRE
   - Équilibrer les compétences proposées (pas uniquement "empathie" pour
     un poste RH, pas uniquement "leadership" pour un poste technique)

5. TYPOLOGIE D'ACTIVITÉS
   - Toujours typer chaque activité : [S] stratégique, [P] pilotage,
     [O] opérationnel, [Su] support
   - Un poste de collaborateur peut n'avoir que des [O] et [Su]
   - Un poste de direction doit avoir au moins 2 [S] et 2 [P]

6. HONNÊTETÉ
   - Ne pas inventer d'éléments absents du briefing utilisateur
   - Si une section manque d'information, laisser un tag
     "À compléter — information insuffisante"

...
```

### Rôle
Ce prompt oriente le LLM dès la génération initiale. Il n'élimine pas toutes les erreurs (les LLM ont leurs biais d'entraînement qui ressortent), mais il en prévient beaucoup.

---

## 4. Couche 2 — Self-review LLM optionnel

### Principe
Après la génération initiale, le LLM relit son propre document avec un prompt de revue spécifique. C'est la technique "LLM-as-judge" de la recherche IA.

### Caractéristiques clés

**Optionnel** : proposé pédagogiquement à l'utilisateur avec estimation de durée, il peut refuser. Paramètre entité pour le comportement par défaut.

**Sur modèle léger** : utilise un modèle plus petit que le modèle principal (ex. Qwen 3B ou Phi 3.5) pour économiser le temps et la VRAM. Suffisant pour détecter des incohérences.

**En 4 micro-passes** : plutôt qu'une grosse passe monolithique, on découpe en 4 passes courtes et ciblées que l'utilisateur peut interrompre :

1. **Passe 1 — Cohérence inter-sections** (~10 secondes)
   - Les pourcentages font-ils 100 % ?
   - Le nombre de subordonnés vs les activités de pilotage
   - L'expérience vs la catégorie de cadre
   - Le lieu de travail vs les mentions de déplacements

2. **Passe 2 — Formulations vagues** (~15 secondes)
   - Détection des verbes creux ("gérer", "faire", "mettre en place")
   - Détection des phrases creuses ("être force de proposition", "dans le cadre de")
   - Suggestion de reformulation précise

3. **Passe 3 — Stéréotypes et biais** (~10 secondes)
   - Compétences genre-coded (empathie vs leadership)
   - Formulations pouvant être vécues comme discriminantes
   - Ouverture internationale du profil (diplôme non-suisse toléré)

4. **Passe 4 — Anglicismes et blabla corporate** (~10 secondes)
   - Détection des anglicismes gratuits
   - Détection du ton "corporate américain"
   - Suggestions en français idiomatique

### Interruption possible
L'utilisateur peut arrêter à tout moment. Les alertes déjà détectées dans les passes terminées sont conservées.

### Output structuré
Chaque passe produit un JSON d'alertes :

```json
{
  "passe": "formulations_vagues",
  "alertes": [
    {
      "id": "alerte_001",
      "severite": "moyenne",
      "section": "missions_detaillees",
      "sous_section": "Mission 3 — Activités opérationnelles",
      "bloc": "activité 1",
      "contenu_original": "Gérer les dossiers clients",
      "probleme": "Verbe 'gérer' utilisé seul, sans précision de ce qu'implique cette gestion",
      "suggestion": "Instruire les demandes clients entrantes, qualifier les besoins, proposer des solutions dans les 48h",
      "action_proposee": "remplacer"
    },
    ...
  ]
}
```

### Limitations honnêtes (à documenter)

Le self-review est très bon sur :
- Incohérences internes
- Formulations vagues
- Stéréotypes de genre
- Anglicismes et blabla corporate
- Ton inapproprié
- Omissions critiques

Il est **moins bon** sur :
- **Hallucinations factuelles** (diplômes inventés) — même le modèle qui a halluciné relit avec le même "faux souvenir"
- **Faits juridiques précis** (articles de loi mal cités)
- **Conformité à des référentiels externes** (liste SECO ORP, CCT applicables) qu'il ne peut pas vérifier sans les avoir en contexte

→ D'où la nécessité de la Couche 3 (checks déterministes) pour ces aspects précis.

---

## 5. Couche 3 — Checks déterministes

### Principe
Code Python classique, pas du LLM. Vérifications rapides (< 3 secondes au total), fiables, reproductibles. Tournent **systématiquement** et de manière **non négociable** à chaque validation.

### Liste des checks

#### Check 3.1 — Cohérence des pourcentages
- Somme des pourcentages des missions = 100 % exactement ?
- Chaque pourcentage est un multiple de 5 ?
- Aucune mission à 0 % ou > 70 % ?

**Alerte en cas d'échec** :
```
Les pourcentages de temps des missions font un total de 95 %.
Il doit être exactement 100 %.
[Proposer un rééquilibrage automatique] [Corriger manuellement]
```

#### Check 3.2 — Cohérence subordonnés vs activités de pilotage
- Si `nombre_subordonnes_directs > 0` → il doit y avoir au moins 2 activités [P] dans les missions
- Si `nombre_subordonnes_directs == 0` → aucune activité ne doit contenir "encadrer", "superviser", "manager" sans contexte

**Alerte en cas d'échec** :
```
Le poste mentionne 0 subordonnés directs, mais la mission 2 contient
des activités d'encadrement ("Superviser le travail du comptable junior").
Incohérence à vérifier.
```

#### Check 3.3 — Cohérence expérience vs catégorie de cadre
- Catégorie "Apprenti" → pas de "X années d'expérience" dans le profil
- Catégorie "Collaborateur" → expérience ≤ 5 ans typiquement
- Catégorie "Cadre opérationnel" → expérience ≥ 3 ans typiquement
- Catégorie "Cadre stratégique" → expérience ≥ 8 ans typiquement

**Alertes informatives** (ne bloquent pas, signalent les incohérences fortes)

#### Check 3.4 — Diplômes et équivalences
Croiser chaque titre mentionné dans "Formation de base" avec le référentiel de familles de diplômes suisses + équivalences internationales (voir 07_CONFORMITE_SUISSE.md §4).

**Règles** :
- Si titre reconnu dans le référentiel → OK
- Si titre non reconnu → alerte : "Le diplôme '[X]' ne correspond à aucune famille de titre dans notre référentiel. Vérifie l'intitulé exact ou utilise une formulation générique ('Bachelor HES ou équivalent reconnu')."
- Si titre mentionné **sans** la mention "ou équivalent reconnu" → alerte : "Le titre '[X]' n'est pas accompagné de la mention 'ou équivalent reconnu', ce qui peut fermer la porte aux candidats étrangers et être perçu comme discriminatoire. [Ajouter la mention]"

#### Check 3.5 — LEg / CO 328 — formulations discriminatoires
Scan du document complet avec une **liste de patterns interdits** :

Patterns âge :
- "jeune", "junior motivé", "débutant dynamique"
- "senior", "expérimenté" (dans les qualificatifs, pas dans la formation)
- mention d'âge ("25-35 ans", "moins de 40 ans")

Patterns genre :
- "mère de famille", "père de famille"
- "mademoiselle", "Mlle"
- formules genrées sans H/F ou formulation épicène

Patterns origine :
- "suisse" (sauf pour lieu de travail ou citoyenneté objectivement justifiée)
- "de langue maternelle française" (utiliser niveau CEFR à la place)

Patterns santé/handicap :
- "en bonne santé", "apte physiquement" (sauf si justifié par poste physique)

**Alertes en cas de détection** :
```
⚠️ Formulation potentiellement discriminatoire détectée (LEg / CO art. 328)

Section : "Profil attendu"
Phrase : "Nous cherchons un jeune commercial dynamique..."

Le mot "jeune" peut être interprété comme un critère d'âge, ce qui est
discriminatoire au sens de la Loi sur l'égalité.

Suggestions :
- "Nous cherchons un commercial motivé..."
- "Nous cherchons un profil énergique, capable de..."
- "Nous cherchons une personne engagée..."

[Appliquer une suggestion] [Ignorer]
```

#### Check 3.6 — Écriture inclusive (si activée dans les paramètres entité)
Scan du document pour :
- Formes masculines génériques non épicènes ("le titulaire", "les collaborateurs")
- Suggestion de reformulation selon le style configuré (doublets, neutre, point médian)

Alerte informative, jamais bloquante.

#### Check 3.7 — Obligation d'annonce ORP
Voir 07_CONFORMITE_SUISSE.md §2 pour la procédure complète.

- Matcher l'intitulé du poste avec la liste SECO chargée localement
- Si match → statut : "Soumis à l'obligation d'annonce pour [année]"
- Si pas de match → statut : "Non soumis"
- Si ambiguïté → statut : "À vérifier sur travail.swiss"

Résultat affiché dans l'écran de checks qualité + format ORP (Format 4) généré conditionnellement.

#### Check 3.8 — Cohérence CCT (si CCT configurée au niveau entité)
Si l'entité a déclaré une CCT applicable, croiser :
- Le niveau de classification proposé
- Les responsabilités du poste
- Le salaire proposé (si mentionné)

Vérifier la cohérence avec la grille de classification de la CCT.

**Note** : cette fonctionnalité dépend de la disponibilité des grilles CCT dans le référentiel. En V1, limiter aux CCT les plus courantes (Construction, Hôtellerie-Restauration, Nettoyage, Location de services). Autres CCT : afficher uniquement un rappel "Vérifiez la cohérence avec votre CCT applicable".

#### Check 3.9 — Cohérence avec le référentiel d'entité
- Lieu de travail vs cantons d'activité de l'entité
- Langue du document vs langue principale de l'entité (alerte si incohérence)
- Politique de télétravail vs mentions dans le document

---

## 6. Couche 4 — Invitation à la relecture humaine

### Principe
À la fin des vérifications (phase 6), un écran récapitulatif affiche toutes les alertes restantes avec une formulation claire :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ✅ J'ai produit ton cahier des charges et je l'ai relu.                 │
│                                                                         │
│  Voici ce que j'ai observé — libre à toi d'en tenir compte ou non :     │
│                                                                         │
│  • 3 incohérences internes signalées                                    │
│  • 5 formulations que j'estime trop vagues                              │
│  • 2 mentions de diplômes à vérifier contre mon référentiel             │
│  • 1 formulation potentiellement discriminatoire (LEg)                  │
│                                                                         │
│  La décision finale t'appartient. Tu peux :                             │
│                                                                         │
│  - Revenir à l'édition pour corriger point par point                    │
│  - Appliquer en masse mes suggestions                                   │
│  - Ignorer les alertes et continuer vers la génération des annonces     │
│                                                                         │
│  [← Retour à l'édition] [Appliquer tout] [Ignorer et continuer]         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Responsabilité éditoriale
Cohérent avec la posture Arhiane : **l'outil suggère, l'humain décide**. Le disclaimer général rappelle que la responsabilité éditoriale incombe à l'utilisateur.

---

## 7. Benchmark machine au premier lancement

### Objectif
Calculer dynamiquement les estimations de durée affichées à l'utilisateur pour que les messages soient crédibles et adaptés à sa machine.

### Procédure

**Au premier lancement d'Arhiane** (en parallèle du onboarding initial, invisible pour l'utilisateur) :

1. Le système lance un mini-benchmark du LLM principal (Qwen 3.5 9B) :
   - Prompt court standardisé
   - Mesure du temps pour générer 500 tokens
   - Calcul de la vitesse en tokens/seconde
   - 3 mesures consécutives, moyenne

2. Idem pour le LLM léger (Qwen 3B ou Phi 3.5) utilisé pour le self-review

3. Stockage dans la config Arhiane locale :
   ```json
   {
     "benchmark_llm_principal": {
       "tokens_per_second": 25.3,
       "date_mesure": "2026-04-22T10:30:00Z",
       "modele": "Qwen-3.5-9B-Q4_K_M"
     },
     "benchmark_llm_leger": {
       "tokens_per_second": 45.8,
       "date_mesure": "2026-04-22T10:30:00Z",
       "modele": "Phi-3.5-mini-Q4_K_M"
     },
     "categorie_machine": "moyenne"  // "rapide", "moyenne", "lente"
   }
   ```

### Catégorisation de la machine
Sur base des tokens/seconde mesurés :

| Catégorie | Vitesse (tokens/s) | Durée self-review estimée |
|-----------|--------------------|-------------------------|
| Rapide | > 40 | < 30 secondes |
| Moyenne | 15-40 | 30-90 secondes |
| Lente | < 15 | > 90 secondes |

### Affichage adaptatif
Les messages de l'UI s'adaptent (voir 04_UX_FLUX.md §8) :

- **Rapide** : *"Je peux relire et vérifier ton cahier des charges. C'est rapide sur ton poste."*
- **Moyenne** : *"Je peux relire et vérifier ton cahier des charges. Ça prend environ [X] secondes sur ton poste."*
- **Lente** : *"Je peux relire et vérifier ton cahier des charges. ⚠️ Sur ton poste, ça prendra environ [X]. Tu peux préférer relire toi-même."*

### Affinage au fil de l'usage
Chaque fois qu'une passe LLM complète s'exécute dans l'utilisation réelle, la mesure est stockée et une moyenne glissante affine l'estimation. Au bout de 3-5 utilisations, l'estimation devient très fiable.

### Re-calibrage manuel
Bouton "Recalibrer" dans les paramètres pour l'utilisateur qui aurait changé de machine ou upgradé son RAM / GPU.

---

## 8. Référentiel factuel minimal

### Contenu du référentiel (stocké localement)

#### 8.1 Familles de titres suisses (`diplomes_suisses.json`)

```json
{
  "titres_suisses": [
    {
      "famille": "Formation professionnelle initiale",
      "titres": [
        {"code": "AFP", "libelle": "Attestation fédérale de formation professionnelle", "duree": 2, "type": "apprentissage"},
        {"code": "CFC", "libelle": "Certificat fédéral de capacité", "duree": 3, "type": "apprentissage"}
      ]
    },
    {
      "famille": "Maturité",
      "titres": [
        {"code": "MP", "libelle": "Maturité professionnelle", "type": "maturite"},
        {"code": "MPS", "libelle": "Maturité professionnelle spécialisée"},
        {"code": "MG", "libelle": "Maturité gymnasiale"}
      ]
    },
    {
      "famille": "Formation professionnelle supérieure",
      "titres": [
        {"code": "BF", "libelle": "Brevet fédéral", "type": "brevet"},
        {"code": "DF", "libelle": "Diplôme fédéral", "type": "diplome"},
        {"code": "ES", "libelle": "École supérieure", "niveau": "tertiaire B"}
      ]
    },
    {
      "famille": "Haute école",
      "titres": [
        {"code": "BSc-HES", "libelle": "Bachelor of Science HES", "niveau": "Bachelor", "duree": 3},
        {"code": "BA-HES", "libelle": "Bachelor of Arts HES"},
        {"code": "MSc-HES", "libelle": "Master of Science HES", "niveau": "Master"},
        {"code": "BSc-Uni", "libelle": "Bachelor universitaire"},
        {"code": "MSc-Uni", "libelle": "Master universitaire"},
        {"code": "EPF", "libelle": "Diplôme EPF/ETH"},
        {"code": "PhD", "libelle": "Doctorat"}
      ]
    }
  ]
}
```

#### 8.2 Équivalences internationales (`equivalences_international.json`)

```json
{
  "equivalences": [
    {
      "famille_suisse": "CFC",
      "equivalents": [
        {"pays": "France", "titre": "CAP / BEP"},
        {"pays": "Allemagne", "titre": "Berufsausbildung"},
        {"pays": "Italie", "titre": "Diploma di qualifica professionale"}
      ]
    },
    {
      "famille_suisse": "Bachelor HES (3 ans)",
      "equivalents": [
        {"pays": "France", "titre": "Licence / Bac+3"},
        {"pays": "International", "titre": "Bachelor's degree"}
      ]
    },
    {
      "famille_suisse": "Master universitaire (5 ans)",
      "equivalents": [
        {"pays": "France", "titre": "Master / Bac+5"},
        {"pays": "International", "titre": "Master's degree"}
      ]
    }
  ]
}
```

#### 8.3 Nomenclature CH-ISCO-08 (`ch_isco_08.json`)
Extrait de la nomenclature suisse des professions. Source : OFS (Office fédéral de la statistique). 4-5 niveaux hiérarchiques de profession, codes à 4 chiffres (ex. "3411 — Comptables").

Utilisé pour :
- Check ORP (matching intitulé du poste vs liste SECO)
- Suggestion de famille de métier dans le catalogue
- Format ORP (champ "Profession")

#### 8.4 CCT étendues (`cct_etendues.json`)
Liste des CCT étendues en Suisse, avec secteurs d'application et liens vers les grilles de classification. Source : SECO. À ingester manuellement (liste maintenue par Arhiane dans le pack).

#### 8.5 Liste SECO ORP (`liste_orp_[annee].csv`)
Liste des genres de professions soumis à l'obligation d'annonce pour l'année en cours. Fournie par SECO chaque automne. Chargée par le client ou dans le pack maintenance.

### Évolution du référentiel
- **Pack maintenance annuel** : Arhiane met à jour tous ces référentiels
- **Mise à jour manuelle** : l'utilisateur peut déposer les fichiers dans le dossier `/references/` d'Arhiane
- **Validation au chargement** : schema check au démarrage du module

---

## 9. Gestion des erreurs LLM

### Erreurs possibles
- Timeout (LLM trop lent, dépasse 120 secondes)
- Génération vide (LLM retourne 0 tokens)
- Output mal formé (JSON invalide, structure non respectée)
- Crash du moteur LLM (LM Studio indisponible)

### Comportement attendu

**Timeout** :
- Retry automatique 1 fois
- Si échec répété : message utilisateur "La relecture prend plus de temps que prévu. [Interrompre et continuer sans relecture] [Réessayer]"

**Génération vide** :
- Retry automatique 1 fois avec prompt légèrement reformulé
- Si échec : message utilisateur "Je n'ai pas réussi à produire ce contenu. Essaie de préciser le contexte dans la section concernée."

**Output mal formé** :
- Parser tolérant qui tente de récupérer ce qui est parsable
- Log technique pour debug (invisible pour l'utilisateur)
- Si irrécupérable : même comportement que génération vide

**Crash moteur LLM** :
- Détection au démarrage (health check)
- Message : "Le moteur d'intelligence artificielle d'Arhiane n'est pas disponible. Vérifie que LM Studio est lancé. [Ouvrir l'aide]"
- Bouton "Vérifier à nouveau"

### Logs techniques
Tous les appels LLM sont loggés avec :
- Date/heure
- Modèle utilisé
- Prompt envoyé (tronqué à 500 caractères)
- Durée
- Status (succès / timeout / erreur)
- Nombre de tokens générés

Logs stockés localement, non accessibles à l'utilisateur standard (fichier `arhiane/logs/llm_calls.log`, avec rotation journalière).

---

## 10. Tests d'acceptation des garde-fous

### Tests unitaires (100 % de couverture exigée)
1. Check 3.1 : pourcentages valides / invalides / manquants
2. Check 3.2 : cohérence subordonnés / activités [P]
3. Check 3.3 : cohérence expérience / catégorie de cadre
4. Check 3.4 : diplômes reconnus / non reconnus / sans mention équivalence
5. Check 3.5 : patterns LEg (listes de tests exhaustives)
6. Check 3.6 : écriture inclusive (avec 3 styles)
7. Check 3.7 : matching ORP sur intitulés variés
8. Check 3.8 : cohérence CCT (sur CCT supportées)
9. Check 3.9 : cohérence référentiel entité

### Tests d'intégration sur jeu de cas
Un jeu de 10-15 cahiers des charges "test" (incluant des cas avec erreurs volontaires) :
- Chaque alerte attendue doit être détectée
- Pas de faux positif en excès
- Performance : tous les checks < 3 secondes

### Tests de régression sur le self-review
Un jeu de 5 documents "pièges" :
- Document avec stéréotype de genre caché → doit être détecté par Passe 3
- Document avec formulations vagues → doit être détecté par Passe 2
- Document parfait → aucune alerte par Passes 1-4

Critère d'acceptation : **80 % de détection** des erreurs attendues sur ces cas de référence.

---

**Fichier suivant à lire** : [07_CONFORMITE_SUISSE.md](07_CONFORMITE_SUISSE.md) — ORP, LEg, CCT, référentiel détaillé.
