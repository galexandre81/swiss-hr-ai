# Module "Cahier des charges" d'Arhiane — Dossier de spécifications V1

Dossier de spécifications fonctionnelles complet destiné à un développeur autonome (Claude Code ou équivalent) pour réaliser ce module.

---

## Ordre de lecture

1. **[00_BRIEF_CLAUDE_CODE.md](00_BRIEF_CLAUDE_CODE.md)** ← **commencer ici**
   Mission, positionnement produit, règles d'autonomie, les 3 questions à répondre avant de coder.

2. **[01_SPEC_FONCTIONNEL.md](01_SPEC_FONCTIONNEL.md)**
   Spec principal, vue d'ensemble, cas d'usage, architecture fonctionnelle en 5 couches.

3. **[02_STRUCTURE_DOCX.md](02_STRUCTURE_DOCX.md)**
   Structure détaillée du cahier des charges .docx : 11 sections canoniques, styles Word, exemple complet.

4. **[03_FORMATS_ANNONCES.md](03_FORMATS_ANNONCES.md)**
   Les 4 formats d'annonce : Classique corporate / Moderne narratif / Bref plateforme / ORP.

5. **[04_UX_FLUX.md](04_UX_FLUX.md)**
   Flux utilisateur en 8 phases, architecture 3 zones, écrans détaillés.

6. **[05_CATALOGUE_POSTES.md](05_CATALOGUE_POSTES.md)**
   Catalogue par entité : schéma DB, versioning, archivage, comparaison, export groupé.

7. **[06_GARDE_FOUS_QUALITE.md](06_GARDE_FOUS_QUALITE.md)**
   Architecture à 4 couches : prompt renforcé + self-review LLM + checks déterministes + relecture humaine. Benchmark machine.

8. **[07_CONFORMITE_SUISSE.md](07_CONFORMITE_SUISSE.md)**
   ORP (art. 53b OSE), LEg, CO 328, CCT, référentiel diplômes suisses + équivalences internationales.

9. **[08_INTEGRATION_ARHIANE.md](08_INTEGRATION_ARHIANE.md)**
   Intégration minimale : lecture référentiel entité + journal audit. Liste explicite de ce qu'on **ne fait pas**.

10. **[09_PROMPTS_LLM.md](09_PROMPTS_LLM.md)**
    Tous les prompts système : génération initiale, self-review 4 passes, actions contextuelles, 4 prompts d'annonce, analyse d'import.

11. **[10_JEUX_DE_TESTS.md](10_JEUX_DE_TESTS.md)**
    25 scénarios de tests : fonctionnels, techniques, conformité, ergonomie. Critères d'acceptation finaux.

12. **[11_ROADMAP.md](11_ROADMAP.md)**
    Plan de développement en 7 phases, 4-6 semaines ETP. Décisions figées, risques techniques, jalons de validation.

---

## Synthèse du module en 30 secondes

**Quoi** : un nouveau module d'Arhiane qui permet à un responsable RH de PME suisse romande de créer un cahier des charges au format .docx structuré (11 sections inspirées Vaud/Genève/Fribourg) + 4 variantes d'annonce d'emploi (classique / moderne / plateforme / ORP).

**Comment** : interface 3 zones (nav / édition / copilote IA), flux en 8 phases, LLM local air-gapped (Qwen 3.5 9B + modèle léger pour self-review), catalogue par entité avec versioning.

**Positionnement** : boîte à outils RH, **pas un SIRH**. Intégration minimale avec Arhiane (référentiel entité + audit seulement). Terminologie officielle suisse romande ("cahier des charges", pas "fiche de poste").

**Qualité** : architecture à 4 couches (prompt renforcé / self-review / checks déterministes / relecture humaine). Alertes informatives, jamais bloquantes. Benchmark machine pour adaptation aux perf réelles.

**Conformité** : ORP (art. 53b OSE), LEg, CO 328, CCT. Référentiel factuel embarqué (diplômes, CH-ISCO-08, CCT, liste SECO). Mise à jour annuelle par pack payant OU par le client.

**Estimation** : 4-6 semaines ETP pour un développeur Python senior familier avec le stack Arhiane.

---

**Fin de l'index.** Commence par [00_BRIEF_CLAUDE_CODE.md](00_BRIEF_CLAUDE_CODE.md).
