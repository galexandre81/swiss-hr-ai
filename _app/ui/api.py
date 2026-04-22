"""Pont JavaScript <-> Python pour PyWebView.

Toutes les méthodes publiques de la classe Api sont exposées au JS sous
la forme `window.pywebview.api.<methode>(...)` et retournent des objets
JSON-sérialisables.

Règle d'or : JAMAIS de Path ni d'objets Python non-sérialisables dans
les retours — on renvoie toujours des dicts/listes/strings. Toute erreur
remonte sous la forme `{"erreur": "..."}` en français, jamais une stack
trace brute.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import webview

from _app.core import (
    STANDARD_CRITERES_FR,
    AuditTrail,
    BlacklistDetector,
    DossierStore,
    EntityManager,
    FormulationLibrary,
    GenerationCancelled,
    LLMClient,
    ModuleContext,
    ModuleRegistry,
    QuestionnaireContext,
    QuestionnaireEngine,
    WizardModuleBase,
    get_config,
    get_logger,
    safe_within,
    save_user_preferences,
)

# Extensions autorisées pour l'archivage de documents sources.
# On reste permissif (doc et img classiques) ; la liste peut évoluer
# côté config plus tard.
_DOCUMENT_EXTS = frozenset({
    ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp",
    ".xlsx", ".xls", ".csv",
    ".msg", ".eml",
})
# Taille max d'un fichier archivé : 50 Mo. Au-delà, on refuse (rapide garde-fou).
_DOCUMENT_MAX_BYTES = 50 * 1024 * 1024

# Pattern de validation d'une couleur hexadécimale #RRGGBB.
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Clés autorisées pour open_folder — mapping fermé pour empêcher toute
# lecture hors des dossiers projet.
_FOLDER_KEYS = {
    "base_juridique", "templates", "entities", "outputs", "logs",
    "dossiers", "bibliotheques",
}


class Api:
    """API exposée au frontend HTML."""

    def __init__(self):
        self._cfg = get_config()
        self._log = get_logger()
        self._llm = LLMClient()
        self._entities = EntityManager()
        self._registry = ModuleRegistry()
        # Services pour les modules wizard (certificats et +).
        self._dossiers = DossierStore()
        self._formulations = FormulationLibrary()
        self._blacklist = BlacklistDetector()
        # Streams actifs : id → Event de cancellation.
        self._streams: dict[str, threading.Event] = {}

    def _make_ctx(self, *, extras: dict[str, Any] | None = None) -> ModuleContext:
        return ModuleContext(
            llm=self._llm,
            entity=self._entities.active,
            logger=self._log,
            dossiers=self._dossiers,
            formulations=self._formulations,
            blacklist=self._blacklist,
            extras=extras or {},
        )

    # --- Statut général (pour la barre du bas) ---------------------------

    def status(self) -> dict[str, Any]:
        llm_info = self._llm.status()
        active = self._entities.active
        return {
            "llm": llm_info.as_dict(),
            "entite_active": active.as_dict() if active else None,
            "nb_entites": len(self._entities.all()),
            "version": "0.1.0",
            "hors_ligne": True,
        }

    def settings(self) -> dict[str, Any]:
        """Préférences utilisateur persistées."""
        return {
            "theme": self._cfg.theme,
            "couleur_primaire": self._cfg.couleur_primaire,
            "audit_log_prompts": self._cfg.audit_log_prompts,
            "langue": self._cfg.langue,
        }

    def update_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        if "theme" in updates and updates["theme"] in {"auto", "light", "dark"}:
            clean["theme"] = updates["theme"]
        if "audit_log_prompts" in updates:
            clean["audit_log_prompts"] = bool(updates["audit_log_prompts"])
        if "couleur_primaire" in updates:
            val = str(updates["couleur_primaire"]).strip()
            if _HEX_COLOR_RE.match(val):
                clean["couleur_primaire"] = val.upper()
            # Valeur invalide : on l'ignore silencieusement (pas de throw).
        if clean:
            save_user_preferences(clean)
        return self.settings()

    # --- Entités ---------------------------------------------------------

    def list_entities(self) -> list[dict[str, Any]]:
        return [e.as_dict() for e in self._entities.all()]

    def set_active_entity(self, entity_id: str) -> dict[str, Any] | None:
        ent = self._entities.set_active(entity_id)
        if ent is None:
            return None
        save_user_preferences({"entite_active": entity_id})
        return ent.as_dict()

    def rescan_entities(self) -> list[dict[str, Any]]:
        self._entities.rescan()
        return self.list_entities()

    def update_entity(self, entity_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Met à jour les champs d'une entité (nom, adresse, signataire, etc.)."""
        allowed = {
            "nom", "forme_juridique", "adresse", "telephone", "email",
            "signataire_nom", "signataire_fonction",
        }
        clean = {k: v for k, v in data.items() if k in allowed}
        try:
            ent = self._entities.update(entity_id, clean)
        except ValueError as exc:
            return {"erreur": str(exc)}
        except OSError as exc:
            self._log.error(f"Mise à jour entité échouée : {exc!r}")
            return {"erreur": "Enregistrement impossible."}
        return {"entite": ent.as_dict()}

    def get_entity(self, entity_id: str) -> dict[str, Any]:
        """Retourne les champs éditables d'une entité (pour pré-remplir un form)."""
        for e in self._entities.all():
            if e.id == entity_id:
                return {
                    "id": e.id,
                    "nom": e.nom,
                    "forme_juridique": e.forme_juridique,
                    "adresse": e.adresse,
                    "telephone": e.telephone,
                    "email": e.email,
                    "signataire_nom": e.signataire_nom,
                    "signataire_fonction": e.signataire_fonction,
                }
        return {"erreur": "Entité introuvable."}

    def entity_pick_and_set_asset(self, entity_id: str, kind: str) -> dict[str, Any]:
        """Ouvre un sélecteur natif et installe l'image comme logo ou signature.

        `kind` ∈ {"logo", "signature"}.
        """
        if kind not in {"logo", "signature"}:
            return {"erreur": "Type d'asset invalide."}
        if not webview.windows:
            return {"erreur": "Fenêtre UI indisponible."}
        try:
            picked = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("Images (*.png;*.jpg;*.jpeg;*.webp)", "Tous les fichiers (*.*)"),
            )
        except Exception as exc:
            self._log.error(f"File dialog asset : {exc!r}")
            return {"erreur": "Impossible d'ouvrir le sélecteur."}
        if not picked:
            return {"annule": True}
        src = Path(str(picked[0]))
        try:
            ent = self._entities.set_asset(entity_id, kind, src)
        except ValueError as exc:
            return {"erreur": str(exc)}
        except OSError as exc:
            self._log.error(f"Copie asset échouée : {exc!r}")
            return {"erreur": "Copie impossible."}
        return {"entite": ent.as_dict()}

    def entity_remove_asset(self, entity_id: str, kind: str) -> dict[str, Any]:
        if kind not in {"logo", "signature"}:
            return {"erreur": "Type d'asset invalide."}
        try:
            ent = self._entities.remove_asset(entity_id, kind)
        except ValueError as exc:
            return {"erreur": str(exc)}
        return {"entite": ent.as_dict()}

    def create_entity(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            ent = self._entities.create(data)
        except ValueError as exc:
            return {"erreur": str(exc)}
        except OSError as exc:
            self._log.error(f"Création entité échouée : {exc!r}")
            return {"erreur": "Impossible de créer le dossier d'entité."}
        self._entities.set_active(ent.id)
        save_user_preferences({"entite_active": ent.id})
        return {"entite": ent.as_dict()}

    # --- Modules ---------------------------------------------------------

    def list_modules(self) -> list[dict[str, Any]]:
        return self._registry.list_modules()

    def run_module(self, module_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Exécution non-streamée — retourne le résultat complet."""
        mod = self._registry.get(module_id)
        if mod is None:
            return {"erreur": f"Module « {module_id} » non disponible (à venir)."}
        if isinstance(mod, WizardModuleBase):
            return {"erreur": "Ce module est un wizard : utilisez l'API wizard_*."}
        ctx = self._make_ctx()
        try:
            result = mod.run(inputs, ctx)
        except Exception as exc:
            self._log.error(f"Module {module_id} a échoué : {exc!r}")
            return {"erreur": "La génération a échoué. Consultez les logs pour le détail."}
        self._log.audit(
            "module_run",
            module=module_id,
            entity=self._entities.active.id if self._entities.active else None,
            inputs_keys=list(inputs.keys()),
        )
        return result

    # --- API Wizard ------------------------------------------------------

    def wizard_describe(self, module_id: str) -> dict[str, Any]:
        """Retourne les steps d'un module wizard pour l'UI."""
        mod = self._registry.get(module_id)
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": f"Module wizard « {module_id} » introuvable."}
        return {
            "id": mod.id,
            "nom": mod.nom,
            "description": mod.description,
            "steps": [s.as_dict() for s in mod.steps()],
        }

    def wizard_list_dossiers(self) -> list[dict[str, Any]]:
        return self._dossiers.list()

    def wizard_create_dossier(self, module_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        mod = self._registry.get(module_id)
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": f"Module wizard « {module_id} » introuvable."}
        try:
            dossier = self._dossiers.create(
                nom=(payload.get("nom") or "").strip(),
                prenom=(payload.get("prenom") or "").strip(),
                entite_id=(self._entities.active.id if self._entities.active else ""),
                type_document=(payload.get("type_document") or "").strip(),
                langue=(payload.get("langue") or "fr").strip(),
                date_naissance=(payload.get("date_naissance") or "").strip(),
                lieu_origine=(payload.get("lieu_origine") or "").strip(),
            )
        except ValueError as exc:
            return {"erreur": str(exc)}
        # Pré-remplit l'étape "identité" avec ce que le RH a déjà saisi à la
        # création du dossier — évite la double saisie.
        state = mod.ensure_state({})
        civilite = (payload.get("civilite") or "").strip()
        genre = (payload.get("genre") or "").strip()
        # Déduction civilité ↔ genre si un seul des deux est fourni.
        if not genre and civilite:
            genre = {"Madame": "f", "Monsieur": "m"}.get(civilite, "")
        if not civilite and genre:
            civilite = {"f": "Madame", "m": "Monsieur"}.get(genre, "")
        state["answers"]["identite"] = {
            "type_document": dossier.type_document,
            "langue": dossier.langue,
            "civilite": civilite,
            "genre": genre,
            "prenom": dossier.collaborateur.prenom,
            "nom": dossier.collaborateur.nom,
            "date_naissance": dossier.collaborateur.date_naissance,
            "lieu_origine": dossier.collaborateur.lieu_origine,
        }
        dossier.wizard_state = state
        dossier.save()
        return {"dossier": self._dossier_summary(dossier)}

    def wizard_get_state(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        mod = self._registry.get("certificats")
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": "Module certificats indisponible."}
        state = mod.ensure_state(dossier.wizard_state)
        return {
            "dossier": self._dossier_summary(dossier),
            "state": state,
            "current_step": state.get("step", mod.first_step_id()),
        }

    def wizard_save_step(
        self,
        dossier_id: str,
        step_id: str,
        answers: dict[str, Any],
    ) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        mod = self._registry.get("certificats")
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": "Module certificats indisponible."}
        # Normalise les checkbox absentes → False.
        step = mod.step_by_id(step_id)
        if step is None:
            return {"erreur": f"Étape inconnue : {step_id}"}
        normalized = dict(answers)
        for f in step.inputs:
            if f.get("type") == "checkbox" and f["id"] not in normalized:
                normalized[f["id"]] = False

        errors = mod.validate_step(step_id, normalized)
        if errors:
            return {"erreurs": errors, "state": mod.ensure_state(dossier.wizard_state)}

        state = mod.record_answers(dossier.wizard_state, step_id, normalized)
        dossier.wizard_state = state
        dossier.save()
        return {"state": state, "current_step": state.get("step", "")}

    def wizard_preview(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        mod = self._registry.get("certificats")
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": "Module certificats indisponible."}
        ctx = self._make_ctx(extras={"dossier": dossier})
        return mod.preview(dossier.wizard_state, ctx)

    def wizard_finalize(self, dossier_id: str, force: bool = False) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        mod = self._registry.get("certificats")
        if not isinstance(mod, WizardModuleBase):
            return {"erreur": "Module certificats indisponible."}
        ok, missing = mod.can_finalize(dossier.wizard_state)
        if not ok:
            return {"erreur": "Étapes incomplètes : " + ", ".join(missing)}
        ctx = self._make_ctx(extras={"dossier": dossier, "force": bool(force)})
        try:
            return mod.finalize(dossier.wizard_state, ctx)
        except Exception as exc:
            self._log.error(f"Finalisation certificat {dossier_id} : {exc!r}")
            return {"erreur": "La finalisation a échoué. Consultez les logs."}

    def wizard_delete_dossier(self, dossier_id: str) -> dict[str, Any]:
        ok = self._dossiers.delete(dossier_id)
        return {"supprime": ok}

    # --- Documents sources (archivage §15.1) -----------------------------

    def documents_list(self, dossier_id: str) -> dict[str, Any]:
        """Liste les documents archivés d'un dossier (02_documents_sources)."""
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        folder = dossier.subfolder("02_documents_sources")
        items: list[dict[str, Any]] = []
        if folder.exists():
            for p in sorted(folder.iterdir(), key=lambda x: x.name.lower()):
                if not p.is_file():
                    continue
                try:
                    stat = p.stat()
                except OSError:
                    continue
                items.append({
                    "nom": p.name,
                    "taille": stat.st_size,
                    "modifie_le": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "extension": p.suffix.lower().lstrip("."),
                })
        return {"items": items}

    def documents_pick_and_attach(self, dossier_id: str) -> dict[str, Any]:
        """Ouvre le sélecteur de fichier natif et archive les fichiers choisis."""
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        if not webview.windows:
            return {"erreur": "Fenêtre UI indisponible."}
        try:
            picked = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=(
                    "Documents RH (PDF, Word, images)"
                    " (*.pdf;*.docx;*.doc;*.txt;*.rtf;*.png;*.jpg;*.jpeg;*.tiff;*.xlsx;*.xls;*.csv;*.msg;*.eml)",
                    "Tous les fichiers (*.*)",
                ),
            )
        except Exception as exc:
            self._log.error(f"File dialog échec : {exc!r}")
            return {"erreur": "Impossible d'ouvrir le sélecteur de fichiers."}
        if not picked:
            return {"items": [], "ajoutes": 0}
        return self._attach_paths(dossier, [str(p) for p in picked])

    def documents_remove(self, dossier_id: str, filename: str) -> dict[str, Any]:
        """Supprime (soft-delete) un document : déplacé vers un sous-dossier
        `_supprimes/` du dossier collaborateur, pour garder une trace.
        """
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        folder = dossier.subfolder("02_documents_sources")
        target = folder / filename
        # Sécurité : pas de traversée ; doit rester strictement sous folder.
        if safe_within(target, folder) is None or not target.is_file():
            return {"erreur": "Fichier introuvable dans ce dossier."}
        trash = folder / "_supprimes"
        trash.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        dst = trash / f"{target.stem}__{stamp}{target.suffix}"
        try:
            target.rename(dst)
        except OSError as exc:
            self._log.error(f"Suppression document échouée : {exc!r}")
            return {"erreur": "Suppression impossible."}
        # Trace d'audit
        try:
            trail = AuditTrail(dossier.racine)
            trail.append("document_removed", nom=filename, corbeille=dst.name)
        except Exception as exc:  # noqa: BLE001
            self._log.warning(f"Audit trail indisponible (rm document) : {exc!r}")
        return {"supprime": True, "corbeille": dst.name}

    # --- Managers & questionnaires (§15) ---------------------------------

    def managers_list(self, dossier_id: str) -> dict[str, Any]:
        """Liste les managers attachés au dossier + statut de leur questionnaire."""
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        managers = self._get_managers(dossier)
        vierges_folder = dossier.subfolder("03_questionnaires_managers/vierges")
        remplis_folder = dossier.subfolder("03_questionnaires_managers/remplis")

        enriched: list[dict[str, Any]] = []
        for m in managers:
            mid = m.get("id", "")
            vierge_nom = m.get("questionnaire_vierge") or ""
            vierge_present = bool(vierge_nom) and (vierges_folder / vierge_nom).exists()
            # Détection automatique des fichiers de réponse — heuristique :
            # tout PDF dans `remplis/` dont le nom contient l'id manager.
            reponses: list[str] = []
            if remplis_folder.exists() and mid:
                for p in remplis_folder.glob("*.pdf"):
                    if mid in p.stem:
                        reponses.append(p.name)
            enriched.append({
                **m,
                "questionnaire_present": vierge_present,
                "reponses_detectees": reponses,
            })
        return {"items": enriched}

    def managers_add(self, dossier_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        nom = (payload.get("nom") or "").strip()
        if not nom:
            return {"erreur": "Le nom du manager est obligatoire."}
        managers = self._get_managers(dossier)
        # id stable : slug du nom + index si conflit
        from _app.core.entity_manager import slugify
        base = slugify(nom, fallback="manager")
        mid = base
        existing = {m.get("id") for m in managers}
        i = 2
        while mid in existing:
            mid = f"{base}_{i}"
            i += 1
        manager = {
            "id": mid,
            "nom": nom,
            "fonction": (payload.get("fonction") or "").strip(),
            "periode_debut": (payload.get("periode_debut") or "").strip(),
            "periode_fin": (payload.get("periode_fin") or "").strip(),
            "ajoute_le": time.strftime("%Y-%m-%d %H:%M:%S"),
            "questionnaire_vierge": "",
        }
        managers.append(manager)
        self._set_managers(dossier, managers)
        dossier.save()
        try:
            AuditTrail(dossier.racine).append(
                "manager_added",
                manager_id=mid, nom=nom,
                periode=f"{manager['periode_debut']} → {manager['periode_fin']}",
            )
        except Exception as exc:  # noqa: BLE001
            self._log.warning(f"Audit indisponible (manager_add) : {exc!r}")
        return {"manager": manager}

    def managers_remove(self, dossier_id: str, manager_id: str) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        managers = self._get_managers(dossier)
        new_list = [m for m in managers if m.get("id") != manager_id]
        if len(new_list) == len(managers):
            return {"erreur": "Manager introuvable dans ce dossier."}
        self._set_managers(dossier, new_list)
        dossier.save()
        try:
            AuditTrail(dossier.racine).append("manager_removed", manager_id=manager_id)
        except Exception as exc:  # noqa: BLE001
            self._log.warning(f"Audit indisponible (manager_rm) : {exc!r}")
        return {"supprime": True}

    def managers_generate_questionnaire(
        self, dossier_id: str, manager_id: str
    ) -> dict[str, Any]:
        """Génère le PDF AcroForm du questionnaire pour un manager donné."""
        if not QuestionnaireEngine.is_available():
            return {"erreur": (
                "Génération PDF indisponible : reportlab n'est pas installé. "
                "Exécutez « pip install reportlab==4.2.2 »."
            )}
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        managers = self._get_managers(dossier)
        manager = next((m for m in managers if m.get("id") == manager_id), None)
        if manager is None:
            return {"erreur": "Manager introuvable."}

        # Paramètres à partir du dossier + entité active
        entity = self._entities.active
        identite = (dossier.wizard_state or {}).get("answers", {}).get("identite", {})
        parcours = (dossier.wizard_state or {}).get("answers", {}).get("parcours", {})

        logo_path = None
        if entity is not None and entity.logo_path.exists():
            logo_path = str(entity.logo_path)
        ctx = QuestionnaireContext(
            employeur_nom=(entity.nom if entity else ""),
            employeur_adresse=(entity.adresse if entity else ""),
            employeur_email_rh=(entity.email if entity else ""),
            collaborateur_prenom=dossier.collaborateur.prenom,
            collaborateur_nom=dossier.collaborateur.nom,
            fonction=(parcours.get("fonction", "") or identite.get("fonction", "")),
            periode_debut=manager.get("periode_debut", "") or parcours.get("date_debut", ""),
            periode_fin=manager.get("periode_fin", "") or parcours.get("date_fin", ""),
            manager_nom=manager.get("nom", ""),
            criteres=STANDARD_CRITERES_FR,
            langue=dossier.langue or "fr",
            couleur_primaire=self._cfg.couleur_primaire,
            logo_path=logo_path,
        )

        vierges_folder = dossier.subfolder("03_questionnaires_managers/vierges")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"questionnaire_{manager_id}_{stamp}.pdf"
        target = vierges_folder / filename
        if safe_within(target, vierges_folder) is None:
            return {"erreur": "Chemin invalide."}

        try:
            engine = QuestionnaireEngine()
            engine.generate_pdf(ctx, target)
        except RuntimeError as exc:
            return {"erreur": str(exc)}
        except Exception as exc:
            self._log.error(f"Génération questionnaire échouée : {exc!r}")
            return {"erreur": "Échec de génération du PDF."}

        manager["questionnaire_vierge"] = filename
        manager["questionnaire_genere_le"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._set_managers(dossier, managers)
        dossier.save()

        try:
            AuditTrail(dossier.racine).append(
                "questionnaire_generated",
                manager_id=manager_id, fichier=filename,
                sha256=_sha256_file(target)[:16],
            )
        except Exception as exc:  # noqa: BLE001
            self._log.warning(f"Audit indisponible (questionnaire gen) : {exc!r}")

        return {"fichier": filename, "chemin": str(target)}

    def managers_open_questionnaire_folder(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        folder = dossier.subfolder("03_questionnaires_managers")
        try:
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            self._log.error(f"Ouverture dossier questionnaires : {exc!r}")
            return {"erreur": "Impossible d'ouvrir le dossier."}
        return {"ouvert": True}

    # Helpers ----
    def _get_managers(self, dossier: Any) -> list[dict[str, Any]]:
        return list(
            (dossier.modules.get("certificats") or {}).get("managers", [])
        )

    def _set_managers(self, dossier: Any, managers: list[dict[str, Any]]) -> None:
        dossier.modules.setdefault("certificats", {})["managers"] = managers

    def documents_open_folder(self, dossier_id: str) -> dict[str, Any]:
        """Ouvre le dossier 02_documents_sources dans l'Explorateur Windows.

        Permet au RH de glisser-déposer directement des fichiers hors UI.
        """
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        folder = dossier.subfolder("02_documents_sources")
        try:
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            self._log.error(f"Ouverture dossier docs : {exc!r}")
            return {"erreur": "Impossible d'ouvrir le dossier."}
        return {"ouvert": True}

    # --- Helpers documents ----------------------------------------------

    def _attach_paths(self, dossier: Any, source_paths: list[str]) -> dict[str, Any]:
        """Copie une liste de fichiers dans `02_documents_sources/`.

        - Refuse les extensions hors whitelist.
        - Refuse les fichiers > _DOCUMENT_MAX_BYTES.
        - Gère les conflits de nom en ajoutant un suffixe _2, _3, …
        - Écrit un événement d'audit par fichier ajouté.
        """
        folder = dossier.subfolder("02_documents_sources")
        folder.mkdir(parents=True, exist_ok=True)

        added: list[dict[str, Any]] = []
        errors: list[str] = []
        trail: AuditTrail | None = None
        try:
            trail = AuditTrail(dossier.racine)
        except Exception as exc:  # noqa: BLE001
            self._log.warning(f"Audit trail indisponible (attach) : {exc!r}")

        for raw in source_paths:
            src = Path(raw)
            if not src.is_file():
                errors.append(f"{src.name} : fichier introuvable.")
                continue
            ext = src.suffix.lower()
            if ext not in _DOCUMENT_EXTS:
                errors.append(f"{src.name} : extension {ext or '(aucune)'} non autorisée.")
                continue
            try:
                size = src.stat().st_size
            except OSError:
                errors.append(f"{src.name} : fichier illisible.")
                continue
            if size > _DOCUMENT_MAX_BYTES:
                errors.append(
                    f"{src.name} : fichier trop volumineux ({size / 1024 / 1024:.1f} Mo > 50 Mo)."
                )
                continue

            # Conflit de nom → suffixe _2, _3, …
            target = folder / src.name
            if safe_within(target, folder) is None:
                errors.append(f"{src.name} : chemin refusé.")
                continue
            if target.exists():
                stem, suffix = src.stem, src.suffix
                i = 2
                while (folder / f"{stem}_{i}{suffix}").exists():
                    i += 1
                target = folder / f"{stem}_{i}{suffix}"

            try:
                shutil.copy2(src, target)
            except OSError as exc:
                errors.append(f"{src.name} : copie impossible ({exc}).")
                continue

            # Empreinte pour audit (§13 : rattachement de preuves).
            digest = _sha256_file(target)
            added.append({
                "nom": target.name,
                "source": str(src),
                "taille": size,
                "sha256_16": digest[:16],
            })
            if trail is not None:
                trail.append(
                    "document_attached",
                    nom=target.name,
                    taille=size,
                    sha256=digest,
                    source_chemin=str(src),
                )

        return {"ajoutes": len(added), "items": added, "erreurs": errors}

    def _dossier_summary(self, dossier: Any) -> dict[str, Any]:
        return {
            "id": dossier.id,
            "collaborateur": f"{dossier.collaborateur.prenom} {dossier.collaborateur.nom}".strip(),
            "entite_id": dossier.entite_id,
            "type_document": dossier.type_document,
            "langue": dossier.langue,
            "cree_le": dossier.cree_le,
            "maj_le": dossier.maj_le,
            "wizard_step": dossier.wizard_state.get("step", ""),
            "finalized": bool(dossier.wizard_state.get("finalized")),
        }

    # --- Streaming -------------------------------------------------------

    def start_stream(self, module_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Démarre une génération streamée. Retourne un stream_id.

        Côté JS, écouter `window.onStreamChunk(stream_id, text)`,
        `window.onStreamDone(stream_id, result)` et
        `window.onStreamError(stream_id, message)`.
        """
        mod = self._registry.get(module_id)
        if mod is None:
            return {"erreur": f"Module « {module_id} » non disponible."}

        stream_id = uuid.uuid4().hex[:12]
        cancel_event = threading.Event()
        self._streams[stream_id] = cancel_event

        thread = threading.Thread(
            target=self._run_stream,
            args=(stream_id, mod, inputs, cancel_event),
            daemon=True,
        )
        thread.start()
        return {"stream_id": stream_id}

    def cancel_stream(self, stream_id: str) -> bool:
        event = self._streams.get(stream_id)
        if event is None:
            return False
        event.set()
        return True

    def _run_stream(
        self,
        stream_id: str,
        mod: Any,
        inputs: dict[str, Any],
        cancel_event: threading.Event,
    ) -> None:
        ctx = ModuleContext(
            llm=self._llm,
            entity=self._entities.active,
            logger=self._log,
            extras={"cancel_event": cancel_event, "stream_id": stream_id,
                    "emit": lambda chunk: self._emit(stream_id, "Chunk", chunk)},
        )
        t0 = time.monotonic()
        try:
            result = mod.run(inputs, ctx)
        except GenerationCancelled:
            self._emit(stream_id, "Error", "Génération annulée.")
        except Exception as exc:
            self._log.error(f"Stream {stream_id} ({mod.id}) a échoué : {exc!r}")
            self._emit(stream_id, "Error", "La génération a échoué.")
        else:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._log.audit(
                "module_stream",
                module=mod.id,
                entity=self._entities.active.id if self._entities.active else None,
                duration_ms=duration_ms,
            )
            self._emit(stream_id, "Done", result)
        finally:
            self._streams.pop(stream_id, None)

    def _emit(self, stream_id: str, event: str, payload: Any) -> None:
        """Pousse un événement vers le frontend via evaluate_js."""
        if not webview.windows:
            return
        import json
        js = (
            f"window.onStream{event} && "
            f"window.onStream{event}({json.dumps(stream_id)}, {json.dumps(payload, ensure_ascii=False)});"
        )
        try:
            webview.windows[0].evaluate_js(js)
        except Exception as exc:
            self._log.error(f"evaluate_js a échoué ({event}) : {exc!r}")

    # --- Divers ----------------------------------------------------------

    def _documents_attach_raw(self, dossier_id: str, source_paths: list[str]) -> dict[str, Any]:
        """Chemin d'attache programmatique — utilisé par les tests.

        Ne passe PAS par la file dialog pywebview ; prend directement une
        liste de chemins déjà résolus.
        """
        dossier = self._dossiers.get(dossier_id)
        if dossier is None:
            return {"erreur": "Dossier introuvable."}
        return self._attach_paths(dossier, source_paths)

    def open_folder(self, dossier: str) -> bool:
        """Ouvre un dossier du projet dans l'Explorateur Windows.

        Seules les clés explicitement listées sont acceptées ; on valide
        aussi que le chemin résolu reste sous la racine projet (empêche
        toute attaque par chemin symbolique ou entité malicieuse).
        """
        if dossier not in _FOLDER_KEYS:
            return False

        mapping = {
            "base_juridique": self._cfg.chemin_base_juridique,
            "templates": self._cfg.chemin_templates,
            "entities": self._cfg.chemin_entities,
            "outputs": self._cfg.chemin_outputs,
            "logs": self._cfg.chemin_logs,
            "dossiers": self._cfg.chemin_dossiers,
            "bibliotheques": self._cfg.chemin_bibliotheques,
        }
        target = mapping.get(dossier)
        if target is None:
            return False

        safe = safe_within(target, self._cfg.root)
        if safe is None or not safe.exists():
            return False

        try:
            if os.name == "nt":
                os.startfile(str(safe))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(safe)])
            return True
        except Exception as exc:
            self._log.error(f"Ouverture dossier {dossier} échouée : {exc}")
            return False


def _sha256_file(path: Path) -> str:
    """SHA-256 hex d'un fichier, en streaming (pas de load complet en mémoire)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
