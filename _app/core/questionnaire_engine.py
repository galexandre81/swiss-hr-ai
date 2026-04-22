"""Génération du PDF questionnaire manager.

Conforme §15 de la spec certificats : page d'intro pédagogique, bloc
identification manager + période couverte, critères avec échelle 5★ +
exemple concret, rappel de confidentialité en pied.

**AcroForm** (formulaire PDF remplissable natif) pour permettre au
manager de saisir directement dans le PDF puis au RH d'extraire les
réponses à la réception (prochain passage Q2).

Reportlab est la dépendance — si absente, `generate_pdf()` lève un
RuntimeError clair et l'UI affiche un message métier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False


# Libellés des 5 niveaux (§15.4) — lisibles par le manager sous chaque étoile.
LEVEL_LABELS_FR = {
    1: "Nettement en-deçà des attentes",
    2: "En-deçà des attentes",
    3: "Conforme aux attentes du poste",
    4: "Supérieur aux attentes",
    5: "Nettement supérieur / exceptionnel",
}

# Couleurs : sobres et imprimables en noir et blanc sans perte.
if _REPORTLAB_AVAILABLE:
    _INK = colors.HexColor("#1a1a1a")
    _INK_SOFT = colors.HexColor("#5a5a5a")
    _ACCENT = colors.HexColor("#6B4AAF")  # violet ARHIANE
    _BG_SOFT = colors.HexColor("#f5f5f5")
    _LINE = colors.HexColor("#d0d0d0")


@dataclass
class Critere:
    """Un critère à évaluer par le manager."""

    id: str
    label: str
    applicable: bool = True
    aide: str = ""


@dataclass
class QuestionnaireContext:
    """Tout ce qu'il faut pour générer le PDF."""

    employeur_nom: str
    employeur_adresse: str = ""
    employeur_email_rh: str = ""
    collaborateur_nom: str = ""
    collaborateur_prenom: str = ""
    fonction: str = ""
    periode_debut: str = ""     # JJ.MM.AAAA
    periode_fin: str = ""       # JJ.MM.AAAA (ou "en cours")
    manager_nom: str = ""        # pré-rempli si connu
    criteres: list[Critere] = field(default_factory=list)
    langue: str = "fr"
    date_generation: str = field(
        default_factory=lambda: datetime.now().strftime("%d.%m.%Y")
    )
    # Personnalisation visuelle (Paramètres globaux + entité)
    couleur_primaire: str = "#6B4AAF"     # hex #RRGGBB — bandeau et accents PDF
    logo_path: str | None = None           # chemin absolu du logo à placer en en-tête


