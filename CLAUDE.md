# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Vue d'ensemble

Projet à fichier unique : `statusline-command.sh`, un script Bash qui génère une barre de status **powerline** pour Claude Code. Claude Code invoque le script en lui passant sur stdin un objet JSON décrivant la session ; le script écrit sur stdout une ligne unique de segments ANSI colorés.

## Tester le script

Pas de build ni de framework de test. Le script se valide en lui injectant un JSON factice sur stdin :

```bash
echo '{"workspace":{"current_dir":"/home/u/p"},"model":{"display_name":"Opus"},"context_window":{"used_percentage":42},"cost":{"total_cost_usd":1.23,"total_duration_ms":65000},"effort":{"level":"high"}}' \
  | bash statusline-command.sh
```

Les champs sont tous optionnels côté script (valeurs par défaut via `// ` dans le filtre `jq`) : retirer une clé du JSON permet de tester le comportement quand Claude Code ne la fournit pas.

## Architecture du rendu

Le flux suit toujours le même pipeline, dans cet ordre :

1. **Extraction** — un seul appel `jq ... | @tsv` parse les 6 champs en variables Bash (l.4-13). Ajouter une donnée = l'ajouter au filtre `jq` ET à la liste `IFS=$'\t' read`.
2. **Accumulation** — chaque segment est poussé via `add_seg <bg> <fg> <texte>` dans les tableaux parallèles `seg_bgs` / `seg_texts` (l.45-51). L'ordre des appels `add_seg` = l'ordre d'affichage.
3. **Chaînage powerline** — la boucle finale (l.87-95) recolle les segments en insérant le séparateur solide `U+E0B0`, dont la **couleur de premier plan = la couleur de fond du segment précédent** et le fond = celle du suivant. C'est ce qui crée l'effet de chevrons enchaînés.

Conventions :
- Couleurs = codes ANSI 256, déclarées groupées en `C_*_BG` juste avant l'accumulation.
- Icônes = emoji en `I_*`, déclarées groupées (l.32).
- Le formatage numérique utilise `LC_ALL=C printf` pour forcer le point décimal indépendamment de la locale.
- `GIT_OPTIONAL_LOCKS=0` + `git -C "$cwd"` : interroge le dépôt du répertoire courant sans poser de lock.

## Régénérer la capture d'écran d'exemple

`docs/generate-screenshot.py` régénère `docs/statusline.png` depuis `statusline-command.sh` : rendu ANSI → HTML (police + couleurs), rendu par le Chromium de Playwright, capture directe de l'élément (sans recadrage ni fichier temporaire).

```bash
uv run docs/generate-screenshot.py
```

Prérequis : [`uv`](https://docs.astral.sh/uv/) (installe seul la dépendance Playwright via les métadonnées PEP 723 du script), une police Nerd Font (séparateur powerline) et une police d'emoji couleur (ex. Noto Color Emoji, pour les icônes des segments). Le navigateur Chromium est géré par Playwright : il est téléchargé automatiquement à la première exécution (~/.cache/ms-playwright), ou manuellement via `playwright install chromium`. Aucune dépendance système à un navigateur (le Chromium de Playwright n'est pas un snap), donc pas de contrainte de confinement sur les chemins.

Vérifier le script (lint + types) : `ruff check docs` passe tel quel, mais `ty check` seul échoue sur `playwright` (dépendance de l'env éphémère `uv`, absente du Python système). Type-checker le script avec ses dépendances installées :

```bash
uvx --with-requirements docs/generate-screenshot.py ty check docs/generate-screenshot.py
```
