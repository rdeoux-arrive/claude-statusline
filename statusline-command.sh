#!/bin/bash
# Claude Code status line — powerline style

IFS=$'\t' read -r cwd model used cost duration_ms effort < <(
    jq -r '[
        .workspace.current_dir // .cwd,
        (.model.display_name // "Claude"),
        (.context_window.used_percentage // 0),
        (.cost.total_cost_usd // 0),
        (.cost.total_duration_ms // 0),
        (.effort.level // empty)
    ] | @tsv'
)

# Raccourcir le chemin : première lettre de chaque composant intermédiaire
short_cwd="${cwd/#$HOME/\~}"
if [[ "$short_cwd" == */* ]]; then
    IFS='/' read -ra parts <<< "$short_cwd"
    last_idx=$(( ${#parts[@]} - 1 ))
    shortened="${parts[0]}"
    for i in "${!parts[@]}"; do
        [ $i -eq 0 ] && continue
        part="${parts[$i]}"
        [ -z "$part" ] && continue
        if (( i < last_idx )); then shortened+="/${part:0:1}"
        else                        shortened+="/$part"
        fi
    done
    short_cwd="$shortened"
fi

R_SOLID=$(printf '\xee\x82\xb0')   # U+E0B0
I_DIR='📂' ; I_GIT='🌿' ; I_MODEL='🧠' ; I_CTX='💾' ; I_COST='💰' ; I_DUR='⏱️'

fg()   { printf '\033[38;5;%sm' "$1"; }
bg()   { printf '\033[48;5;%sm' "$1"; }
bold() { printf '\033[1m'; }
rst()  { printf '\033[0m'; }

export GIT_OPTIONAL_LOCKS=0
git_branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -n "$git_branch" ] && git_dirty=$(git -C "$cwd" status --porcelain 2>/dev/null)

C_DIR_BG=88 ; C_MODEL_BG=130 ; C_CTX_BG=136 ; C_COST_BG=28 ; C_DUR_BG=25 ; C_GIT_BG=54

seg_bgs=()
seg_texts=()

add_seg() {
    seg_bgs+=("$1")
    seg_texts+=("$(bg "$1")$(fg "$2")$(bold) $3 $(rst)")
}

add_seg $C_DIR_BG 231 "${I_DIR} ${short_cwd}"

if [ -n "$model" ]; then
    case "$effort" in
        low)       model="${model} ○" ;;
        medium)    model="${model} ◐" ;;
        high)      model="${model} ●" ;;
        xhigh)     model="${model} ◉" ;;
        max)       model="${model} ◈" ;;
        ultracode) model="${model} ✦" ;;
    esac
    add_seg $C_MODEL_BG 231 "${I_MODEL} ${model}"
fi

if [ -n "$used" ]; then
    LC_ALL=C printf -v ctx "%.0f" "$used"
    for (( i=1; i<=10; i++ )); do
        (( i <= ctx * 10 / 100 )) && bar+="█" || bar+="░"
    done
    add_seg $C_CTX_BG 231 "${I_CTX} ${bar} ${ctx}%"
fi

if [ -n "$cost" ]; then
    cost_fmt=$(LC_ALL=C printf '%.2f' "$cost")
    add_seg $C_COST_BG 231 "${I_COST} \$${cost_fmt}"
fi

if [ -n "$duration_ms" ]; then
    total_s=$(( duration_ms / 1000 ))
    h=$(( total_s / 3600 ))
    m=$(( (total_s % 3600) / 60 ))
    s=$(( total_s % 60 ))
    if   (( h > 0 )); then dur_fmt="${h}h${m}m"
    elif (( m > 0 )); then dur_fmt="${m}m${s}s"
    else                   dur_fmt="${s}s"
    fi
    add_seg $C_DUR_BG 231 "${I_DUR} ${dur_fmt}"
fi

if [ -n "$git_branch" ]; then
    [ -n "$git_dirty" ] && dirty="🚧 " || dirty=""
    add_seg $C_GIT_BG 231 "${I_GIT} ${git_branch} ${dirty}"
fi

n=${#seg_bgs[@]}
out=""
for (( i=0; i<n; i++ )); do
    out+="${seg_texts[$i]}"
    (( i+1 < n )) && out+="$(bg ${seg_bgs[$((i+1))]})$(fg ${seg_bgs[$i]})${R_SOLID}$(rst)"
done
out+="$(fg ${seg_bgs[$((n-1))]})${R_SOLID}$(rst)"

printf "%s\n" "$out"