class QuestionnaireEngine:
    """Générateur de PDF questionnaire manager."""

    def __init__(self):
        if not _REPORTLAB_AVAILABLE:
            # On diffère l'erreur jusqu'à l'appel de generate_pdf pour
            # permettre au socle de charger sans reportlab.
            pass

    @staticmethod
    def is_available() -> bool:
        return _REPORTLAB_AVAILABLE

    def generate_pdf(self, ctx: QuestionnaireContext, output: Path) -> Path:
        """Écrit le PDF à l'emplacement `output` et retourne ce chemin."""
        if not _REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "reportlab n'est pas installé. Installez-le avec "
                "`pip install reportlab==4.2.2`."
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        # Résolution de la couleur d'accent custom
        try:
            self._accent = colors.HexColor(ctx.couleur_primaire or "#6B4AAF")
        except Exception:
            self._accent = _ACCENT
        c = canvas.Canvas(str(output), pagesize=A4)
        c.setTitle(f"Questionnaire manager — {ctx.collaborateur_prenom} {ctx.collaborateur_nom}")
        c.setAuthor(ctx.employeur_nom)
        c.setSubject("Certificat de travail — collecte d'évaluation managériale")

        # Formulaire AcroForm — unique par document.
        form = c.acroForm

        self._page_intro(c, ctx)
        c.showPage()
        self._page_identification(c, ctx, form)
        c.showPage()
        self._pages_criteres(c, ctx, form)
        c.showPage()
        self._page_synthese(c, ctx, form)

        c.save()
        return output

    # ----------------------------------------------------------------
    # Pages
    # ----------------------------------------------------------------

    def _page_intro(self, c: "canvas.Canvas", ctx: QuestionnaireContext) -> None:
        """Page 1 : objet, spécificité suisse, échelle, exemples, confidentialité."""
        w, h = A4
        margin = 20 * mm
        y = h - margin

        # Bandeau titre
        c.setFillColor(getattr(self, "_accent", _ACCENT))
        c.rect(0, h - 18 * mm, w, 18 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, h - 12 * mm, "QUESTIONNAIRE D'ÉVALUATION MANAGÉRIALE")
        c.setFont("Helvetica", 9)
        c.drawString(margin, h - 16 * mm,
                     f"Destiné à la rédaction du certificat de travail • {ctx.employeur_nom}")

        # Logo (en bas à droite de la page 1 — optionnel, fourni par l'entité)
        if ctx.logo_path:
            try:
                from pathlib import Path as _Path
                p = _Path(ctx.logo_path)
                if p.is_file():
                    # 35mm max en largeur/hauteur — s'adapte proportionnellement.
                    c.drawImage(str(p),
                                x=w - margin - 35 * mm,
                                y=margin + 10 * mm,
                                width=35 * mm, height=20 * mm,
                                preserveAspectRatio=True, anchor="se", mask="auto")
            except Exception as exc:  # noqa: BLE001
                # On ne fait pas échouer la génération pour un logo problématique.
                pass

        y = h - 24 * mm
        c.setFillColor(_INK)

        def section(title: str, body: list[str]) -> float:
            nonlocal y
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin, y, title)
            y -= 5 * mm
            c.setFont("Helvetica", 9.5)
            c.setFillColor(_INK_SOFT)
            for line in body:
                c.drawString(margin, y, line)
                y -= 4.3 * mm
            c.setFillColor(_INK)
            y -= 3 * mm
            return y

        section("Objet du document", [
            "Votre évaluation servira à rédiger le certificat de travail de "
            f"{ctx.collaborateur_prenom} {ctx.collaborateur_nom}.",
            "Merci d'y répondre avec soin — vos retours seront la base de la rédaction finale.",
        ])

        section("Spécificité suisse du certificat de travail", [
            "En Suisse, le certificat est une pièce centrale du dossier de candidature,",
            "conservée tout au long de la carrière (art. 330a CO).",
            "Chaque mot y est lu par les recruteurs — précision et honnêteté priment.",
        ])

        section("Échelle de notation (5 étoiles + N/A)", [
            "★       1 — Nettement en-deçà des attentes",
            "★★     2 — En-deçà des attentes",
            "★★★   3 — Conforme aux attentes du poste",
            "★★★★ 4 — Supérieur aux attentes",
            "★★★★★ 5 — Nettement supérieur / exceptionnel",
            "N/A    — Critère non applicable (ex. pas de contact client, pas d'équipe à encadrer)",
            "",
            "⚠  Attention : dans le langage implicite du certificat suisse, une note de 3/5 est lue",
            "comme « moyen / perfectible » par les recruteurs. Positionnez-vous en connaissance de cause.",
        ])

        section("Importance des exemples concrets", [
            "Pour chaque critère, merci d'illustrer votre note par 2-3 lignes factuelles",
            "(un dossier, un projet, une situation vécue). Ces exemples nourrissent la rédaction",
            "et rendent le certificat crédible.",
        ])

        section("Temps indicatif", [
            "15 à 25 minutes. Vous pouvez sauvegarder et reprendre plus tard.",
        ])

        section("Pour toute question", [
            ctx.employeur_email_rh or "— contactez votre RH interne —",
        ])

        # Pied confidentialité
        self._footer_confidentialite(c, ctx)

    def _page_identification(self, c: "canvas.Canvas", ctx: QuestionnaireContext,
                              form: Any) -> None:
        """Page 2 : identification manager + rappel période."""
        w, h = A4
        margin = 20 * mm
        y = h - 25 * mm

        self._page_header(c, "IDENTIFICATION")

        c.setFillColor(_INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Collaborateur-rice évalué-e")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        self._kv(c, margin, y, "Nom et prénom",
                 f"{ctx.collaborateur_prenom} {ctx.collaborateur_nom}".strip())
        y -= 5 * mm
        self._kv(c, margin, y, "Fonction", ctx.fonction or "—")
        y -= 5 * mm

        periode = ctx.periode_debut or "—"
        if ctx.periode_fin:
            periode = f"{ctx.periode_debut or '—'}  →  {ctx.periode_fin}"
        else:
            periode = f"{ctx.periode_debut or '—'}  →  en cours"
        self._kv(c, margin, y, "Période couverte", periode)

        # Explicit reminder if manager manages only part of the period (§15.7)
        y -= 10 * mm
        c.setFillColor(_BG_SOFT)
        c.rect(margin, y - 10 * mm, w - 2 * margin, 12 * mm, stroke=0, fill=1)
        c.setFillColor(_INK)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(margin + 4 * mm, y - 2 * mm,
                     "Vos réponses concernent UNIQUEMENT la période durant laquelle vous avez")
        c.drawString(margin + 4 * mm, y - 6 * mm,
                     "managé directement cette personne. En cas de doute, précisez-le dans les commentaires.")
        y -= 20 * mm

        # Champs manager (AcroForm)
        c.setFillColor(_INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Vous")
        y -= 6 * mm

        self._text_field(c, form, margin, y,
                          name="manager_nom",
                          label="Votre nom et prénom",
                          value=ctx.manager_nom,
                          width=w - 2 * margin - 5 * mm, height=8 * mm)
        y -= 14 * mm
        self._text_field(c, form, margin, y,
                          name="manager_fonction",
                          label="Votre fonction",
                          width=w - 2 * margin - 5 * mm, height=8 * mm)
        y -= 14 * mm
        self._text_field(c, form, margin, y,
                          name="manager_periode_reelle",
                          label="Période durant laquelle vous avez effectivement managé cette personne",
                          width=w - 2 * margin - 5 * mm, height=8 * mm)
        y -= 14 * mm
        self._text_field(c, form, margin, y,
                          name="manager_date_retour",
                          label="Date de retour du questionnaire (JJ.MM.AAAA)",
                          width=70 * mm, height=8 * mm)

        self._footer_confidentialite(c, ctx)

    def _pages_criteres(self, c: "canvas.Canvas", ctx: QuestionnaireContext,
                         form: Any) -> None:
        """Pages 3+ : une par groupe de critères."""
        w, h = A4
        margin = 20 * mm
        self._page_header(c, "ÉVALUATION PAR CRITÈRE")

        y = h - 30 * mm
        c.setFillColor(_INK)
        c.setFont("Helvetica", 9)
        c.drawString(margin, y,
                     "Pour chaque critère : cochez une note de 1 à 5, puis illustrez par un exemple concret.")
        y -= 8 * mm

        for crit in ctx.criteres:
            if not crit.applicable:
                continue
            # Nouvelle page si on approche le bas
            if y < 80 * mm:
                self._footer_confidentialite(c, ctx)
                c.showPage()
                self._page_header(c, "ÉVALUATION PAR CRITÈRE (suite)")
                y = h - 30 * mm
            y = self._block_critere(c, form, crit, margin, y, w - 2 * margin)

        self._footer_confidentialite(c, ctx)

    def _page_synthese(self, c: "canvas.Canvas", ctx: QuestionnaireContext,
                       form: Any) -> None:
        """Dernière page : note globale + commentaire libre + contexte départ."""
        w, h = A4
        margin = 20 * mm
        self._page_header(c, "SYNTHÈSE")
        y = h - 30 * mm

        # Appréciation globale
        c.setFillColor(_INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Appréciation globale")
        y -= 5 * mm
        c.setFont("Helvetica", 9)
        c.setFillColor(_INK_SOFT)
        c.drawString(margin, y,
                     "Votre note de synthèse pour l'ensemble de la collaboration.")
        y -= 7 * mm
        c.setFillColor(_INK)
        y = self._stars_row(c, form, name="global_niveau", x=margin, y=y, include_na=False)
        y -= 4 * mm

        # Commentaire libre
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Commentaire de synthèse (3-4 lignes)")
        y -= 6 * mm
        self._textarea_field(c, form, margin, y,
                              name="global_commentaire",
                              width=w - 2 * margin, height=28 * mm)
        y -= 32 * mm

        # Contexte départ (§15.6)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Contexte de départ (pour certificat final)")
        y -= 6 * mm
        self._text_field(c, form, margin, y,
                          name="contexte_initiative",
                          label="Initiative du départ (tel que vous la comprenez)",
                          width=w - 2 * margin, height=8 * mm)
        y -= 14 * mm

        self._checkbox_field(c, form, margin, y,
                              name="recommanderait",
                              label="Recommanderiez-vous cette personne à un-e collègue manager ?")
        y -= 10 * mm

        self._text_field(c, form, margin, y,
                          name="reserves",
                          label="Réserves particulières à signaler au RH (confidentielles)",
                          width=w - 2 * margin, height=8 * mm)

        self._footer_confidentialite(c, ctx)

    # ----------------------------------------------------------------
    # Primitives de layout
    # ----------------------------------------------------------------

    def _page_header(self, c: "canvas.Canvas", title: str) -> None:
        w, h = A4
        c.setFillColor(getattr(self, "_accent", _ACCENT))
        c.rect(0, h - 12 * mm, w, 12 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, h - 8 * mm, title)

    def _footer_confidentialite(self, c: "canvas.Canvas",
                                 ctx: QuestionnaireContext) -> None:
        w, _ = A4
        c.setFillColor(_INK_SOFT)
        c.setFont("Helvetica-Oblique", 7.5)
        msg = (
            f"Document confidentiel — destiné uniquement au service RH de "
            f"{ctx.employeur_nom}. À supprimer après usage. "
            f"Généré le {ctx.date_generation}."
        )
        c.drawCentredString(w / 2, 8 * mm, msg)

    def _kv(self, c: "canvas.Canvas", x: float, y: float,
             label: str, value: str) -> None:
        c.setFont("Helvetica", 10)
        c.setFillColor(_INK_SOFT)
        c.drawString(x, y, f"{label} :")
        c.setFillColor(_INK)
        c.drawString(x + 45 * mm, y, value or "—")

    def _text_field(self, c, form, x, y, *, name, label, value="",
                     width=120 * mm, height=8 * mm) -> None:
        c.setFont("Helvetica", 9)
        c.setFillColor(_INK_SOFT)
        c.drawString(x, y + height + 1 * mm, label)
        c.setFillColor(_INK)
        form.textfield(
            name=name, tooltip=label,
            x=x, y=y, width=width, height=height,
            value=value,
            borderStyle="inset", borderWidth=0.5,
            fillColor=colors.white,
            textColor=_INK,
            fontSize=10,
            forceBorder=True,
        )

    def _textarea_field(self, c, form, x, y, *, name, width, height) -> None:
        form.textfield(
            name=name, tooltip=name,
            x=x, y=y - height, width=width, height=height,
            value="",
            fieldFlags="multiline",
            borderStyle="inset", borderWidth=0.5,
            fillColor=colors.white,
            textColor=_INK,
            fontSize=10,
            forceBorder=True,
        )

    def _checkbox_field(self, c, form, x, y, *, name, label) -> None:
        form.checkbox(
            name=name, tooltip=label,
            x=x, y=y - 4 * mm, size=5 * mm,
            checked=False,
            buttonStyle="check",
            borderStyle="solid", borderWidth=0.5,
            fillColor=colors.white,
            forceBorder=True,
        )
        c.setFont("Helvetica", 10)
        c.setFillColor(_INK)
        c.drawString(x + 8 * mm, y - 2.5 * mm, label)

    def _block_critere(self, c, form, crit: Critere, x: float, y: float,
                        width: float) -> float:
        """Un bloc : label, étoiles (+ N/A), champ exemple. Retourne le nouveau y."""
        c.setFillColor(_INK)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x, y, crit.label)
        y -= 4.5 * mm

        if crit.aide:
            c.setFont("Helvetica-Oblique", 8.5)
            c.setFillColor(_INK_SOFT)
            c.drawString(x, y, crit.aide)
            y -= 4 * mm

        # Ligne d'étoiles + N/A
        y = self._stars_row(c, form, name=f"crit_{crit.id}_niveau", x=x, y=y)
        y -= 3 * mm

        # Exemple concret
        c.setFont("Helvetica", 9)
        c.setFillColor(_INK_SOFT)
        c.drawString(x, y, "Exemple concret (2-3 lignes) :")
        y -= 2 * mm
        self._textarea_field(c, form, x, y,
                              name=f"crit_{crit.id}_exemple",
                              width=width, height=18 * mm)
        y -= 22 * mm

        # Séparateur discret
        c.setStrokeColor(_LINE)
        c.setLineWidth(0.3)
        c.line(x, y, x + width, y)
        y -= 6 * mm
        return y

    def _stars_row(self, c, form, *, name: str, x: float, y: float,
                    include_na: bool = True) -> float:
        """Ligne 5 étoiles (+ N/A) alignées sur une unique baseline.

        Pas de libellés détaillés sous chaque étoile : la légende est déjà
        affichée en page 1 (§15.4 spec). La colonne « N/A » permet à un
        manager de marquer explicitement qu'un critère ne s'applique pas
        (ex. : pas de contact client, pas d'équipe à encadrer).
        """
        options: list[tuple[str, str]] = [
            ("1", "1 ★"), ("2", "2 ★"), ("3", "3 ★"),
            ("4", "4 ★"), ("5", "5 ★"),
        ]
        if include_na:
            options.append(("na", "N/A"))

        n = len(options)
        radio_size = 4 * mm
        # Largeur de colonne : cercle + gap + label (« 1 ★ » ~ 9 mm).
        col_width = 27 * mm
        # Base commune pour tous les cercles — évite toute dérive verticale.
        radio_y = y - radio_size - 1 * mm
        # La baseline du texte, placée ~1/3 de la hauteur du cercle pour
        # tomber visuellement au centre du cercle (la baseline est sous
        # le caractère, la hauteur de la capitale est ~70 % du cadre).
        text_y = radio_y + 1.2 * mm

        for i, (value, label) in enumerate(options):
            cx = x + i * col_width
            form.radio(
                name=name, tooltip=f"Niveau {value}",
                value=value, selected=False,
                x=cx, y=radio_y, size=radio_size,
                buttonStyle="check",
                borderStyle="solid", borderWidth=0.6,
                fillColor=colors.white,
                forceBorder=False,
            )
            c.setFont("Helvetica-Bold", 9.5)
            c.setFillColor(_INK if value != "na" else _INK_SOFT)
            c.drawString(cx + radio_size + 2 * mm, text_y, label)
        return radio_y - 3 * mm


# Mapping des critères standard (aligné avec generator.py des certificats).
STANDARD_CRITERES_FR: list[Critere] = [
    Critere("qualite_travail", "Qualité du travail"),
    Critere("quantite_travail", "Quantité / productivité"),
    Critere("competences_techniques", "Compétences techniques / professionnelles"),
    Critere("fiabilite_autonomie", "Fiabilité / autonomie"),
    Critere("comportement_hierarchie", "Comportement envers la hiérarchie"),
    Critere("comportement_collegues", "Comportement envers les collègues"),
    Critere("comportement_subordonnes", "Comportement envers les subordonné·es",
             applicable=True,
             aide="Cochez N/A si la personne n'encadre pas d'équipe."),
    Critere("comportement_clients", "Comportement envers les clients / partenaires externes",
             applicable=True,
             aide="Cochez N/A si la fonction n'implique pas de relation externe."),
]
