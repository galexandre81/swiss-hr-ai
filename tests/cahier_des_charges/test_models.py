"""Tests des modèles de données du cahier des charges.

On vérifie :
    - la création d'un document vide (valeurs par défaut cohérentes)
    - le roundtrip to_dict / from_dict
    - la tolérance aux clés manquantes ou inconnues
    - la sérialisation de la clé réservée `_meta`
"""

from __future__ import annotations

import pytest

from _app.modules.cahier_des_charges.models import (
    SECTION_IDS,
    SECTIONS_TOGGABLES,
    CahierDesCharges,
    Identification,
    MissionDetaillee,
    MissionPrincipale,
    Relation,
)


def test_empty_document_has_11_sections():
    """L'ordre canonique couvre 11 sections."""
    assert len(SECTION_IDS) == 11


def test_toggables_are_subset_of_sections():
    assert SECTIONS_TOGGABLES <= set(SECTION_IDS)


def test_empty_document_to_dict_has_meta_key():
    doc = CahierDesCharges()
    d = doc.to_dict()
    # Clé _meta au niveau racine (contrat EditorModuleBase).
    assert "_meta" in d
    assert "meta" not in d
    # Les 11 sections sont représentées (avec leur nom interne).
    for key in [
        "identification",
        "raison_detre",
        "missions_principales",
        "missions_detaillees",
        "pouvoirs_decision",
        "profil_attendu",
        "competences",
        "signature_employeur",
        "signature_titulaire",
    ]:
        assert key in d


def test_roundtrip_empty():
    doc = CahierDesCharges()
    restored = CahierDesCharges.from_dict(doc.to_dict())
    assert restored.to_dict() == doc.to_dict()


def test_roundtrip_rich_document():
    doc = CahierDesCharges(
        identification=Identification(
            intitule_poste="Responsable comptable",
            categorie_cadre="cadre_operationnel",
            taux_activite=80,
            nombre_subordonnes_directs=2,
        ),
        raison_detre="Garantir la tenue des comptes et le respect des obligations.",
        missions_principales=[
            MissionPrincipale(ordre=1, libelle="Piloter la comptabilité"),
            MissionPrincipale(ordre=2, libelle="Encadrer l'équipe"),
        ],
        missions_detaillees=[
            MissionDetaillee(
                ordre=1,
                libelle="Piloter la comptabilité",
                pourcentage_temps=60,
                activites_strategiques=["[S] Arbitrer les provisions"],
                activites_operationnelles=["[O] Établir les comptes annuels"],
                livrables_attendus=["Comptes annuels au 31 mars"],
                indicateurs_succes=["Zéro redressement TVA sur 3 ans"],
            ),
        ],
        relations_internes=[
            Relation(interlocuteur="Direction", frequence="Mensuelle", objet="Reporting"),
        ],
    )
    data = doc.to_dict()
    restored = CahierDesCharges.from_dict(data)
    assert restored.to_dict() == data
    assert restored.identification.intitule_poste == "Responsable comptable"
    assert len(restored.missions_detaillees) == 1
    assert restored.missions_detaillees[0].total_activites() == 2


def test_from_dict_tolerates_unknown_keys():
    """Un document avec des clés parasites (ex: vieille version du
    schéma) ne doit pas crasher."""
    data = {
        "identification": {
            "intitule_poste": "Assistant",
            "champ_inconnu_historique": "blabla",
        },
        "raison_detre": "Soutenir l'équipe.",
        "champ_tout_en_haut_inconnu": 42,
    }
    doc = CahierDesCharges.from_dict(data)
    assert doc.identification.intitule_poste == "Assistant"
    assert doc.raison_detre == "Soutenir l'équipe."


def test_from_dict_accepts_meta_or_underscore_meta():
    """Que le dict fournisse `meta` ou `_meta`, la désérialisation
    trouve les métadonnées."""
    d1 = {"_meta": {"cree_par": "alice@example.ch"}}
    d2 = {"meta": {"cree_par": "alice@example.ch"}}
    for d in (d1, d2):
        doc = CahierDesCharges.from_dict(d)
        assert doc.meta.cree_par == "alice@example.ch"


def test_from_dict_rejects_non_dict():
    with pytest.raises(ValueError):
        CahierDesCharges.from_dict("pas un dict")  # type: ignore[arg-type]


def test_toggable_none_preserved():
    """Les sections toggables (5, 6, 10) supportent None = N/A."""
    doc = CahierDesCharges(
        responsabilites_particulieres=None,
        relations_internes=None,
        relations_externes=None,
        conditions_particulieres=None,
    )
    data = doc.to_dict()
    assert data["responsabilites_particulieres"] is None
    assert data["relations_internes"] is None
    restored = CahierDesCharges.from_dict(data)
    assert restored.responsabilites_particulieres is None
    assert restored.conditions_particulieres is None
