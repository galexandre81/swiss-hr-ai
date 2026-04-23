# 12 — Divergences vis-à-vis du dossier de spécifications "Cahier des charges"

**Version :** 1.0 — 23 avril 2026
**Statut :** À valider avant démarrage Phase 0
**Référence :** dossier de spécifications V1 du module "Cahier des charges" (13 fichiers, README + 00 à 11)

---

## Objet

Ce document acte les écarts assumés entre le dossier de spécifications V1 du module "Cahier des charges" et l'implémentation prévue dans Arhiane. Tout autre écart non listé ici doit être validé explicitement (cf. règle d'autonomie, [00_BRIEF_CLAUDE_CODE.md §3](../downloads/generateur%20descriptifs%20de%20poste/00_BRIEF_CLAUDE_CODE.md)).

---

## Divergence 1 — Modèle LLM : Qwen 3.5 9B confirmé (pas de divergence avec la spec, correction de l'archi globale)

### Contexte
- Le dossier de spécifications cible **Qwen 3.5 9B Q4_K_M** comme modèle principal.
- L'[00_ARCHITECTURE_GLOBALE.md §1](00_ARCHITECTURE_GLOBALE.md) d'Arhiane (datée 21 avril 2026) indique que ce modèle "n'existe pas à ce jour" et recommande Qwen 3 8B Instruct GGUF Q4_K_M en remplacement.

### Vérification
- Qwen 3.5 9B est sorti en **février 2026**, sous licence Apache 2.0, avec GGUF disponibles pour LM Studio (177 quantifications référencées sur Hugging Face).
- L'information dans l'archi globale est obsolète au 23 avril 2026.

### Décision
- **On suit la spec : Qwen 3.5 9B Q4_K_M devient le modèle principal du module CdC.**
- L'archi globale d'Arhiane sera mise à jour en conséquence (action séparée, à arbitrer si on bascule aussi les autres modules sur Qwen 3.5 9B ou si on garde une cohabitation 8B/9B selon les modules).

### Impact
- Aucun sur le scope du module CdC.
- Téléchargement initial utilisateur : ~5,5 Go au lieu de ~5 Go pour Qwen 3 8B Q4_K_M (négligeable).

---

## Divergence 2 — Self-review LLM : un seul modèle, pas deux

### Contexte
- La spec ([00_BRIEF_CLAUDE_CODE.md §6](../downloads/generateur%20descriptifs%20de%20poste/00_BRIEF_CLAUDE_CODE.md), [09_PROMPTS_LLM.md §3](../downloads/generateur%20descriptifs%20de%20poste/09_PROMPTS_LLM.md)) prévoit un **second LLM léger ~3B** (Qwen 3B ou Phi 3.5) chargé/déchargé à la demande pour exécuter les 4 passes de self-review.
- Justification originelle : économie de VRAM, vitesse (<90 s pour les 4 passes).

### Problème
- L'utilisateur cible (responsable RH PME, non technique) doit gérer **deux modèles distincts** dans LM Studio : téléchargement doublé, choix du modèle à charger, gestion des cas où la VRAM ne tient pas les deux en parallèle.
- Cela contredit la doctrine Arhiane ([00_ARCHITECTURE_GLOBALE.md §6](00_ARCHITECTURE_GLOBALE.md)) : *"Jamais de terminal, de fichier JSON à éditer, ou de message d'erreur technique"*.
- Aucun autre module Arhiane n'impose deux modèles.

### Décision
- **On utilise le même modèle Qwen 3.5 9B pour la génération initiale ET pour le self-review.**
- Les 4 prompts de self-review ([09_PROMPTS_LLM.md §3](../downloads/generateur%20descriptifs%20de%20poste/09_PROMPTS_LLM.md)) sont conservés tels quels — c'est la rigueur du prompt qui produit la valeur, pas la taille du modèle.
- Le self-review reste **optionnel** et explicitement présenté comme "relecture approfondie" à l'utilisateur.

### Impact
- **Performance** : self-review attendu à 2-3 minutes au lieu de <90 s. Acceptable car (a) optionnel, (b) l'utilisateur fait autre chose pendant ce temps, (c) cohérent avec un workflow où le RH revient relire ses alertes après pause café.
- **Qualité** : meilleure qu'avec un 3B (un 9B comprend mieux les nuances rédactionnelles d'un cahier des charges suisse romand).
- **Install utilisateur** : un seul modèle dans LM Studio, comme tous les autres modules Arhiane. **Friction réduite à zéro.**
- **Code** : pas de logique de chargement/déchargement dynamique de modèle dans `llm_client.py`. Économie de ~2-3 jours de dev.
- **Benchmark machine** : conservé, recalibré sur le 9B uniquement. Estimations affichées à l'utilisateur ajustées.

### Options écartées
- **Option B : auto-orchestration LM Studio CLI (`lms load/unload`)** — fragile, couplage fort à la version LM Studio, complexité d'install.
- **Option C : drop complet du self-review en V1** — perte d'une couche de qualité valorisée par la spec, pas justifié.

---

## Divergence 3 — Persistance : fichiers JSON, pas SQLite

