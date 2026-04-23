"""Tests de persistance du catalogue — fichiers JSON par entité.

Couvre : CRUD, versioning (minor/major), duplication, bascule de
version active, corbeille TTL 30j, isolation multi-entité, robustesse
(reconstruction de l'index après suppression).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from _app.core.entity_manager import EntityManager
from _app.modules.cahier_des_charges.catalogue_store import (
    CATALOGUE_SUBDIR,
    INDEX_FILENAME,
    CatalogueError,
    CatalogueStore,
    PosteIntrouvable,
    VersionInfo,
    VersionIntrouvable,
)
from _app.modules.cahier_des_charges.models import CahierDesCharges, Identification

# --- Fixtures ---------------------------------------------------------


@pytest.fixture
def entity(sandbox) -> Path:
    mgr = EntityManager()
    ent = mgr.create({"nom": "Gates Solutions SA"})
    return ent.dossier


@pytest.fixture
def store(entity) -> CatalogueStore:
    return CatalogueStore(entity)


def make_doc(intitule: str = "Assistant administratif") -> dict:
    return CahierDesCharges(
        identification=Identification(
            intitule_poste=intitule,
            categorie_cadre="collaborateur",
            departement="Administration",
        ),
        raison_detre="Soutenir l'équipe dans les tâches administratives.",
    ).to_dict()


# --- VersionInfo ------------------------------------------------------


def test_version_info_parse_and_bump():
    v = VersionInfo.parse("v1.2")
    assert v.majeure == 1
    assert v.mineure == 2
    assert str(v.bump_minor()) == "v1.3"
    assert str(v.bump_major()) == "v2.0"


def test_version_info_rejects_invalid():
    with pytest.raises(ValueError):
        VersionInfo.parse("1.0")
    with pytest.raises(ValueError):
        VersionInfo.parse("version_1")


# --- Structure de base -----------------------------------------------


def test_store_creates_catalogue_dir(entity):
    CatalogueStore(entity)
    assert (entity / CATALOGUE_SUBDIR).is_dir()
    assert (entity / CATALOGUE_SUBDIR / "_corbeille").is_dir()


def test_store_rejects_missing_entity(sandbox):
    with pytest.raises(CatalogueError):
        CatalogueStore(sandbox / "Entities" / "n_existe_pas")


# --- CRUD de base -----------------------------------------------------


def test_create_poste_returns_id_and_v1(store):
    poste_id, version = store.create(make_doc(), cree_par="alice@ex.ch")
    assert version == "v1.0"
    assert poste_id  # non-vide
    assert len(poste_id) <= 16  # id court


def test_create_persists_metadata(store):
    pid, _ = store.create(make_doc(), cree_par="alice@ex.ch")
    doc = store.get(pid)
    meta = doc["_meta"]
    assert meta["cree_par"] == "alice@ex.ch"
    assert meta["modifie_par"] == "alice@ex.ch"
    assert meta["statut"] == "brouillon"
    assert meta["cree_le"]


def test_get_unknown_poste_raises(store):
    with pytest.raises(PosteIntrouvable):
        store.get("n_existe_pas")


def test_get_unknown_version_raises(store):
    pid, _ = store.create(make_doc(), cree_par="alice@ex.ch")
    with pytest.raises(VersionIntrouvable):
        store.get(pid, version="v9.9")


# --- Listage + filtres -----------------------------------------------


def test_list_empty(store):
    assert store.list() == []


def test_list_returns_created_postes(store):
    store.create(make_doc("Poste A"), cree_par="x")
    store.create(make_doc("Poste B"), cree_par="x")
    entries = store.list()
    assert len(entries) == 2
    titles = {e.intitule_poste for e in entries}
    assert titles == {"Poste A", "Poste B"}


def test_list_filter_by_statut(store):
    pa, _ = store.create(make_doc("A"), cree_par="x")
    pb, _ = store.create(make_doc("B"), cree_par="x")
    store.set_statut(pa, "valide")
    entries = store.list(statut="valide")
    assert len(entries) == 1
    assert entries[0].poste_id == pa


def test_list_search_texte(store):
    store.create(make_doc("Comptable senior"), cree_par="x")
    store.create(make_doc("Assistant juridique"), cree_par="x")
    assert len(store.list(texte="comptable")) == 1
    assert len(store.list(texte="juridique")) == 1
    assert len(store.list(texte="truc")) == 0


# --- Versioning -------------------------------------------------------


def test_save_autosave_overwrites_active(store):
    pid, _ = store.create(make_doc("Assistant"), cree_par="alice@ex.ch")
    doc = store.get(pid)
    doc["raison_detre"] = "Version éditée."
    returned = store.save(pid, doc, modifie_par="alice@ex.ch")
    assert returned == "v1.0"  # auto-save = même version
    assert store.list_versions(pid) == ["v1.0"]
    assert store.get(pid)["raison_detre"] == "Version éditée."


def test_save_new_version_minor_bumps_mineure(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    returned = store.save(pid, make_doc(), modifie_par="x", new_version="minor")
    assert returned == "v1.1"
    versions = store.list_versions(pid)
    assert versions == ["v1.0", "v1.1"]


def test_save_new_version_major_bumps_majeure(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    store.save(pid, make_doc(), modifie_par="x", new_version="minor")  # v1.1
    returned = store.save(pid, make_doc(), modifie_par="x", new_version="major")
    assert returned == "v2.0"
    assert store.list_versions(pid) == ["v1.0", "v1.1", "v2.0"]


def test_save_new_version_invalid_raises(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    with pytest.raises(ValueError):
        store.save(pid, make_doc(), modifie_par="x", new_version="bizarre")


def test_set_active_version_switches_back(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    store.save(pid, make_doc(), modifie_par="x", new_version="minor")  # v1.1
    store.set_active_version(pid, "v1.0")
    entries = store.list()
    assert entries[0].version_active == "v1.0"


def test_set_active_unknown_version_raises(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    with pytest.raises(VersionIntrouvable):
        store.set_active_version(pid, "v9.9")


# --- Duplication ------------------------------------------------------


def test_duplicate_creates_new_poste_with_fresh_meta(store):
    src, _ = store.create(
        make_doc("Commercial régional Vaud"), cree_par="alice@ex.ch"
    )
    new_id = store.duplicate(
        src, cree_par="bob@ex.ch", nouveau_intitule="Commercial régional Genève"
    )
    assert new_id != src
    doc_new = store.get(new_id)
    assert doc_new["identification"]["intitule_poste"] == "Commercial régional Genève"
    assert doc_new["_meta"]["cree_par"] == "bob@ex.ch"
    # L'original est intact
    doc_src = store.get(src)
    assert doc_src["identification"]["intitule_poste"] == "Commercial régional Vaud"


# --- Statut -----------------------------------------------------------


def test_set_statut_updates_index_and_file(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    store.set_statut(pid, "valide")
    assert store.get(pid)["_meta"]["statut"] == "valide"
    assert store.list()[0].statut == "valide"


def test_set_statut_rejects_invalid(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    with pytest.raises(ValueError):
        store.set_statut(pid, "en_cours_de_validation")


# --- Corbeille (soft-delete) -----------------------------------------


def test_delete_soft_moves_to_trash(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    trash_id = store.delete_soft(pid, supprime_par="alice@ex.ch")
    assert store.list() == []                                  # retiré de l'index
    trash = store.list_trash()
    assert len(trash) == 1
    assert trash[0]["trash_id"] == trash_id
    assert trash[0]["supprime_par"] == "alice@ex.ch"
    assert trash[0]["original_poste_id"] == pid


def test_restore_trash_brings_poste_back(store):
    pid, _ = store.create(make_doc("X"), cree_par="x")
    trash_id = store.delete_soft(pid, supprime_par="x")
    restored_id = store.restore_trash(trash_id)
    assert restored_id == pid
    entries = store.list()
    assert len(entries) == 1
    assert entries[0].poste_id == pid


def test_restore_trash_handles_id_collision(store):
    pid1, _ = store.create(make_doc("X"), cree_par="x")
    trash_id = store.delete_soft(pid1, supprime_par="x")
    # Même id réutilisé entre-temps
    store.create(make_doc("X"), cree_par="x", poste_id=pid1)
    restored = store.restore_trash(trash_id)
    assert restored != pid1
    assert restored.startswith(pid1)  # suffixe ajouté


def test_delete_hard_removes_definitively(store):
    pid, _ = store.create(make_doc(), cree_par="x")
    trash_id = store.delete_soft(pid, supprime_par="x")
    store.delete_hard(trash_id)
    assert store.list_trash() == []
    with pytest.raises(PosteIntrouvable):
        store.delete_hard(trash_id)


def test_purge_expired_only_removes_old_entries(store, monkeypatch):
    """On simule une entrée de corbeille dont la date de rétention est
    dépassée en patchant le fichier de meta."""
    pid1, _ = store.create(make_doc("Vieux"), cree_par="x")
    pid2, _ = store.create(make_doc("Recent"), cree_par="x")

    trash_old = store.delete_soft(pid1, supprime_par="x")
    store.delete_soft(pid2, supprime_par="x")

    # On rétroactive la date de rétention du vieux poste à hier.
    import json as _json
    meta_file = (
        store._trash_dir / trash_old / "_trash_meta.json"  # type: ignore[attr-defined]
    )
    meta = _json.loads(meta_file.read_text(encoding="utf-8"))
    meta["restaurable_jusquau"] = (datetime.now() - timedelta(days=1)).isoformat(
        timespec="seconds"
    )
    meta_file.write_text(
        _json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    purged = store.purge_expired()
    assert purged == 1
    remaining = {t["original_poste_id"] for t in store.list_trash()}
    assert remaining == {pid2}


# --- Reconstruction d'index ------------------------------------------


def test_index_rebuilt_after_manual_deletion(entity, store):
    pid, _ = store.create(make_doc("Test"), cree_par="x")
    # Simulation : utilisateur supprime manuellement _index.json
    (entity / CATALOGUE_SUBDIR / INDEX_FILENAME).unlink()
    # Le store doit reconstruire silencieusement.
    store2 = CatalogueStore(entity)
    entries = store2.list()
    assert len(entries) == 1
    assert entries[0].poste_id == pid


def test_index_rebuilt_after_corruption(entity, store):
    pid, _ = store.create(make_doc("Test"), cree_par="x")
    index_file = entity / CATALOGUE_SUBDIR / INDEX_FILENAME
    index_file.write_text("ce n'est pas du JSON valide {{{", encoding="utf-8")
    store2 = CatalogueStore(entity)
    entries = store2.list()
    assert len(entries) == 1
    assert entries[0].poste_id == pid


# --- Isolation multi-entité ------------------------------------------


def test_two_entities_have_independent_catalogues(sandbox):
    mgr = EntityManager()
    ea = mgr.create({"nom": "Alpha SA"})
    eb = mgr.create({"nom": "Beta SA"})
    sa = CatalogueStore(ea.dossier)
    sb = CatalogueStore(eb.dossier)
    sa.create(make_doc("Poste alpha"), cree_par="x")
    sb.create(make_doc("Poste beta 1"), cree_par="x")
    sb.create(make_doc("Poste beta 2"), cree_par="x")
    assert len(sa.list()) == 1
    assert len(sb.list()) == 2
    assert sa.list()[0].intitule_poste == "Poste alpha"
