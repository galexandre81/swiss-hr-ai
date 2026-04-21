"""Point d'entrée UI : crée la fenêtre PyWebView et branche l'API Python."""

from __future__ import annotations

from pathlib import Path

import webview

from _app.core import get_config, get_logger
from _app.ui.api import Api


WINDOW_TITLE = "Swiss HR Local AI Toolbox"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
MIN_WIDTH = 1024
MIN_HEIGHT = 680


def _web_root() -> Path:
    return Path(__file__).resolve().parent / "web"


def launch() -> None:
    cfg = get_config()
    log = get_logger()
    log.info(f"Démarrage UI — racine projet : {cfg.root}")

    api = Api()
    index_html = _web_root() / "index.html"
    if not index_html.exists():
        raise FileNotFoundError(f"Fichier UI introuvable : {index_html}")

    webview.create_window(
        title=WINDOW_TITLE,
        url=str(index_html),
        js_api=api,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        text_select=True,
        confirm_close=False,
    )
    # debug=False en prod — évite les DevTools chez l'utilisateur final.
    webview.start(debug=False)


if __name__ == "__main__":
    launch()
