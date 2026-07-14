#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["playwright"]
# ///
"""Régénère docs/statusline.png à partir de statusline-command.sh.

Fait tourner le script avec un JSON d'exemple, convertit sa sortie ANSI en
HTML (police + couleurs), la fait rendre par le Chromium géré par Playwright,
puis capture directement l'élément — sans recadrage ni fichier temporaire.

Prérequis : une police Nerd Font pour le séparateur powerline et une police
d'emoji couleur (ex. Noto Color Emoji) pour les icônes des segments. Le
navigateur Chromium est géré par Playwright et téléchargé automatiquement à la
première exécution (ou via `playwright install chromium`). Les dépendances
Python sont gérées par `uv run`.

Usage : ./docs/generate-screenshot.py [--json '<json custom>']
     ou : uv run docs/generate-screenshot.py [--json '<json custom>']
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import Error, sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUSLINE_SCRIPT = REPO_ROOT / "statusline-command.sh"
OUTPUT_PATH = REPO_ROOT / "docs" / "statusline.png"

# Chemin d'exemple ancré sur le HOME réel de l'exécutant : statusline le
# raccourcit alors toujours en « ~/D/claude-statusline », quel que soit
# l'utilisateur qui régénère la capture.
EXAMPLE_DIR = str(Path.home() / "Documents" / "claude-statusline")
DEFAULT_JSON = json.dumps(
    {
        "workspace": {"current_dir": EXAMPLE_DIR},
        "model": {"display_name": "Opus"},
        "context_window": {"used_percentage": 42},
        "cost": {"total_cost_usd": 1.23, "total_duration_ms": 65000},
        "effort": {"level": "high"},
    }
)

FONT_FAMILY = "UbuntuMono Nerd Font"
FONT_SIZE_PX = 28
BG_COLOR = "#1e1e1e"
PADDING_PX = 12
DEVICE_SCALE_FACTOR = 2  # capture nette sur écran haute densité


def ansi256_to_rgb(n: int) -> tuple[int, int, int]:
    if n < 16:
        basic = [
            (0, 0, 0),
            (205, 0, 0),
            (0, 205, 0),
            (205, 205, 0),
            (0, 0, 238),
            (205, 0, 205),
            (0, 205, 205),
            (229, 229, 229),
            (127, 127, 127),
            (255, 0, 0),
            (0, 255, 0),
            (255, 255, 0),
            (92, 92, 255),
            (255, 0, 255),
            (0, 255, 255),
            (255, 255, 255),
        ]
        return basic[n]
    if n <= 231:
        n -= 16
        levels = [0, 95, 135, 175, 215, 255]
        return (levels[n // 36], levels[(n % 36) // 6], levels[n % 6])
    gray = 8 + (n - 232) * 10
    return (gray, gray, gray)


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")


def ansi_to_html(raw: str) -> str:
    out = [
        f"<span style=\"font-family: '{FONT_FAMILY}', monospace; "
        f'font-size: {FONT_SIZE_PX}px; white-space: pre; line-height: 1.4;">'
    ]
    fg = bg = None
    bold = False
    span_open = False

    def close_span():
        nonlocal span_open
        if span_open:
            out.append("</span>")
            span_open = False

    def open_span():
        nonlocal span_open
        style = []
        if bg:
            style.append(f"background-color:{rgb_hex(bg)}")
        if fg:
            style.append(f"color:{rgb_hex(fg)}")
        if bold:
            style.append("font-weight:bold")
        out.append(f'<span style="{";".join(style)}">')
        span_open = True

    pos = 0
    for m in ANSI_RE.finditer(raw):
        text = raw[pos : m.start()]
        if text:
            if not span_open:
                open_span()
            out.append(html.escape(text))
        codes = m.group(1).split(";") if m.group(1) else ["0"]
        j = 0
        while j < len(codes):
            c = codes[j]
            if c in ("", "0"):
                fg = bg = None
                bold = False
            elif c == "1":
                bold = True
            elif c == "38" and j + 2 < len(codes) and codes[j + 1] == "5":
                fg = ansi256_to_rgb(int(codes[j + 2]))
                j += 2
            elif c == "48" and j + 2 < len(codes) and codes[j + 1] == "5":
                bg = ansi256_to_rgb(int(codes[j + 2]))
                j += 2
            j += 1
        # Toute séquence SGR reconnue clôt le span courant ; le prochain
        # texte le rouvrira avec le style mis à jour.
        close_span()
        pos = m.end()
    tail = raw[pos:]
    if tail:
        if not span_open:
            open_span()
        out.append(html.escape(tail))
    close_span()
    out.append("</span>")
    return "".join(out)


def build_html(body: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; }}
  .wrap {{ display: inline-block; padding: {PADDING_PX}px; background: {BG_COLOR}; }}
</style></head>
<body><div class="wrap">{body}</div></body></html>
"""


def run_or_die(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Exécute `cmd` en capturant sa sortie ; en cas d'échec, affiche son stderr et sort."""
    proc = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if proc.returncode != 0:
        sys.exit(
            f"« {cmd[0]} » a échoué (code {proc.returncode}) :\n{proc.stderr.strip()}"
        )
    return proc


def launch_chromium(playwright):
    """Lance Chromium, en le téléchargeant à la première exécution si nécessaire."""
    try:
        return playwright.chromium.launch()
    except Error as exc:
        if "Executable doesn't exist" not in str(exc):
            raise
        print(
            "Chromium pour Playwright absent — téléchargement (première exécution)…",
            file=sys.stderr,
        )
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"], check=True
        )
        return playwright.chromium.launch()


def render_png(html_doc: str, output_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        page = browser.new_page(device_scale_factor=DEVICE_SCALE_FACTOR)
        page.set_content(html_doc, wait_until="load")
        # Attendre le chargement des polices (glyphes Nerd Font et emoji) avant
        # la capture, sinon on risque un rendu de secours.
        page.evaluate("async () => { await document.fonts.ready; }")
        page.locator(".wrap").screenshot(path=str(output_path))
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", default=DEFAULT_JSON, help="JSON envoyé à statusline-command.sh"
    )
    parser.add_argument(
        "--output", default=str(OUTPUT_PATH), help="Chemin du PNG généré"
    )
    args = parser.parse_args()

    raw = run_or_die(["bash", str(STATUSLINE_SCRIPT)], input=args.json).stdout
    html_doc = build_html(ansi_to_html(raw))
    output_path = Path(args.output).resolve()
    render_png(html_doc, output_path)
    print(f"Capture générée : {output_path}")


if __name__ == "__main__":
    main()
