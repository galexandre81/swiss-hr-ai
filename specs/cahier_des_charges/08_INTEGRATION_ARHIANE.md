# 08 — Intégration avec Arhiane

Spécification de l'intégration du module "Cahier des charges" avec le reste d'Arhiane. **Principe directeur : intégration minimale, volontairement limitée.**

---

## 1. Philosophie

Arhiane est positionné comme une **boîte à outils RH**, pas comme un SIRH intégré. Chaque module doit pouvoir être **utilisé indépendamment**, sans dépendance forte aux autres modules. Les interactions transverses sont donc **volontairement limitées** en V1.

Cette position a été actée explicitement lors de la phase de conception :
> *"On veut une boîte à outils, pas un SIRH."*

Toute demande d'intégration supplémentaire en V1 doit être validée explicitement avant d'être implémentée.

---

## 2. Ce qui EST intégré en V1 (3 points seulement)

### 2.1 Lecture du référentiel d'entité Arhiane

Le module lit en **lecture seule** les informations suivantes depuis le référentiel d'entité Arhiane, pour pré-remplir les cahiers des charges :

| Donnée | Usage |
|--------|-------|
| Nom de l'entité | Page de garde, champs d'identification |
| Logo | Page de garde |
| Canton principal | Pré-remplissage du lieu de travail |
| CCT applicable (si configurée) | Check 3.8 (cohérence CCT) |
| Politique d'écriture inclusive | Style par défaut (doublets / neutre / point médian) |
| Langue principale | Langue de génération par défaut |
| Compétences socles de l'entité | Pré-remplissage Section 9.1 |

**Nature technique** : appel en lecture à l'API interne d'Arhiane, pas de duplication des données. Si le référentiel d'entité est modifié dans Arhiane, les cahiers des charges nouvellement créés reflètent immédiatement les changements.

**Pas de synchronisation inverse** : le module ne modifie jamais le référentiel d'entité.

### 2.2 Catalogue de postes propre au module

Le catalogue de postes (voir 05_CATALOGUE_POSTES.md) est **interne au module**. Il n'est pas accessible depuis les autres modules d'Arhiane en V1.

**Justification** : chaque module d'Arhiane gère ses propres données pour rester simple et indépendant. Si un autre module (ex. module ATS futur) avait besoin de lire le catalogue, une API dédiée serait ajoutée à ce moment-là, pas par anticipation.

**Isolation multi-entité** : strictement respectée. Un utilisateur qui bascule d'entité dans Arhiane change de catalogue sans mélange.

### 2.3 Journal d'audit commun

Toutes les actions significatives du module sont tracées dans le journal d'audit commun d'Arhiane, avec :

