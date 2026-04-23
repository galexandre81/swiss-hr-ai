"""Modèles de données du cahier des charges.

Structure en 11 sections canoniques inspirées des modèles romands
(Vaud, Genève, Fribourg). Référence : specs/cahier_des_charges/02_STRUCTURE_DOCX.md

Principes :
- Un cahier des charges = un dict JSON sérialisable, structure plate
  par section. Chaque section a une clé stable, réutilisée côté UI.
- Les dataclasses ci-dessous sont des **gabarits**, pas des contrats
  stricts : un document en cours d'édition peut avoir des sections à
  `None`. Les checks de cohérence/complétude vivent dans `checks.py`.
- Tout est sérialisable via `asdict()` ; tout est désérialisable via
  `from_dict()` tolérant (les clés inconnues sont ignorées, les clés
  manquantes prennent leur valeur par défaut).

La V1.0 vise les 11 sections dans leur forme canonique. Les variantes
d'annonce d'emploi (§03_FORMATS_ANNONCES.md) sont hors de ce fichier —
elles vivent dans `annonces.py`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- Constantes énumérées (pas d'enum pour rester JSON-natif) ----------

# Typologie d'activités (Section 4).
TYPOLOGIE_ACTIVITE = frozenset({"strategique", "pilotage", "operationnel", "support"})

# Catégories de cadre (Section 1).
CATEGORIE_CADRE = frozenset({
    "cadre_strategique",
    "cadre_operationnel",
    "cadre_intermediaire",
    "collaborateur_specialise",
    "collaborateur",
    "apprenti",
})

# Types de contrat (Section 1).
TYPE_CONTRAT = frozenset({"cdi", "cdd", "stage", "apprentissage"})

# Niveaux CEFR pour les langues (Section 8.4).
NIVEAU_CEFR = frozenset({"A1", "A2", "B1", "B2", "C1", "C2", "langue_maternelle"})

# Statut de section pour l'affichage UI.
STATUT_SECTION = frozenset({
    "vide",           # jamais touchée
    "partielle",      # en cours, incomplète
    "complete",       # remplie, non encore revue
    "validee",        # revue par le RH
    "non_applicable", # explicitement marquée N/A (sections toggables : 5, 6, 10)
})

# Statut global d'un cahier des charges.
STATUT_CDC = frozenset({"brouillon", "valide", "archive"})


# --- Section 1 — Identification ----------------------------------------


@dataclass
class Identification:
    """Tableau d'identification du poste (Section 1)."""

    version_document: str = "v1.0"
    date_etablissement: str = ""  # DD.MM.YYYY
    auteur: str = ""
    version_remplacee: str = ""
    entite: str = ""
    departement: str = ""
    entite_organisationnelle: str = ""
    intitule_poste: str = ""
    libelle_emploi_type: str = ""
    categorie_cadre: str = ""  # ∈ CATEGORIE_CADRE ou vide
    lieu_travail: str = ""
    taux_activite: int = 100  # %
    type_contrat: str = "cdi"  # ∈ TYPE_CONTRAT
    duree_cdd: str = ""  # texte libre si type_contrat == "cdd"
    date_entree_prevue: str = ""  # DD.MM.YYYY
    superieur_hierarchique: str = ""
    nombre_subordonnes_directs: int = 0
    suppleance_remplace: str = ""
    suppleance_remplace_par: str = ""


# --- Section 3 — Missions principales ----------------------------------


@dataclass
class MissionPrincipale:
    """Une ligne de la Section 3 (liste numérotée de 4 à 7 missions)."""

    ordre: int = 0
    libelle: str = ""


# --- Section 4 — Missions et activités détaillées ----------------------


