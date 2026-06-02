#!/bin/bash
# Installe le statusline powerline pour Claude Code.
# Clone (ou met à jour) le dépôt dans ~/.claude/claude-statusline,
# puis déclare la clé statusLine dans ~/.claude/settings.json.
#
# Usage : curl -fsSL <raw>/install.sh | bash
#     ou : ./install.sh (depuis un clone local)

set -euo pipefail

REPO_URL="https://github.com/rdeoux-arrive/claude-statusline.git"
CLAUDE_DIR="$HOME/.claude"
INSTALL_DIR="$CLAUDE_DIR/claude-statusline"
SETTINGS="$CLAUDE_DIR/settings.json"
SCRIPT_CMD="bash \$HOME/.claude/claude-statusline/statusline-command.sh"

# 1. Prérequis
for tool in git jq; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Erreur : '$tool' est requis mais introuvable. Installe-le puis relance." >&2
        exit 1
    fi
done

# 2. Clone ou mise à jour
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "📥 Mise à jour de $INSTALL_DIR…"
    git -C "$INSTALL_DIR" pull --ff-only
else
    echo "📥 Clonage dans $INSTALL_DIR…"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 3. settings.json
mkdir -p "$CLAUDE_DIR"
if [ ! -f "$SETTINGS" ]; then
    echo "{}" > "$SETTINGS"
    echo "🆕 $SETTINGS créé."
else
    cp "$SETTINGS" "$SETTINGS.bak"
    echo "💾 Sauvegarde : $SETTINGS.bak"
fi

tmp=$(mktemp)
jq --arg cmd "$SCRIPT_CMD" \
    '.statusLine = {type: "command", command: $cmd}' \
    "$SETTINGS" > "$tmp"
mv "$tmp" "$SETTINGS"

# 4. Résumé
echo
echo "✅ statusLine déclaré dans $SETTINGS"
echo "   command = $SCRIPT_CMD"
echo "👉 Relance Claude Code pour voir la barre de status."
