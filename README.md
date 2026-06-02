# claude-statusline

Une barre de status **powerline** pour [Claude Code](https://claude.com/claude-code).

Elle affiche, sous forme de segments colorés enchaînés :

| Segment | Contenu |
|---------|---------|
| 📂 | Répertoire courant, chemin raccourci (1ʳᵉ lettre des composants intermédiaires) |
| 🧠 | Modèle actif |
| 💾 | Utilisation du contexte (barre `████░░░░░░` + pourcentage) |
| 💰 | Coût total de la session (USD) |
| ⏱️ | Durée totale de la session |
| 🌿 | Branche git (+ 🚧 si l'arbre de travail est sale) |

## Prérequis

- [`jq`](https://jqlang.github.io/jq/) — parsing du JSON fourni par Claude Code
- `git` — pour le segment de branche
- Une **police powerline** (Nerd Font ou patchée) dans ton terminal, pour le caractère séparateur ``  (`U+E0B0`)

## Installation

### Script automatique (recommandé)

```bash
curl -fsSL https://raw.githubusercontent.com/rdeoux-arrive/claude-statusline/main/install.sh | bash
```

Le script :

- clone (ou met à jour) le dépôt dans `~/.claude/claude-statusline` ;
- déclare la clé `statusLine` dans `~/.claude/settings.json` (en sauvegardant l'ancien fichier en `.bak`, en préservant les autres clés).

Il est idempotent : relance-le pour mettre à jour le statusline. Relance ensuite Claude Code.

### Installation manuelle

1. Récupère le script :

   ```bash
   curl -fsSL https://raw.githubusercontent.com/rdeoux-arrive/claude-statusline/main/statusline-command.sh \
     -o ~/.claude/statusline-command.sh
   ```

2. Déclare-le dans `~/.claude/settings.json` :

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "bash /home/<user>/.claude/statusline-command.sh"
     }
   }
   ```

3. Relance Claude Code.

## Personnalisation

Les couleurs des segments (codes ANSI 256) sont définies en tête de section, faciles à ajuster :

```bash
C_DIR_BG=88 ; C_MODEL_BG=130 ; C_CTX_BG=136 ; C_COST_BG=28 ; C_DUR_BG=25 ; C_GIT_BG=54
```

Les icônes se trouvent juste au-dessus :

```bash
I_DIR='📂' ; I_GIT='🌿' ; I_MODEL='🧠' ; I_CTX='💾' ; I_COST='💰' ; I_DUR='⏱️'
```

## Licence

MIT
