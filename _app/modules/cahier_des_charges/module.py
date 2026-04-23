"""Module Cahier des charges — EditorModule stateful par document.

V1.0 minimal (cf. PHASE_0_ANALYSE_RISQUES.md) :
    - 11 sections canoniques
    - 1 format d'annonce (classique corporate)
    - Checks déterministes
    - UI 2 zones (navigation gauche + édition centrale + boutons
      d'actions contextuelles, pas encore de chat copilote)
    - Catalogue basique avec versioning

V1.1 (reporté) :
    - Self-review LLM (même modèle, prompts dédiés)
    - 3 autres formats d'annonce (moderne narratif, bref plateforme, ORP)
    - Copilote chat persistant en zone droite
    - Comparaison de versions, recherche full-text avancée

Ce fichier définit le **contrat du module** (métadonnées, sections,
actions, intégration avec `ModuleRegistry`). La logique métier vit
dans des fichiers frères :
    - `models.py`          : dataclasses des 11 sections
    - `catalogue_store.py` : persistance JSON par entité
    - `generator.py`       : génération LLM initiale et par section
    - `checks.py`          : validations déterministes
    - `docx_export.py`     : export .docx final
    - `annonces.py`        : génération des variantes d'annonce
"""

from __future__ import annotations

from typing import Any

from _app.core.editor_base import EditorAction, EditorModuleBase, EditorSection
from _app.core.module_base import ModuleContext
from _app.modules.cahier_des_charges.models import (
    SECTIONS_TOGGABLES,
    CahierDesCharges,
)