@dataclass
class MissionDetaillee:
    """Détail complet d'une mission (Section 4)."""

    ordre: int = 0
    libelle: str = ""
    pourcentage_temps: int = 0  # 0-100, somme des missions = 100
    activites_strategiques: list[str] = field(default_factory=list)
    activites_pilotage: list[str] = field(default_factory=list)
    activites_operationnelles: list[str] = field(default_factory=list)
    activites_support: list[str] = field(default_factory=list)
    livrables_attendus: list[str] = field(default_factory=list)
    indicateurs_succes: list[str] = field(default_factory=list)

    def total_activites(self) -> int:
        return (
            len(self.activites_strategiques)
            + len(self.activites_pilotage)
            + len(self.activites_operationnelles)
            + len(self.activites_support)
        )


# --- Section 6 — Relations --------------------------------------------


@dataclass
class Relation:
    """Une ligne du tableau Section 6.1 (internes) ou 6.2 (externes)."""

    interlocuteur: str = ""
    frequence: str = ""
    objet: str = ""


# --- Section 7 — Pouvoirs de décision ----------------------------------


@dataclass
class PouvoirsDecision:
    """Structure de la Section 7 (3 sous-sections + budget)."""

    decisions_autonomes: list[str] = field(default_factory=list)
    decisions_proposees: list[str] = field(default_factory=list)
    decisions_instruction: list[str] = field(default_factory=list)
    budget_gere_description: str = ""  # "15'000 CHF/an, plafond 5'000 CHF par acte"


# --- Section 8 — Profil attendu ----------------------------------------


@dataclass
class LigneFormation:
    """Une ligne des tableaux de formation (8.1, 8.2)."""

    intitule: str = ""  # toujours suivi implicitement de "ou équivalent reconnu"
    exige: bool = False
    souhaite: bool = False


@dataclass
class LigneExperience:
    """Une ligne du tableau Section 8.3."""

    domaine: str = ""
    annees_minimum: str = ""  # "5 ans", "Souhaité", "—"


@dataclass
class LigneLangue:
    """Une ligne du tableau Section 8.4."""

    langue: str = ""  # "Français", "Allemand", "Anglais", "Italien"
    niveau_cefr: str = ""  # ∈ NIVEAU_CEFR ou vide
    exige: bool = False
    souhaite: bool = False


@dataclass
class ProfilAttendu:
    """Section 8 complète."""

    formation_base: list[LigneFormation] = field(default_factory=list)
    formation_complementaire: list[LigneFormation] = field(default_factory=list)
    experience: list[LigneExperience] = field(default_factory=list)
    langues: list[LigneLangue] = field(default_factory=list)
    connaissances_particulieres: str = ""  # texte libre


# --- Section 9 — Compétences -------------------------------------------


@dataclass
class Competences:
    """Section 9 — 4 sous-sections. Les managériales sont conditionnelles
    au nombre de subordonnés directs > 0 (cf. Identification)."""

    socles: list[str] = field(default_factory=list)
    transversales: list[str] = field(default_factory=list)
    metier: list[str] = field(default_factory=list)
    manageriales: list[str] = field(default_factory=list)


# --- Section 11 — Signatures -------------------------------------------


@dataclass
class BlocSignature:
    """Un bloc de signature (employeur ou titulaire)."""

    nom: str = ""
    fonction: str = ""
    date: str = ""
    signe: bool = False


# --- Métadonnées techniques du document --------------------------------


@dataclass
class MetaDocument:
    """Métadonnées techniques. Correspond à la clé `_meta` imposée
    par `EditorModuleBase.META_KEY`."""

    version_schema: str = "1.0"
    cree_le: str = ""           # ISO 8601
    cree_par: str = ""          # email / id utilisateur Arhiane
    modifie_le: str = ""
    modifie_par: str = ""
    entite_id: str = ""         # entité Arhiane à la création
    langue: str = "fr"          # "fr" | "de"
    statut: str = "brouillon"   # ∈ STATUT_CDC
    commentaire_version: str = ""


# --- Document complet --------------------------------------------------