- Date et heure
- Utilisateur (email / identifiant Arhiane)
- Entité active
- Module ("cahier_des_charges")
- Action (voir liste ci-dessous)
- Objet (ID du cahier des charges concerné)
- Détails (JSON libre selon l'action)

**Liste des actions tracées** :
- `cdc.create` : création d'un nouveau cahier des charges
- `cdc.open` : ouverture d'un cahier des charges existant
- `cdc.edit_save` : sauvegarde d'une édition (30s auto ou manuelle)
- `cdc.new_version` : création d'une nouvelle version
- `cdc.validate` : validation finale
- `cdc.duplicate` : duplication
- `cdc.archive` : archivage
- `cdc.restore_archive` : restauration depuis archive
- `cdc.delete_soft` : suppression (corbeille)
- `cdc.delete_hard` : suppression définitive
- `cdc.restore_trash` : restauration depuis corbeille
- `cdc.llm_generate_initial` : génération structurée par LLM
- `cdc.llm_selfreview` : exécution d'un self-review
- `cdc.checks_run` : exécution des checks déterministes
- `cdc.orp_submit_confirm` : confirmation de soumission à Job-Room (saisie utilisateur)
- `cdc.export_docx` : export .docx
- `cdc.export_pack` : export du pack groupé
- `cdc.export_batch` : export groupé depuis le catalogue

**Format technique** : utiliser l'API de journalisation existante d'Arhiane. Respecter le schéma imposé.

---

## 3. Ce qui N'EST PAS intégré en V1 (liste explicite)

Cette liste est importante pour éviter les glissements de scope. Chaque élément a été explicitement retiré lors de la conception.

### 3.1 ❌ Lien avec le module Certificat de travail
**Abandonné**. Pas de synchronisation poste ↔ certificat. Si un utilisateur veut créer un certificat depuis un cahier des charges existant, il devra copier-coller manuellement.

**Raison** : les deux modules ont des cycles de vie et des granularités très différents. Un cahier des charges est un document de poste, un certificat est un document de personne. Le lien naturel est humain, pas technique.

### 3.2 ❌ Bascule contextuelle vers le module Consultation juridique
**Abandonné**. Pas de bouton "Vérifier avec la doc juridique" depuis le module Cahier des charges.

**Raison** : le copilote intégré du module (zone droite) répond à la plupart des questions sur les formulations du cahier des charges. Pour les questions juridiques pointues, l'utilisateur se rend naturellement dans le module Consultation juridique d'Arhiane.

### 3.3 ❌ Vérificateur LEg/inclusif comme service transverse
**Abandonné en V1**. Le vérificateur LEg reste **interne au module Cahier des charges** et n'est pas exposé comme service transverse aux autres modules Arhiane.

**Raison** : mieux vaut un vérificateur bien intégré à un cas d'usage précis qu'un service abstrait exposé partout mais mal contextualisé. En V1.5, si plusieurs modules en ont besoin, factoriser.

### 3.4 ❌ Copilote Arhiane global transverse
**Abandonné en V1**. Pas de copilote qui aurait une vision transverse des modules de l'entité.

**Raison** : périmètre trop large, risque de confusion de scope, multiplication des contextes LLM à gérer. Chaque module a son propre copilote ciblé.

### 3.5 ❌ Bus d'événements inter-modules
**Abandonné en V1**. Pas d'architecture événementielle où la création d'un cahier des charges déclenche des actions dans d'autres modules.

**Raison** : complexité technique et opérationnelle disproportionnée pour V1. Chaque module agit en autonomie, les utilisateurs font les liens humainement.

### 3.6 ❌ Lien avec un hypothétique module ATS
**Hors scope V1**. Il n'existe pas de module ATS dans Arhiane en V1. Même si une annonce est générée, le cahier des charges ne reçoit aucune information sur l'avancement d'un recrutement.

### 3.7 ❌ Lien avec un module de paie
**Hors scope V1**. Arhiane n'a pas de module paie. Aucun champ salaire n'est synchronisé entre le cahier des charges et un système de paie.

### 3.8 ❌ Organigramme visuel automatique
**Hors scope V1**. Même si le module dispose des informations hiérarchiques (supérieur, subordonnés), aucun organigramme visuel n'est généré. Reporté V1.5 ou V2.

### 3.9 ❌ Matrice de compétences transverse
**Hors scope V1**. Pas de vue "toutes les compétences utilisées dans tous les cahiers des charges de l'entité, avec qui les a". Reporté V1.5.

### 3.10 ❌ Détection automatique de doublons de postes
**Hors scope V1**. Si l'utilisateur crée deux fois le même poste, le module n'alerte pas automatiquement. Il propose seulement une fonction de comparaison manuelle (voir 05_CATALOGUE_POSTES.md §4 Geste 4).

---

## 4. Architecture technique de l'intégration minimale

### 4.1 Accès au référentiel d'entité

**Interface attendue** (à aligner avec l'existant Arhiane, Claude Code à valider avec le spec principal) :

```python
from arhiane.core.entite import EntiteService

entite_service = EntiteService()
entite = entite_service.get_entite_active(user_context)

# Accès aux champs
nom = entite.nom
logo_path = entite.logo_path
canton = entite.canton_principal
cct_applicable = entite.cct_applicable  # None si non configurée
politique_inclusif = entite.politique_inclusif  # "doublets" / "neutre" / "point_median" / "desactive"
langue_principale = entite.langue_principale  # "fr" / "de"
competences_socles = entite.competences_socles  # Liste de strings
```

### 4.2 Journalisation audit

**Interface attendue** :

```python
from arhiane.core.audit import JournalAuditService

journal = JournalAuditService()
journal.trace(
    user=current_user,
    entite=entite_active,
    module="cahier_des_charges",
    action="cdc.validate",
    objet_id=cdc.id,
    objet_type="cahier_des_charges",
    details={
        "version": "v1.2",
        "intitule_poste": cdc.intitule_poste,
        "nombre_sections_completes": 11,
        "self_review_execute": True,
        "alertes_ignorees": 2
    }
)
```

### 4.3 Isolation multi-entité

**Règle technique** : toute requête à la base de données du catalogue **doit** inclure un filtre `entite_id = current_entite.id`. Pas d'exception possible, même pour les administrateurs.

Pour éviter les oublis : factoriser dans une classe `CahierDesChargesRepository` qui a un constructeur prenant `entite_id` et l'injecte dans toutes les requêtes :

```python
class CahierDesChargesRepository:
    def __init__(self, entite_id: str):
        self.entite_id = entite_id

    def list(self, filters=None):
        query = "SELECT * FROM cahiers_des_charges WHERE entite_id = ?"
        params = [self.entite_id]
        if filters:
            # ... filters additionnels
        return self.db.fetchall(query, params)

    def get(self, cdc_id: int):
        query = "SELECT * FROM cahiers_des_charges WHERE id = ? AND entite_id = ?"
        return self.db.fetchone(query, [cdc_id, self.entite_id])
    # etc.
```

Cette discipline protège contre les fuites inter-entités qui seraient catastrophiques.

---

## 5. Checklist de non-régression

Avant chaque release du module, vérifier :

- ✅ Aucun appel au module Certificat de travail
- ✅ Aucun appel au module Consultation juridique depuis le module CdC
- ✅ Aucun appel réseau sortant hors LM Studio local
- ✅ Toute opération sur le catalogue filtre par entité
- ✅ Aucun bouton "Aller à..." vers un autre module
- ✅ Aucun service du module exposé aux autres modules (pas d'API transverse)
- ✅ Toutes les actions tracées dans le journal d'audit avec le bon `module="cahier_des_charges"`
- ✅ Les paramètres du module restent scopés au niveau entité, pas au niveau global Arhiane

---

## 6. Perspectives V1.5 et V2 (pour mémoire, NE PAS IMPLÉMENTER en V1)

Liste pour garder la trace des demandes reportées :

### V1.5 (amélioration sans refonte d'architecture)
- Import d'un emploi-type depuis un référentiel sectoriel (SKOS, Codex romand)
- Génération bilingue FR/DE en un clic sur un cahier des charges existant
- Intégration CCT élargie (au-delà des 4-5 CCT supportées en V1)
- Questionnaire titulaire envoyé par email (si module email connecté)
- Signature électronique simple (SignLive ou équivalent)

### V2 (refonte ou extension majeure)
- Lien dynamique poste ↔ titulaire(s) (introduction d'un concept "personne" dans Arhiane)
- Organigramme visuel interactif généré automatiquement
- Matrice de compétences transverse
- Copilote Arhiane global
- Bus d'événements inter-modules
- Workflow d'approbation multi-étapes
- Intégration avec un module ATS (à créer)
- Intégration avec un module Paie (à créer)
- API publique pour connecteurs tiers

---

**Fichier suivant à lire** : [09_PROMPTS_LLM.md](09_PROMPTS_LLM.md) — les prompts système pour les différents appels LLM.