class Module(EditorModuleBase):
    id = "cahier_des_charges"
    nom = "Cahier des Charges"
    icone = "liste"
    description = (
        "Transforme une liste de tâches en cahier des charges structuré "
        "selon les modèles romands (Vaud, Genève, Fribourg), avec génération "
        "d'annonces d'emploi. Terminologie officielle, conformité ORP/LEg, "
        "référentiel factuel embarqué."
    )
    categorie = "administration_documents"
    # Tempé 0.5 : créatif pour la rédaction, sans glisser dans l'invention
    # (les garde-fous factuels sont dans checks.py + référentiels).
    temperature = 0.5
    statut = "disponible"

    # ------------------------------------------------------------------
    # Structure du document : 11 sections canoniques
    # ------------------------------------------------------------------

    def sections(self) -> list[EditorSection]:
        """Ordre et titres tels qu'affichés dans la navigation gauche
        de l'éditeur. Les ids sont alignés avec `models.SECTION_IDS`.
        """
        return [
            EditorSection(
                id="identification",
                titre="1. Identification",
                description=(
                    "Intitulé du poste, entité, lieu, type de contrat, "
                    "rattachement hiérarchique, suppléances."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="raison_detre",
                titre="2. Raison d'être du poste",
                description=(
                    "Paragraphe de 3 à 5 lignes qui répond à la question : "
                    "\"Si ce poste disparaissait demain, que perdrait-on ?\""
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="missions_principales",
                titre="3. Missions principales",
                description=(
                    "Entre 4 et 7 missions à l'infinitif, par ordre "
                    "d'importance décroissante."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="missions_detaillees",
                titre="4. Missions et activités détaillées",
                description=(
                    "Pour chaque mission : % de temps, activités typées "
                    "[S/P/O/Su], livrables, indicateurs de succès."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="responsabilites_particulieres",
                titre="5. Responsabilités particulières",
                description=(
                    "Mandats, représentation externe, fonctions transverses. "
                    "Section facultative (toggable Non applicable)."
                ),
                obligatoire=False,
            ),
            EditorSection(
                id="relations",
                titre="6. Relations et interactions",
                description=(
                    "Tableaux des relations internes et externes : "
                    "interlocuteur, fréquence, objet."
                ),
                obligatoire=False,
            ),
            EditorSection(
                id="pouvoirs_decision",
                titre="7. Pouvoirs de décision et autonomie",
                description=(
                    "Décisions autonomes / proposées / exécutées sur "
                    "instruction + budget géré le cas échéant."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="profil_attendu",
                titre="8. Profil attendu",
                description=(
                    "Formation de base et complémentaire, expérience, "
                    "langues, connaissances particulières."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="competences",
                titre="9. Compétences",
                description=(
                    "Socles (entité), transversales, métier, managériales "
                    "(conditionnelles aux subordonnés directs)."
                ),
                obligatoire=True,
            ),
            EditorSection(
                id="conditions_particulieres",
                titre="10. Conditions particulières",
                description=(
                    "Horaires, déplacements, piquets, charge physique, "
                    "confidentialité renforcée. Toggable Non applicable."
                ),
                obligatoire=False,
            ),
            EditorSection(
                id="signatures",
                titre="11. Signatures",
                description=(
                    "Blocs signature employeur + titulaire. Mention "
                    "\"recrutement en cours\" remplace le second bloc si "
                    "le document est établi avant engagement."
                ),
                obligatoire=True,
                verrouillee_apres_validation=True,
            ),
        ]

    # ------------------------------------------------------------------
    # Actions contextuelles disponibles sur chaque section
    # ------------------------------------------------------------------

    def actions(self) -> list[EditorAction]:
        """Actions contextuelles exposées dans l'UI d'édition.

        V1.0 minimal : 4 actions de reformulation. Le chat copilote
        (zone droite) est reporté en V1.1.
        """
        return [
            EditorAction(
                id="reformuler",
                label="Reformuler",
                description=(
                    "Réécrit la section dans un style équivalent, en "
                    "respectant les contraintes romandes (cahier des charges, "
                    "pas fiche de poste ; verbes actifs ; pas de superlatifs)."
                ),
            ),
            EditorAction(
                id="raccourcir",
                label="Raccourcir",
                description="Réduit la longueur tout en conservant l'information clé.",
            ),
            EditorAction(
                id="developper",
                label="Développer",
                description=(
                    "Enrichit la section avec des détails cohérents avec le "
                    "reste du cahier des charges."
                ),
            ),
            EditorAction(
                id="rendre_inclusif",
                label="Rendre inclusif",
                description=(
                    "Applique la politique d'écriture inclusive configurée "
                    "au niveau de l'entité (doublets, neutre, ou point médian)."
                ),
            ),
        ]

    # ------------------------------------------------------------------
    # Gabarit vide d'un nouveau document
    # ------------------------------------------------------------------

    def empty_document(self) -> dict[str, Any]:
        """Retourne un CahierDesCharges vide, sérialisé en dict.

        Respecte le contrat `EditorModuleBase` : clé `_meta` pour les
        métadonnées techniques, une clé par section pour le contenu.
        """
        return CahierDesCharges().to_dict()

    # ------------------------------------------------------------------
    # Complétude (surcharge pour gérer les sections toggables N/A)
    # ------------------------------------------------------------------

    def section_is_filled(self, document: dict[str, Any], section_id: str) -> bool:
        """Une section toggable marquée None compte comme "traitée"
        (l'utilisateur a statué "Non applicable").
        """
        # Gestion particulière de la section 6 (deux sous-listes).
        if section_id == "relations":
            internes = document.get("relations_internes")
            externes = document.get("relations_externes")
            # Toggable N/A : si les DEUX sont None
            if internes is None and externes is None:
                return True
            return bool(internes) or bool(externes)

        # Gestion particulière de la section 11 (deux blocs + flag recrutement)
        if section_id == "signatures":
            emp = document.get("signature_employeur") or {}
            tit = document.get("signature_titulaire") or {}
            recrut = document.get("recrutement_en_cours", False)
            emp_ok = bool((emp.get("nom") or "").strip())
            # Si recrutement en cours : titulaire non requis, seul employeur compte
            tit_ok = recrut or bool((tit.get("nom") or "").strip())
            return emp_ok and tit_ok

        # Cas général : clé de section = valeur unique
        value = document.get(section_id)
        # Toggable marquée N/A (explicitement None)
        if value is None and section_id in SECTIONS_TOGGABLES:
            return True
        return super().section_is_filled(document, section_id)

    # ------------------------------------------------------------------
    # Inputs de cadrage initial (écran "Nouveau cahier des charges")
    # ------------------------------------------------------------------

    def inputs_schema(self) -> list[dict[str, Any]]:
        """5 questions de cadrage avant la génération initiale.

        Une fois répondues, le module appelle `generate_initial()` pour
        produire un premier jet des 11 sections à partir du texte brut
        des tâches + ces 5 points de contexte.
        """
        return [
            {
                "id": "intitule_poste",
                "label": "Intitulé du poste",
                "type": "text",
                "required": True,
                "aide": (
                    "Ex: 'Responsable comptable et administratif', "
                    "'Assistant(e) de direction', 'Chargé(e) de recrutement'."
                ),
            },
            {
                "id": "categorie_cadre",
                "label": "Catégorie",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "cadre_strategique", "label": "Cadre stratégique"},
                    {"value": "cadre_operationnel", "label": "Cadre opérationnel"},
                    {"value": "cadre_intermediaire", "label": "Cadre intermédiaire"},
                    {"value": "collaborateur_specialise", "label": "Collaborateur spécialisé"},
                    {"value": "collaborateur", "label": "Collaborateur"},
                    {"value": "apprenti", "label": "Apprenti"},
                ],
            },
            {
                "id": "type_contrat",
                "label": "Type de contrat",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "cdi", "label": "CDI"},
                    {"value": "cdd", "label": "CDD"},
                    {"value": "stage", "label": "Stage"},
                    {"value": "apprentissage", "label": "Apprentissage"},
                ],
            },
            {
                "id": "nombre_subordonnes",
                "label": "Nombre de subordonnés directs",
                "type": "number",
                "required": True,
                "aide": (
                    "Conditionne l'apparition de la sous-section 9.4 "
                    "\"Compétences managériales\"."
                ),
            },
            {
                "id": "taches_vrac",
                "label": "Tâches et responsabilités (en vrac)",
                "type": "textarea",
                "required": True,
                "aide": (
                    "Collez librement la liste des tâches du poste. "
                    "Pas besoin de structurer — Arhiane s'en charge."
                ),
            },
        ]

    # ------------------------------------------------------------------
    # Hooks LLM — implémentations vides pour la V1.0 initiale
    # ------------------------------------------------------------------

    def generate_initial(
        self,
        inputs: dict[str, Any],
        ctx: ModuleContext,
    ) -> dict[str, Any]:
        """TODO Phase 2 : génération LLM initiale.

        En attendant que la couche LLM soit branchée, on retourne un
        document vide avec l'identification pré-remplie depuis les
        inputs de cadrage. Ça permet déjà de tester le flux d'édition
        manuelle bout en bout.
        """
        doc = CahierDesCharges()
        doc.identification.intitule_poste = (inputs.get("intitule_poste") or "").strip()
        doc.identification.categorie_cadre = inputs.get("categorie_cadre") or ""
        doc.identification.type_contrat = inputs.get("type_contrat") or "cdi"
        try:
            doc.identification.nombre_subordonnes_directs = int(
                inputs.get("nombre_subordonnes") or 0
            )
        except (TypeError, ValueError):
            doc.identification.nombre_subordonnes_directs = 0

        # Pré-remplissage depuis l'entité active (logo/nom traités côté export).
        if ctx.entity is not None:
            doc.identification.entite = ctx.entity.nom
            doc.meta.entite_id = ctx.entity.id
            doc.meta.langue = ctx.entity.langue_principale
            # Compétences socles de l'entité pré-remplies en 9.1.
            doc.competences.socles = list(ctx.entity.competences_socles)

        return doc.to_dict()

    def generate_section(
        self,
        section_id: str,
        document: dict[str, Any],
        ctx: ModuleContext,
    ) -> Any:
        """TODO Phase 2 : génération ciblée d'une section via LLM."""
        raise NotImplementedError(
            f"generate_section({section_id!r}) sera branché en Phase 2 "
            f"avec les prompts spécifiques. En Phase 1, l'édition est "
            f"manuelle ou issue du remplissage initial."
        )

    def run_action(
        self,
        action_id: str,
        section_id: str,
        document: dict[str, Any],
        ctx: ModuleContext,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """TODO Phase 2 : exécution d'une action contextuelle via LLM."""
        raise NotImplementedError(
            f"run_action({action_id!r} sur {section_id!r}) sera branché "
            f"en Phase 2 avec les prompts dédiés."
        )