@dataclass
class CahierDesCharges:
    """Document complet — 11 sections canoniques + métadonnées.

    Pendant l'édition, n'importe quelle section peut être partielle
    ou vide. Les validations strictes (somme des %, compétences
    managériales si subordonnés > 0, etc.) sont externalisées dans
    `checks.py` — ce dataclass reste un pur conteneur de données.

    Les sections toggables "Non applicable" (5, 6, 10) utilisent
    None pour indiquer le mode N/A. Une liste vide signifie
    "section applicable mais pas encore remplie".
    """

    # Section 1 — Identification
    identification: Identification = field(default_factory=Identification)

    # Section 2 — Raison d'être (paragraphe libre 300-400 chars)
    raison_detre: str = ""

    # Section 3 — Missions principales (4 à 7 entrées)
    missions_principales: list[MissionPrincipale] = field(default_factory=list)

    # Section 4 — Missions et activités détaillées
    missions_detaillees: list[MissionDetaillee] = field(default_factory=list)

    # Section 5 — Responsabilités particulières (toggable N/A)
    responsabilites_particulieres: list[str] | None = field(default_factory=list)

    # Section 6 — Relations (toggable N/A)
    relations_internes: list[Relation] | None = field(default_factory=list)
    relations_externes: list[Relation] | None = field(default_factory=list)

    # Section 7 — Pouvoirs de décision
    pouvoirs_decision: PouvoirsDecision = field(default_factory=PouvoirsDecision)

    # Section 8 — Profil attendu
    profil_attendu: ProfilAttendu = field(default_factory=ProfilAttendu)

    # Section 9 — Compétences
    competences: Competences = field(default_factory=Competences)

    # Section 10 — Conditions particulières (toggable N/A)
    conditions_particulieres: list[str] | None = field(default_factory=list)

    # Section 11 — Signatures
    signature_employeur: BlocSignature = field(default_factory=BlocSignature)
    signature_titulaire: BlocSignature = field(default_factory=BlocSignature)
    recrutement_en_cours: bool = False  # si True, le bloc titulaire est remplacé

    # Métadonnées (clé réservée _meta)
    meta: MetaDocument = field(default_factory=MetaDocument)

    # --- Sérialisation -------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Conversion en dict JSON-sérialisable.

        La clé `_meta` est extraite au niveau racine (contrat imposé
        par `EditorModuleBase.META_KEY`).
        """
        d = asdict(self)
        d["_meta"] = d.pop("meta")
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CahierDesCharges:
        """Désérialisation tolérante : clés inconnues ignorées, clés
        manquantes prennent la valeur par défaut.

        On n'utilise pas une lib (dataclass-wizard, pydantic) pour
        rester dans l'esprit "pas de dépendance externe majeure" de
        la doctrine Arhiane. Coût : ~40 lignes de code ici, lisibles.
        """
        if not isinstance(data, dict):
            raise ValueError("CahierDesCharges.from_dict attend un dict.")

        meta_raw = data.get("_meta") or data.get("meta") or {}

        ident_raw = data.get("identification") or {}
        ident = Identification(**_filter_kwargs(Identification, ident_raw))

        missions_p = [
            MissionPrincipale(**_filter_kwargs(MissionPrincipale, m))
            for m in data.get("missions_principales") or []
            if isinstance(m, dict)
        ]

        missions_d = [
            MissionDetaillee(**_filter_kwargs(MissionDetaillee, m))
            for m in data.get("missions_detaillees") or []
            if isinstance(m, dict)
        ]

        resp = data.get("responsabilites_particulieres")
        if resp is not None and not isinstance(resp, list):
            resp = []

        rel_int = data.get("relations_internes")
        if rel_int is not None:
            rel_int = [
                Relation(**_filter_kwargs(Relation, r))
                for r in rel_int if isinstance(r, dict)
            ]
        rel_ext = data.get("relations_externes")
        if rel_ext is not None:
            rel_ext = [
                Relation(**_filter_kwargs(Relation, r))
                for r in rel_ext if isinstance(r, dict)
            ]

        pouvoirs = PouvoirsDecision(
            **_filter_kwargs(PouvoirsDecision, data.get("pouvoirs_decision") or {})
        )

        profil_raw = data.get("profil_attendu") or {}
        profil = ProfilAttendu(
            formation_base=[
                LigneFormation(**_filter_kwargs(LigneFormation, f))
                for f in profil_raw.get("formation_base") or []
                if isinstance(f, dict)
            ],
            formation_complementaire=[
                LigneFormation(**_filter_kwargs(LigneFormation, f))
                for f in profil_raw.get("formation_complementaire") or []
                if isinstance(f, dict)
            ],
            experience=[
                LigneExperience(**_filter_kwargs(LigneExperience, e))
                for e in profil_raw.get("experience") or []
                if isinstance(e, dict)
            ],
            langues=[
                LigneLangue(**_filter_kwargs(LigneLangue, lang))
                for lang in profil_raw.get("langues") or []
                if isinstance(lang, dict)
            ],
            connaissances_particulieres=profil_raw.get(
                "connaissances_particulieres", ""
            ),
        )

        comp = Competences(**_filter_kwargs(Competences, data.get("competences") or {}))

        cond = data.get("conditions_particulieres")
        if cond is not None and not isinstance(cond, list):
            cond = []

        sig_emp = BlocSignature(
            **_filter_kwargs(BlocSignature, data.get("signature_employeur") or {})
        )
        sig_tit = BlocSignature(
            **_filter_kwargs(BlocSignature, data.get("signature_titulaire") or {})
        )

        meta = MetaDocument(**_filter_kwargs(MetaDocument, meta_raw))

        return cls(
            identification=ident,
            raison_detre=data.get("raison_detre", ""),
            missions_principales=missions_p,
            missions_detaillees=missions_d,
            responsabilites_particulieres=resp,
            relations_internes=rel_int,
            relations_externes=rel_ext,
            pouvoirs_decision=pouvoirs,
            profil_attendu=profil,
            competences=comp,
            conditions_particulieres=cond,
            signature_employeur=sig_emp,
            signature_titulaire=sig_tit,
            recrutement_en_cours=bool(data.get("recrutement_en_cours", False)),
            meta=meta,
        )


# --- Helpers internes --------------------------------------------------


def _filter_kwargs(cls: type, raw: dict[str, Any]) -> dict[str, Any]:
    """Garde uniquement les clés dict qui correspondent à des champs du
    dataclass. Tolère les clés inconnues (utile quand le schéma évolue).
    """
    if not isinstance(raw, dict):
        return {}
    # __dataclass_fields__ existe sur toute dataclass (hasattr safe).
    fields_ = getattr(cls, "__dataclass_fields__", {})
    return {k: v for k, v in raw.items() if k in fields_}


# --- Identifiants de section (alignés avec EditorModuleBase.sections()) -


# Ordre canonique des 11 sections pour l'UI (navigation gauche de l'éditeur).
# Chaque id est la clé stable utilisée dans le document JSON.
SECTION_IDS: tuple[str, ...] = (
    "identification",              # §1
    "raison_detre",                # §2
    "missions_principales",        # §3
    "missions_detaillees",         # §4
    "responsabilites_particulieres",  # §5 (toggable)
    "relations",                   # §6 (internes + externes + toggable)
    "pouvoirs_decision",           # §7
    "profil_attendu",              # §8
    "competences",                 # §9
    "conditions_particulieres",    # §10 (toggable)
    "signatures",                  # §11
)


# Sections qui supportent le mode "Non applicable" (toggable).
SECTIONS_TOGGABLES: frozenset[str] = frozenset({
    "responsabilites_particulieres",
    "relations",
    "conditions_particulieres",
})