### Contexte
- La spec ([05_CATALOGUE_POSTES.md §2](../downloads/generateur%20descriptifs%20de%20poste/05_CATALOGUE_POSTES.md)) propose 3 tables SQLite (`cahiers_des_charges`, `cahiers_des_charges_supprimes`, `exports_cdc`) avec index, contraintes d'unicité, FK, pour gérer le catalogue de postes.
- Arhiane actuel n'utilise aucune BDD : tout passe par [dossier_store.py](_app/core/dossier_store.py), fichiers JSON dans des dossiers lisibles par l'utilisateur. Doctrine explicite : *"tout est JSON pour rester grep-able et auditable. Un RH qui fouille l'Explorateur Windows à 3 ans doit reconnaître instantanément de quoi il s'agit."*

### Problème
- Introduire SQLite ferait du module CdC le **premier du genre** dans Arhiane : nouvelle dépendance, nouveau format de backup (attention au WAL), opacité pour le RH (impossible d'ouvrir le `.db` dans Notepad), risque de corruption fichier.
- Volumétrie réelle : 50 à 200 postes par entité. `os.scandir()` + `json.load()` reste largement sous les 100 ms pour cette taille — SQL n'apporte pas de gain perceptible.

### Décision
- **On reste en JSON pur, cohérent avec le reste d'Arhiane.**
- Arborescence proposée (à affiner en Phase 1) :
  ```
  Entities/
    [ENTITE]/
      Catalogue_CdC/
        _index.json                     ← métadonnées agrégées, reconstructible
        _corbeille/                     ← soft-delete, TTL 30j via date_suppression
        [poste_id]/
          v1.0.json
          v1.1.json
          v2.0.json                     ← la "version active" est une clé dans _index.json
          exports/
            v1.1_cahier_des_charges.docx
            v1.1_annonce_orp.docx
  ```
- `_index.json` contient les champs filtrables (intitulé, famille métier, statut, version active, dates). Régénérable à 100 % depuis les fichiers de poste.
- Le versioning utilise la convention de nommage (`v1.0.json`, `v1.1.json`) plutôt qu'une contrainte SQL.
- Soft-delete = déplacement dans `_corbeille/` avec timestamp dans le nom ; job de nettoyage au démarrage du module.
- Recherche full-text : parcours des JSON du catalogue de l'entité active, en mémoire. Si ça devient lent (>500 postes, peu probable en PME), bascule en option hybride (index SQLite régénérable) en V1.5.

### Impact
- **UX utilisateur** : transparence totale. Le RH peut ouvrir, sauvegarder, copier-coller un poste en dehors d'Arhiane.
- **Backup** : copier `Entities/` suffit. Pas de considération BDD.
- **Code** : pas de SQLAlchemy/Alembic, pas de schéma SQL à maintenir. Le `CahierDesChargesRepository` de la spec ([08_INTEGRATION_ARHIANE.md §4.3](../downloads/generateur%20descriptifs%20de%20poste/08_INTEGRATION_ARHIANE.md)) reste identique en interface mais tape sur les fichiers.
- **Isolation multi-entité** : garantie par l'arborescence (`Entities/[ENTITE]/Catalogue_CdC/`), sans filtre SQL.
- **Phase 1** : plans "Jour 1-2 Modèles et DB" de la [Roadmap §3](../downloads/generateur%20descriptifs%20de%20poste/11_ROADMAP.md) deviennent "Jour 1-2 Modèles et persistance fichier". Gain de ~1 jour.

### Option de repli
- Si les perfs du catalogue deviennent problématiques (peu probable à 200 postes), l'introduction d'un index SQLite **régénérable à tout moment** depuis les JSON est non-bloquante et cosmétique. À garder en V1.5 de côté.

---

## Divergences mineures (rappel pour mémoire)

Identifiées lors de l'analyse initiale, à corriger sans débat :

| Spec | Existant Arhiane | Action |
|---|---|---|
| Arborescence `arhiane/modules/cahier_des_charges/` | `_app/modules/cahier_des_charges/` | Aligner sur l'existant |
| Référence à une `EntiteService` (classe Python) | Module fonctionnel `_app/core/entity_manager.py` | Adapter les appels au pattern existant |
| Référence à une `JournalAuditService` | Module `_app/core/audit_trail.py` | Idem |
| Champs entité `politique_inclusif`, `langue_principale`, `competences_socles`, `cct_applicable` | Pas tous présents dans `Entities/*/config.json` actuel | Étendre le schéma `config.json` au début de la Phase 1, valider avec utilisateur |

---

## Sign-off

- [x] Utilisateur (Guillaume) : décision 1 validée (Qwen 3.5 9B confirmé)
- [x] Utilisateur (Guillaume) : décision 2 validée (un seul modèle pour génération + self-review)
- [x] Utilisateur (Guillaume) : décision 3 validée (persistance fichiers JSON, pas SQLite)
- [ ] Mise à jour de [00_ARCHITECTURE_GLOBALE.md §1](00_ARCHITECTURE_GLOBALE.md) planifiée (Qwen 3.5 9B comme modèle principal Arhiane)
- [ ] Extension du schéma `Entities/*/config.json` avec les 4 champs manquants (langue, inclusif, CCT, compétences socles) — action Phase 1

Démarrage Phase 0 du module Cahier des charges **autorisé** dès que les 2 cases restantes sont traitées (elles ne bloquent pas le Phase 0 analyse, uniquement l'entrée en Phase 1 code).
