"""Module Certificats de travail — wizard stateful.

Flow (cf. §14 spec) ramené à 5 étapes cohérentes pour la V1 :

    1. identite   — type de document, langue, collaborateur
    2. parcours   — dates, fonction, activités, réalisations
    3. decisions  — motif de départ, zones grises documentées
    4. evaluation — note 1-5 + exemple concret par critère
    5. conclusion — formule (remerciements / regrets / vœux)

La « collecte manager » par questionnaire AcroForm (§15) arrive en
phase C2 ; en V1, on travaille en mode « saisie RH en lieu et place du
manager » (§15.8) — le plus fiable puisqu'il ne dépend d'aucun canal
externe. L'auteur RH est tracé dans l'audit pour chaque étape.

Le LLM n'est PAS appelé en V1 : le brouillon est assemblé de manière
déterministe à partir des inputs + formulations validées. Un polissage
narratif via LM Studio pourra être branché dans `run_polish()` quand les
benchs Qwen seront faits.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from _app.core.audit_trail import AuditTrail
from _app.core.module_base import ModuleContext
from _app.core.wizard_base import WizardModuleBase, WizardStep
from _app.modules.certificats.generator import (
    CRITERES,
    CRITERES_OBLIGATOIRES,
    LEVEL_LABELS,
    build_draft,
)


class Module(WizardModuleBase):
    id = "certificats"
    nom = "Générateur de Certificats"
    icone = "diplome"
    description = (
        "Rédige un certificat de travail conforme à l'art. 330a CO à partir "
        "d'un dossier collaborateur pas-à-pas. Garde-fous et audit inclus."
    )
    categorie = "administration_documents"
    temperature = 0.2  # faible — appréciations encadrées par bibliothèque
    statut = "disponible"

    # ------------------------------------------------------------------
    # Définition des étapes
    # ------------------------------------------------------------------

    def steps(self) -> list[WizardStep]:
        level_options = [
            {"value": str(k), "label": f"{k} ★ — {v}"} for k, v in LEVEL_LABELS.items()
        ]
        # Champs par critère (5 niveaux + exemple concret).
        critere_fields: list[dict[str, Any]] = []
        for cid, label, _default_applicable in CRITERES:
            critere_fields.append({
                "id": f"crit_{cid}_niveau",
                "label": f"{label} — niveau",
                "type": "select",
                "options": level_options,
                "required": cid in CRITERES_OBLIGATOIRES,
                "aide": (
                    "3 ★ = conforme aux attentes. Les recruteurs suisses lisent "
                    "ce niveau comme « moyen » — à assumer consciemment."
                ),
            })
            critere_fields.append({
                "id": f"crit_{cid}_exemple",
                "label": f"{label} — exemple concret (2-3 lignes)",
                "type": "textarea",
                "required": False,
                "aide": "Un fait concret qui illustre la note. Nourrit la traçabilité et la détection d'incohérences.",
            })

        return [
            WizardStep(
                id="identite",
                label="Identité & type de document",
                description=(
                    "Collaborateur-rice concerné-e, type de certificat et langue cible. "
                    "L'entité employeur active (en haut à gauche) sera utilisée."
                ),
                inputs=[
                    {"id": "type_document", "label": "Type de document",
                     "type": "select", "required": True,
                     "options": [
                         {"value": "certificat_final", "label": "Certificat de travail (final)"},
                         {"value": "certificat_intermediaire", "label": "Certificat de travail intermédiaire"},
                         {"value": "attestation", "label": "Attestation de travail (art. 330a al. 2 — sur demande expresse)"},
                     ]},
                    {"id": "langue", "label": "Langue du certificat",
                     "type": "select", "required": True,
                     "options": [
                         {"value": "fr", "label": "Français"},
                         {"value": "de", "label": "Allemand"},
                         {"value": "en", "label": "Anglais"},
                     ]},
                    {"id": "civilite", "label": "Civilité",
                     "type": "select", "required": False,
                     "options": [
                         {"value": "", "label": "—"},
                         {"value": "Madame", "label": "Madame"},
                         {"value": "Monsieur", "label": "Monsieur"},
                     ]},
                    {"id": "genre", "label": "Accords grammaticaux",
                     "type": "select", "required": True,
                     "options": [
                         {"value": "f", "label": "Féminin (Elle, prise, reconnue)"},
                         {"value": "m", "label": "Masculin (Il, pris, reconnu)"},
                         {"value": "inclusif", "label": "Inclusif (Elle·Il, pris·e) — usage administratif"},
                     ],
                     "aide": (
                         "Détermine les pronoms et accords de participes passés dans le certificat. "
                         "Par défaut, cale sur la civilité. Utiliser « inclusif » sur demande explicite du/de la collaborateur-rice."
                     )},
                    {"id": "prenom", "label": "Prénom", "type": "text", "required": True},
                    {"id": "nom", "label": "Nom", "type": "text", "required": True},
                    {"id": "date_naissance", "label": "Date de naissance (JJ.MM.AAAA)",
                     "type": "text", "required": False,
                     "aide": "Format suisse : 15.03.1985."},
                    {"id": "lieu_origine", "label": "Lieu d'origine",
                     "type": "text", "required": False,
                     "aide": (
                         "Commune d'origine au sens suisse (figure sur la pièce d'identité). "
                         "Ex. : « Lausanne VD », « Sion VS ». Pour un-e collaborateur-rice non suisse, "
                         "laisser vide ou indiquer la nationalité."
                     )},
                ],
                required_fields=["type_document", "langue", "prenom", "nom", "genre"],
            ),
            WizardStep(
                id="parcours",
                label="Parcours & fonction",
                description=(
                    "Dates de rapport de travail, fonction, taux, activités et "
                    "réalisations marquantes. Une ligne par activité/réalisation."
                ),
                inputs=[
                    {"id": "date_debut", "label": "Date de début (JJ.MM.AAAA)",
                     "type": "text", "required": True,
                     "aide": "Format suisse : 15.01.2020."},
                    {"id": "date_fin", "label": "Date de fin (JJ.MM.AAAA — laisser vide pour un intermédiaire)",
                     "type": "text", "required": False},
                    {"id": "fonction", "label": "Fonction / intitulé de poste",
                     "type": "text", "required": True},
                    {"id": "taux_activite", "label": "Taux d'activité (ex. 100%)",
                     "type": "text", "required": False},
                    {"id": "departement", "label": "Département / équipe",
                     "type": "text", "required": False},
                    {"id": "activites", "label": "Activités principales (une par ligne)",
                     "type": "textarea", "required": False,
                     "aide": "Chaque ligne devient une puce dans le certificat."},
                    {"id": "realisations", "label": "Réalisations marquantes (une par ligne)",
                     "type": "textarea", "required": False},
                ],
                required_fields=["date_debut", "fonction"],
            ),
            WizardStep(
                id="decisions",
                label="Décisions préalables",
                description=(
                    "Motif de départ (si certificat final), mention ou non du motif, "
                    "et décisions explicites sur les zones grises (absences longues, "
                    "maladie, maternité). Ces décisions sont tracées dans l'audit."
                ),
                inputs=[
                    {"id": "motif_fin", "label": "Motif de fin (final uniquement)",
                     "type": "select", "required": False,
                     "options": [
                         {"value": "", "label": "— Non applicable / intermédiaire —"},
                         {"value": "demission", "label": "Démission du travailleur"},
                         {"value": "employeur", "label": "Résiliation par l'employeur"},
                         {"value": "accord_commun", "label": "Accord commun"},
                         {"value": "fin_cdd", "label": "Fin de contrat de durée déterminée"},
                         {"value": "retraite", "label": "Départ en retraite"},
                         {"value": "motif_grave", "label": "Motif grave (art. 337 CO — prudence)"},
                         {"value": "autre", "label": "Autre / ne pas mentionner"},
                     ]},
                    {"id": "afficher_motif", "label": "Faire apparaître le motif dans le certificat",
                     "type": "checkbox", "required": False,
                     "aide": "Par défaut, le motif n'apparaît pas. Le travailleur peut en règle générale refuser sa mention."},
                    {"id": "motif_delivrance", "label": "Motif de délivrance (intermédiaire uniquement)",
                     "type": "text", "required": False,
                     "aide": "Ex. : à la demande de l'employé, suite à un changement de supérieur, dans le cadre d'une restructuration."},
                    {"id": "absences_longues", "label": "Absences longues significatives à mentionner (texte neutre)",
                     "type": "textarea", "required": False,
                     "aide": "Cf. ATF 136 III 510 : mention obligatoire si l'omission donnerait une fausse impression. Formulation neutre recommandée — pas de diagnostic médical."},
                    {"id": "notes_rh", "label": "Notes internes RH (non incluses dans le certificat)",
                     "type": "textarea", "required": False},
                ],
                required_fields=[],
            ),
            WizardStep(
                id="evaluation",
                label="Évaluation",
                description=(
                    "Note 1-5 et exemple concret par critère. L'exemple concret est "
                    "essentiel : il nourrit la traçabilité et déclenche des alertes "
                    "si la note et l'exemple ne sont pas cohérents."
                ),
                inputs=[
                    {"id": "subs_applicable",
                     "label": "Le collaborateur manage-t-il une équipe ?",
                     "type": "checkbox", "required": False},
                    {"id": "clients_applicable",
                     "label": "Le poste implique-t-il des clients / partenaires externes ?",
                     "type": "checkbox", "required": False},
                    *critere_fields,
                    {"id": "appreciation_globale_niveau",
                     "label": "Appréciation globale — niveau de synthèse",
                     "type": "select", "required": True, "options": level_options,
                     "aide": "Ce niveau détermine la formule de synthèse choisie dans la bibliothèque validée."},
                ],
                required_fields=[
                    "appreciation_globale_niveau",
                    *(f"crit_{cid}_niveau" for cid, _, _ in CRITERES
                      if cid in CRITERES_OBLIGATOIRES),
                ],
            ),
            WizardStep(
                id="conclusion",
                label="Formule de conclusion",
                description=(
                    "Pour un certificat final : remerciements / regrets / vœux. "
                    "La combinaison est elle-même un code — incohérence signalée "
                    "en cas d'appréciation élevée sans formule."
                ),
                inputs=[
                    {"id": "remerciements", "label": "Inclure des remerciements",
                     "type": "checkbox", "required": False},
                    {"id": "regrets", "label": "Inclure des regrets",
                     "type": "checkbox", "required": False},
                    {"id": "voeux", "label": "Inclure des vœux pour la suite",
                     "type": "checkbox", "required": False},
                ],
                required_fields=[],
            ),
        ]

    # ------------------------------------------------------------------
    # Validation métier additionnelle
    # ------------------------------------------------------------------

    def validate_step(
        self,
        step_id: str,
        answers: dict[str, Any],
    ) -> list[str]:
        errors = super().validate_step(step_id, answers)

        if step_id == "identite":
            dn = (answers.get("date_naissance") or "").strip()
            if dn and _parse_ch_date(dn) is None:
                errors.append("Date de naissance : format attendu JJ.MM.AAAA (ex. 15.03.1985).")

        if step_id == "parcours":
            dd_raw = (answers.get("date_debut") or "").strip()
            df_raw = (answers.get("date_fin") or "").strip()
            dd = _parse_ch_date(dd_raw)
            df = _parse_ch_date(df_raw)
            if dd_raw and dd is None:
                errors.append("Date de début : format attendu JJ.MM.AAAA (ex. 15.01.2020).")
            if df_raw and df is None:
                errors.append("Date de fin : format attendu JJ.MM.AAAA.")
            if dd and df and df < dd:
                errors.append("Date de fin antérieure à la date de début.")

        if step_id == "evaluation":
            # Alertes souples côté front, mais on impose l'appréciation globale.
            ag = answers.get("appreciation_globale_niveau")
            if not ag:
                errors.append("Appréciation globale : niveau à sélectionner (1-5).")

        return errors

    # ------------------------------------------------------------------
    # Consolidation des réponses plates → structure générateur
    # ------------------------------------------------------------------

    def _reshape_for_generator(
        self,
        answers_by_step: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Convertit le state (plat par step) vers la forme attendue par
        build_draft (evaluation.criteres[cid] = {niveau, exemple})."""
        identite = dict(answers_by_step.get("identite", {}))
        parcours = dict(answers_by_step.get("parcours", {}))
        decisions = dict(answers_by_step.get("decisions", {}))
        evaluation_raw = dict(answers_by_step.get("evaluation", {}))
        conclusion = dict(answers_by_step.get("conclusion", {}))

        criteres: dict[str, dict[str, Any]] = {}
        for cid, _label, _app in CRITERES:
            niveau = evaluation_raw.get(f"crit_{cid}_niveau", "")
            exemple = evaluation_raw.get(f"crit_{cid}_exemple", "")
            if not niveau and not exemple:
                continue
            criteres[cid] = {"niveau": niveau, "exemple": exemple}

        evaluation = {
            "subs_applicable": bool(evaluation_raw.get("subs_applicable")),
            "clients_applicable": bool(evaluation_raw.get("clients_applicable")),
            "criteres": criteres,
            "appreciation_globale": {
                "niveau": evaluation_raw.get("appreciation_globale_niveau", ""),
            },
        }
        return {
            "identite": identite,
            "parcours": parcours,
            "decisions": decisions,
            "evaluation": evaluation,
            "conclusion": conclusion,
        }

    # ------------------------------------------------------------------
    # Prévisualisation (sans sceller)
    # ------------------------------------------------------------------

    def preview(
        self,
        state: dict[str, Any],
        ctx: ModuleContext,
    ) -> dict[str, Any]:
        """Assemble un brouillon depuis l'état courant, SANS écrire de
        fichier ni de scellement d'audit. Pour affichage live dans l'UI.
        """
        reshaped = self._reshape_for_generator(state.get("answers", {}))
        if ctx.formulations is None:
            return {
                "texte": "",
                "alertes": [{
                    "code": "bibliotheque_indisponible",
                    "severite": "bloquant",
                    "message": "La bibliothèque de formulations n'est pas chargée.",
                    "suggestion": "Vérifier que Bibliotheques/<langue>/formulations_validees.json existe.",
                }],
            }
        draft = build_draft(
            answers=reshaped,
            entity=ctx.entity,
            formulations=ctx.formulations,
            blacklist=ctx.blacklist,
        )
        return draft.as_dict()

    # ------------------------------------------------------------------
    # Finalisation : écrit le brouillon + scelle l'audit
    # ------------------------------------------------------------------

    def finalize(
        self,
        state: dict[str, Any],
        ctx: ModuleContext,
    ) -> dict[str, Any]:
        """Produit la version finale et la sauvegarde dans le dossier.

        Prérequis : `ctx.extras["dossier"]` contient le `Dossier` courant.
        Refus de sceller si des alertes bloquantes subsistent ET que le
        flag `force` n'est pas activé.
        """
        dossier = ctx.extras.get("dossier")
        if dossier is None:
            raise RuntimeError("finalize() nécessite un dossier courant (ctx.extras['dossier']).")

        reshaped = self._reshape_for_generator(state.get("answers", {}))
        draft = build_draft(
            answers=reshaped,
            entity=ctx.entity,
            formulations=ctx.formulations,
            blacklist=ctx.blacklist,
        )

        bloquants = [a for a in draft.alertes if a.severite == "bloquant"]
        force = bool(ctx.extras.get("force"))
        if bloquants and not force:
            return {
                **draft.as_dict(),
                "scelle": False,
                "raison": "Alertes bloquantes à résoudre avant finalisation.",
            }

        # Écriture du brouillon (.txt pour V1 — DOCX viendra avec doc_engine).
        brouillons_dir: Path = dossier.subfolder("05_brouillons")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = brouillons_dir / f"certificat_{stamp}.txt"
        txt_path.write_text(draft.texte, encoding="utf-8")

        # Trail : ouverture / décisions / draft / seal.
        trail = AuditTrail(dossier.racine)
        trail.append("wizard_state_snapshot", state=state)
        decisions = state.get("answers", {}).get("decisions", {})
        for k, v in decisions.items():
            if v in (None, "", False):
                continue
            trail.record_decision(zone=k, choix=str(v))
        for a in draft.alertes:
            trail.record_alert(a.code, a.message, resolution=("forcée" if force and a.severite == "bloquant" else ""))
        trail.record_draft(version=1, texte=draft.texte)
        seal = trail.seal(draft.texte, outputs=[str(txt_path.name)])

        # Mise à jour du dossier
        state["finalized"] = True
        dossier.wizard_state = state
        dossier.modules.setdefault(self.id, {})["dernier_scellement"] = {
            "fichier": str(txt_path.name),
            "sha256": seal["sha256"],
            "at": trail.events()[-1]["at"],
        }
        dossier.save()

        ctx.logger.info(
            f"Certificat scellé pour dossier {dossier.id} "
            f"(sha256={seal['sha256'][:12]}..)"
        )
        ctx.logger.audit(
            "certificat_scelle",
            dossier=dossier.id,
            entity=(ctx.entity.id if ctx.entity else None),
            fichier=txt_path.name,
            sha256_16=seal["sha256"][:16],
            alertes=[a.as_dict() for a in draft.alertes],
            forced=force,
        )

        return {
            **draft.as_dict(),
            "scelle": True,
            "fichier": str(txt_path),
            "sha256": seal["sha256"],
            "audit": str(trail.path.name),
        }


def _parse_ch_date(s: str):
    """Parse une date suisse `JJ.MM.AAAA` (ou l'ISO `AAAA-MM-JJ` pour tolérance).

    Retourne un `datetime` ou None si le format est invalide.
    """
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
