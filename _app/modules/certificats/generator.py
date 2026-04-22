"""Assemblage déterministe du brouillon de certificat.

Principe (cf. §18 spec) :
    - Les phrases d'appréciation synthèse viennent de la bibliothèque
      validée, PAS du LLM ;
    - Les sections narratives (activités, projets, formations) peuvent
      être polies par le LLM, mais seulement à partir de faits injectés ;
    - En V1 de la V1 : pas d'appel LLM — on livre un brouillon
      100 % déterministe. L'intégration LLM (polissage) sera ajoutée
      quand Qwen 3 8B sera benché. Cela garantit que le module est
      utilisable même si LM Studio n'est pas démarré.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Critères du questionnaire (cf. §15.6 spec).
# (critere_id, label_fr, applicable_par_defaut)
CRITERES: list[tuple[str, str, bool]] = [
    ("qualite_travail", "Qualité du travail", True),
    ("quantite_travail", "Quantité / productivité", True),
    ("competences_techniques", "Compétences techniques", True),
    ("fiabilite_autonomie", "Fiabilité / autonomie", True),
    ("comportement_hierarchie", "Comportement envers la hiérarchie", True),
    ("comportement_collegues", "Comportement envers les collègues", True),
    ("comportement_subordonnes", "Comportement envers les subordonnés", False),
    ("comportement_clients", "Comportement envers les clients / partenaires", False),
]

# Critères minimaux qu'un certificat complet DOIT couvrir (checklist §4, §19).
CRITERES_OBLIGATOIRES: frozenset[str] = frozenset({
    "qualite_travail",
    "quantite_travail",
    "comportement_hierarchie",
    "comportement_collegues",
})

LEVEL_LABELS = {
    1: "Nettement en-deçà des attentes",
    2: "En-deçà des attentes",
    3: "Conforme aux attentes du poste",
    4: "Supérieur aux attentes",
    5: "Nettement supérieur / exceptionnel",
}


@dataclass
class Alerte:
    code: str
    severite: str   # "bloquant" | "alerte" | "info"
    message: str
    suggestion: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severite": self.severite,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class Draft:
    texte: str
    alertes: list[Alerte] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "texte": self.texte,
            "alertes": [a.as_dict() for a in self.alertes],
            "metadata": self.metadata,
        }


def apply_genre(text: str, genre: str) -> str:
    """Applique les accords grammaticaux à un texte qui contient des
    marqueurs conventionnels.

    Marqueurs pris en charge :
        "Elle/Il"   → "Elle" | "Il" | "Elle·Il"
        "elle/il"   → "elle" | "il" | "elle·il"
        "·e"        → ""     | "e"  | "·e"          (ex: reconnu·e)
        "(e)"       → ""     | "e"  | "·e"          (ex: reconnu(e))

    `genre` attendu : "f" (féminin), "m" (masculin), "inclusif", ou "" (= inclusif).
    """
    g = (genre or "inclusif").lower()
    if g == "f":
        repl = [("Elle/Il", "Elle"), ("elle/il", "elle"), ("·e", "e"), ("(e)", "e")]
    elif g == "m":
        repl = [("Elle/Il", "Il"), ("elle/il", "il"), ("·e", ""), ("(e)", "")]
    else:
        repl = [("Elle/Il", "Elle·Il"), ("elle/il", "elle·il"), ("(e)", "·e")]
    for a, b in repl:
        text = text.replace(a, b)
    return text


def _fmt_date(iso_like: str) -> str:
    """Accepte '2024-03-01' ou '01.03.2024' ou vide. Sort en format suisse."""
    s = (iso_like or "").strip()
    if not s:
        return "…"
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return s  # on renvoie tel quel si format inconnu


def build_draft(
    *,
    answers: dict[str, dict[str, Any]],
    entity: Any | None,
    formulations: Any,
    blacklist: Any,
) -> Draft:
    """Assemble le brouillon à partir des réponses du wizard.

    `answers` = state["answers"] du wizard — structure :
        {
          "identite": {...}, "parcours": {...}, "decisions": {...},
          "evaluation": {...}, "conclusion": {...}
        }
    """
    identite = answers.get("identite", {})
    parcours = answers.get("parcours", {})
    decisions = answers.get("decisions", {})
    evaluation = answers.get("evaluation", {})
    conclusion = answers.get("conclusion", {})

    langue = identite.get("langue", "fr")
    type_doc = identite.get("type_document", "certificat_final")
    present = type_doc == "certificat_intermediaire"
    verb_etre = "travaille" if present else "a travaillé"
    verb_occ = "occupe" if present else "a occupé"

    prenom = identite.get("prenom", "").strip() or "Prénom"
    nom = identite.get("nom", "").strip() or "NOM"
    civilite = (identite.get("civilite") or "").strip()  # "Madame" / "Monsieur"
    genre = (identite.get("genre") or "").strip().lower()
    # Fallback si le genre n'a pas été fourni : déduit de la civilité, sinon inclusif.
    if not genre:
        genre = {"Madame": "f", "Monsieur": "m"}.get(civilite, "inclusif")
    personne = f"{civilite + ' ' if civilite else ''}{prenom} {nom}".strip()

    date_debut = _fmt_date(parcours.get("date_debut", ""))
    date_fin = _fmt_date(parcours.get("date_fin", "")) if not present else None
    fonction = parcours.get("fonction", "").strip() or "—"
    taux = parcours.get("taux_activite", "").strip()
    departement = parcours.get("departement", "").strip()
    date_naissance = _fmt_date(identite.get("date_naissance", ""))
    lieu_origine = identite.get("lieu_origine", "").strip()

    # --- En-tête --------------------------------------------------------

    employeur_nom = ""
    if entity is not None:
        employeur_nom = getattr(entity, "nom", "") or ""

    if type_doc == "attestation":
        titre = "Attestation de travail"
    elif type_doc == "certificat_intermediaire":
        titre = "Certificat de travail intermédiaire"
    else:
        titre = "Certificat de travail"

    lignes: list[str] = []
    lignes.append(titre.upper())
    lignes.append("")

    # --- Paragraphe 1 : nature et durée --------------------------------

    naissance_str = f", né·e le {date_naissance}" if date_naissance and date_naissance != "…" else ""  # géré par apply_genre
    origine_str = f", originaire de {lieu_origine}" if lieu_origine else ""
    if present:
        p1 = (
            f"{personne}{naissance_str}{origine_str}, "
            f"{verb_etre} au sein de {employeur_nom or 'notre entreprise'} depuis le {date_debut} "
            f"en qualité de {fonction}"
        )
    else:
        p1 = (
            f"{personne}{naissance_str}{origine_str}, "
            f"{verb_etre} au sein de {employeur_nom or 'notre entreprise'} du {date_debut} au {date_fin} "
            f"en qualité de {fonction}"
        )
    if taux:
        p1 += f", à un taux d'activité de {taux}"
    if departement:
        p1 += f", au sein du département {departement}"
    p1 += "."
    lignes.append(p1)
    lignes.append("")

    # --- Paragraphe 2 : activités -------------------------------------

    activites = (parcours.get("activites") or "").strip()
    if activites:
        if present:
            intro = f"Dans le cadre de ses fonctions, {prenom} {verb_occ} les responsabilités suivantes :"
        else:
            intro = f"Dans le cadre de ses fonctions, {prenom} a eu les responsabilités suivantes :"
        lignes.append(intro)
        for ligne in _bulletize(activites):
            lignes.append(ligne)
        lignes.append("")

    realisations = (parcours.get("realisations") or "").strip()
    if realisations:
        lignes.append("Parmi ses réalisations marquantes, on peut notamment relever :")
        for ligne in _bulletize(realisations):
            lignes.append(ligne)
        lignes.append("")

    # Attestation (§2) : on s'arrête aux éléments factuels.
    if type_doc == "attestation":
        lignes.append(_formule_date_lieu(entity))
        texte = "\n".join(lignes).strip() + "\n"
        texte = apply_genre(texte, genre)
        return Draft(texte=texte, alertes=[], metadata={"type": type_doc, "langue": langue})

    # --- Paragraphe 3 : appréciation par critère -----------------------

    alertes: list[Alerte] = []
    criteres_inputs: dict[str, dict[str, Any]] = evaluation.get("criteres", {})
    subs_applicable = bool(evaluation.get("subs_applicable"))
    clients_applicable = bool(evaluation.get("clients_applicable"))

    # Contrôle de complétude (§4, §19).
    manquants: list[str] = []
    for cid, label, default_applicable in CRITERES:
        applicable = default_applicable
        if cid == "comportement_subordonnes":
            applicable = subs_applicable
        elif cid == "comportement_clients":
            applicable = clients_applicable
        if not applicable:
            continue
        niveau = criteres_inputs.get(cid, {}).get("niveau")
        if not niveau:
            manquants.append(label)
            continue
        phrase = formulations.pick(cid, int(niveau), langue)
        if not phrase:
            alertes.append(Alerte(
                code="formulation_manquante",
                severite="alerte",
                message=f"Aucune formulation validée pour {label} niveau {niveau} ({langue}).",
                suggestion=f"Compléter Bibliotheques/{langue}/formulations_validees.json.",
            ))
            continue
        lignes.append(phrase)

    if manquants:
        for m in manquants:
            alertes.append(Alerte(
                code="critere_non_evalue",
                severite="bloquant",
                message=f"Critère obligatoire non évalué : {m}.",
                suggestion="Compléter la notation dans l'étape Évaluation.",
            ))

    # Synthèse globale
    niveau_global = evaluation.get("appreciation_globale", {}).get("niveau")
    if niveau_global:
        phrase_glob = formulations.pick("appreciation_globale", int(niveau_global), langue)
        if phrase_glob:
            lignes.append("")
            lignes.append(
                f"De manière générale, {personne} {phrase_glob}."
            )
        else:
            alertes.append(Alerte(
                code="formulation_manquante",
                severite="alerte",
                message=f"Formulation d'appréciation globale manquante pour le niveau {niveau_global}.",
                suggestion="Compléter la bibliothèque ou ajuster le niveau.",
            ))
    else:
        alertes.append(Alerte(
            code="appreciation_globale_manquante",
            severite="bloquant",
            message="L'appréciation globale n'a pas été choisie.",
            suggestion="Sélectionner un niveau 1-5 dans l'étape Évaluation.",
        ))

    lignes.append("")

    # --- Motif / conclusion -------------------------------------------

    if not present:
        motif = (decisions.get("motif_fin") or "").strip()
        afficher_motif = bool(decisions.get("afficher_motif"))
        if motif and afficher_motif:
            lignes.append(_phrase_motif(motif, prenom))

        remerciements = bool(conclusion.get("remerciements"))
        regrets = bool(conclusion.get("regrets"))
        voeux = bool(conclusion.get("voeux"))

        if any([remerciements, regrets, voeux]):
            parts: list[str] = []
            if remerciements:
                parts.append(
                    f"Nous remercions {personne} pour son engagement et la qualité de sa collaboration"
                )
            if regrets:
                parts.append("regrettons son départ")
            if voeux:
                parts.append(
                    "lui souhaitons plein succès dans la suite de son parcours professionnel"
                )
            # On joint proprement
            phrase = parts[0]
            if len(parts) == 2:
                phrase += f", et {parts[1]}"
            elif len(parts) == 3:
                phrase += f", {parts[1]} et {parts[2]}"
            phrase += "."
            lignes.append(phrase)

        # Cohérence (§19) : appréciation excellente sans formule → alerte.
        if niveau_global and int(niveau_global) >= 4 and not any(
            [remerciements, regrets, voeux]
        ):
            alertes.append(Alerte(
                code="formule_conclusion_manquante",
                severite="alerte",
                message=(
                    "Appréciation élevée sans remerciements/regrets/vœux : incohérence "
                    "lue par les recruteurs comme un signal négatif codé."
                ),
                suggestion="Activer au moins une composante de la formule de conclusion.",
            ))
    else:
        # Intermédiaire : pas de motif de fin, motif de délivrance en tête.
        motif_delivrance = (decisions.get("motif_delivrance") or "").strip()
        if motif_delivrance:
            lignes.insert(
                2,
                f"Le présent certificat intermédiaire est établi {motif_delivrance}.",
            )
            lignes.insert(3, "")

    lignes.append("")
    lignes.append(_formule_date_lieu(entity))

    texte = "\n".join(lignes).strip() + "\n"
    # Application des accords grammaticaux (Elle/Il, ·e, (e)) avant blacklist :
    # la blacklist scanne le texte tel qu'il sera remis au collaborateur.
    texte = apply_genre(texte, genre)

    # --- Passage blacklist -----------------------------------------
    if blacklist is not None:
        try:
            hits = blacklist.scan(texte, langue)
            for h in hits:
                alertes.append(Alerte(
                    code=h.regle_id,
                    severite=h.severite,
                    message=f"{h.raison} — extrait : …{h.extrait.strip()}…",
                    suggestion=h.suggestion,
                ))
        except Exception as exc:  # noqa: BLE001
            alertes.append(Alerte(
                code="blacklist_erreur",
                severite="alerte",
                message=f"Scan blacklist indisponible : {exc}",
            ))

    # --- Cohérence inter-critères (§19) --------------------------
    niveaux = [int(v.get("niveau", 0)) for v in criteres_inputs.values() if v.get("niveau")]
    if niveaux:
        lo, hi = min(niveaux), max(niveaux)
        if (hi - lo) >= 3:
            alertes.append(Alerte(
                code="ecart_niveaux",
                severite="alerte",
                message=(
                    f"Écart important entre critères (min {lo}, max {hi}). "
                    f"Cohérence à valider."
                ),
                suggestion="Vérifier que les exemples concrets étayent cette disparité.",
            ))

    return Draft(
        texte=texte,
        alertes=alertes,
        metadata={
            "type": type_doc,
            "langue": langue,
            "nb_caracteres": len(texte),
        },
    )


def _bulletize(raw: str) -> list[str]:
    """Transforme un bloc texte multiligne en puces — chaque ligne non vide
    devient une puce. Permet à l'utilisateur de lister librement.
    """
    out: list[str] = []
    for line in raw.splitlines():
        line = line.strip().lstrip("-•*").strip()
        if not line:
            continue
        out.append(f"  • {line}")
    return out


def _phrase_motif(motif: str, prenom: str) -> str:
    mapping = {
        "demission": f"{prenom} nous quitte suite à sa démission.",
        "employeur": "Les rapports de travail ont pris fin à notre initiative.",
        "accord_commun": "Les rapports de travail ont pris fin d'un commun accord.",
        "fin_cdd": "Les rapports de travail ont pris fin à l'échéance du contrat de durée déterminée.",
        "retraite": f"{prenom} fait valoir ses droits à la retraite.",
        "motif_grave": "La résiliation est intervenue pour motif grave au sens de l'art. 337 CO.",
        "autre": "",
    }
    return mapping.get(motif, "")


def _formule_date_lieu(entity: Any | None) -> str:
    lieu = ""
    if entity is not None:
        adresse = getattr(entity, "adresse", "") or ""
        # Heuristique : on garde la dernière composante de l'adresse (ville/NPA ville).
        lieu = adresse.split(",")[-1].strip() if adresse else ""
    lieu = lieu or "…"
    today = datetime.now().strftime("%d.%m.%Y")
    return f"Fait à {lieu}, le {today}."
