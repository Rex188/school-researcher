#!/usr/bin/env bash
#
# School-Researcher 安装脚本
#
# 用法:
#   ./install.sh                          # 安装为 Claude Code Skill（默认）
#   ./install.sh --platform gemini        # 安装到当前工作区的 Antigravity/Gemini 目录
#   ./install.sh --target /path/to/skill  # 自定义安装位置
#   ./install.sh --uninstall              # 卸载
#
# 不指定 --target 时的默认位置:
#   claude → ~/.claude/skills/school-researcher
#   gemini → ./.agent/skills/school-researcher

set -euo pipefail

REPO_NAME="school-researcher"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 安装内容（刻意排除 .git 与 examples/，后者不是 Skill 运行所需）
ITEMS=(SKILL.md scripts references templates agent_rules README.md LICENSE)

usage() {
    sed -n '3,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

PLATFORM="claude"
TARGET=""
DO_UNINSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform) PLATFORM="${2:-}"; shift 2 ;;
        --target)   TARGET="${2:-}";   shift 2 ;;
        --uninstall) DO_UNINSTALL=1;   shift ;;
        -h|--help)  usage; exit 0 ;;
        *) echo "未知参数: $1" >&2; echo; usage >&2; exit 1 ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    case "$PLATFORM" in
        claude) TARGET="$HOME/.claude/skills/$REPO_NAME" ;;
        gemini) TARGET="$PWD/.agent/skills/$REPO_NAME" ;;
        *) echo "错误：未知平台 '$PLATFORM'。请用 --target 显式指定目录。" >&2; exit 1 ;;
    esac
fi

# ---------------------------------------------------------------- 卸载
if [[ "$DO_UNINSTALL" == "1" ]]; then
    if [[ ! -d "$TARGET" ]]; then
        echo "目录不存在，无需卸载: $TARGET"
        exit 0
    fi
    # 只删自己装的东西，避免误删用户在同一目录下的其他内容
    for item in "${ITEMS[@]}"; do
        rm -rf "${TARGET:?}/$item"
    done
    # 目录若已空则一并删除
    rmdir "$TARGET" 2>/dev/null || true
    echo "已从 $TARGET 卸载 $REPO_NAME"
    exit 0
fi

# ---------------------------------------------------------------- 安装
echo "=== 安装 School-Researcher ==="

# 防呆：目标目录若位于源码目录内部，会导致自我递归复制
mkdir -p "$TARGET"
SRC_REAL="$(cd "$SCRIPT_DIR" && pwd -P)"
TGT_REAL="$(cd "$TARGET" && pwd -P)"
if [[ "$TGT_REAL" == "$SRC_REAL" || "$TGT_REAL" == "$SRC_REAL"/* ]]; then
    echo "错误：目标目录位于源码目录内部（$TGT_REAL）。" >&2
    echo "      这会导致自我递归复制，已中止。请改用其他 --target。" >&2
    exit 1
fi

for item in "${ITEMS[@]}"; do
    if [[ -e "$SCRIPT_DIR/$item" ]]; then
        rm -rf "${TARGET:?}/$item"
        cp -R "$SCRIPT_DIR/$item" "$TARGET/"
    else
        echo "  跳过（源码中不存在）: $item"
    fi
done

echo
echo "已安装至: $TARGET"
echo "平台: $PLATFORM"
echo
echo "下一步:"
case "$PLATFORM" in
    claude) echo "  在 Claude Code 中输入 /school-researcher 或直接描述任务即可触发。" ;;
    gemini) echo "  在 Antigravity / Gemini CLI 中按 Skill 机制自动发现。" ;;
esac
echo "  核验产出: python3 $TARGET/scripts/verify.py <dossier.md>"
echo "  卸载:     ./install.sh --uninstall --target $TARGET"
