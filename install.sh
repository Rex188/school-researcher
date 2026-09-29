#!/usr/bin/env bash
#
# School-Researcher 安装脚本
#
# 用法:
#   ./install.sh                            # 安装为 Claude Code Skill（默认）
#   ./install.sh --platform gemini          # 安装到当前工作区的 Antigravity/Gemini 目录
#   ./install.sh --platform cursor          # 写入 .cursor/rules/school-researcher.mdc
#   ./install.sh --platform chatgpt         # 生成可直接粘贴的提示词文件
#   ./install.sh --workspace ~/SchoolResearch   # 建立工作区骨架
#   ./install.sh --target /path/to/skill    # 自定义安装位置
#   ./install.sh --list-platforms           # 列出所有平台及其目标位置
#   ./install.sh --uninstall                # 卸载
#
# 两类安装方式（--list-platforms 会标明每个平台属于哪类）:
#   目录型：平台有 Skill / rules 目录约定，脚本把规则文件装进去
#   提示词型：平台没有目录约定（如 ChatGPT），脚本生成一份可直接粘贴的提示词

set -euo pipefail

REPO_NAME="school-researcher"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 装进 Skill 目录的内容（刻意排除 .git 与 examples/，后者不是运行所需）
ITEMS=(SKILL.md scripts references templates agent_rules README.md LICENSE)

# 平台 → 类型:默认目标位置
platform_target() {
    case "$1" in
        claude)   echo "dir:$HOME/.claude/skills/$REPO_NAME" ;;
        gemini)   echo "dir:$PWD/.agent/skills/$REPO_NAME" ;;
        cursor)   echo "dir:$PWD/.cursor/rules" ;;
        windsurf) echo "dir:$PWD/.windsurf/rules" ;;
        chatgpt|codex|deepseek|generic) echo "prompt:$PWD/$REPO_NAME-prompt.txt" ;;
        *) return 1 ;;
    esac
}

platform_help() {
    case "$1" in
        claude)   echo "Claude Code —— 自动发现 ~/.claude/skills/ 下的 SKILL.md" ;;
        gemini)   echo "Antigravity / Gemini CLI —— 当前工作区内的 .agent/skills/" ;;
        cursor)   echo "Cursor —— 写入 .cursor/rules/ 下的 .mdc 规则文件" ;;
        windsurf) echo "Windsurf —— 写入 .windsurf/rules/" ;;
        chatgpt)  echo "ChatGPT —— 生成 Custom Instructions 粘贴版（1500 字符上限）" ;;
        codex)    echo "OpenAI Codex —— 生成提示词文件" ;;
        deepseek) echo "DeepSeek —— 生成提示词文件（事实层仍须本地跑 verify.py）" ;;
        generic)  echo "任意 OpenAI 兼容端点 —— 生成完整 SYSTEM_PROMPT 文件" ;;
        *) return 1 ;;
    esac
}

usage() {
    sed -n '3,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

list_platforms() {
    echo "可用平台："
    echo
    for p in claude gemini cursor windsurf chatgpt codex deepseek generic; do
        local spec kind target
        spec="$(platform_target "$p")"
        kind="${spec%%:*}"
        target="${spec#*:}"
        printf '  %-9s [%s]  %s\n' "$p" "$kind" "$(platform_help "$p")"
        printf '  %-9s         → %s\n\n' "" "$target"
    done
    echo "  dir    = 安装规则文件到该目录"
    echo "  prompt = 生成一份可直接粘贴的提示词文件（平台无目录约定）"
}

PLATFORM="claude"
TARGET=""
WORKSPACE=""
DO_UNINSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform)       PLATFORM="${2:-}";  shift 2 ;;
        --target)         TARGET="${2:-}";    shift 2 ;;
        --workspace)      WORKSPACE="${2:-}"; shift 2 ;;
        --uninstall)      DO_UNINSTALL=1;     shift ;;
        --list-platforms) list_platforms; exit 0 ;;
        -h|--help)        usage; exit 0 ;;
        *) echo "未知参数: $1" >&2; echo; usage >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------- 工作区脚手架

scaffold_workspace() {
    local ws="$1"
    local src="$SCRIPT_DIR/templates/workspace"

    if [[ ! -d "$src" ]]; then
        echo "错误：模板目录不存在 $src" >&2
        return 1
    fi

    echo "=== 建立工作区骨架 ==="
    mkdir -p "$ws/inputs" "$ws/reports"

    # 已存在的文件不覆盖——用户可能已经填过内容
    local created=0 skipped=0
    while IFS= read -r -d '' f; do
        local rel="${f#"$src"/}"
        local dst="$ws/$rel"
        if [[ -e "$dst" ]]; then
            echo "  跳过（已存在，不覆盖）: $rel"
            skipped=$((skipped + 1))
        else
            mkdir -p "$(dirname "$dst")"
            cp "$f" "$dst"
            echo "  创建: $rel"
            created=$((created + 1))
        fi
    done < <(find "$src" -type f -print0)

    # 工作区不应被提交到公开仓库（含申请人个人信息）
    if [[ ! -e "$ws/.gitignore" ]]; then
        printf '# 申请人个人信息，禁止入库\n*\n' > "$ws/.gitignore"
        echo "  创建: .gitignore（忽略全部内容）"
        created=$((created + 1))
    fi

    echo
    echo "工作区就绪: $ws  （新建 $created 项，跳过 $skipped 项）"
    echo
    echo "接下来:"
    echo "  1. 填 $ws/inputs/01_申请者画像与叙事资产总档案.md"
    echo "  2. 把主文书全文放进 $ws/inputs/common_app_personal_statement.md"
    echo "  3. 在 $ws/00_选校总表.md 里锁定第一批 3 所"
    echo "  4. 让 Agent 按 SKILL.md 的 Step 1-9 执行"
    echo "  5. 核验: python3 scripts/verify.py \"$ws/reports/\""
}

if [[ -n "$WORKSPACE" ]]; then
    scaffold_workspace "$WORKSPACE"
    exit 0
fi

# ---------------------------------------------------------------- 解析平台

SPEC="$(platform_target "$PLATFORM" || true)"
if [[ -z "$SPEC" && -z "$TARGET" ]]; then
    echo "错误：未知平台 '$PLATFORM'。" >&2
    echo "      用 --list-platforms 查看可用平台，或用 --target 显式指定目录。" >&2
    exit 1
fi
KIND="${SPEC%%:*}"
DEFAULT_TARGET="${SPEC#*:}"
[[ -z "$TARGET" ]] && TARGET="$DEFAULT_TARGET"

# ---------------------------------------------------------------- 卸载
if [[ "$DO_UNINSTALL" == "1" ]]; then
    if [[ "$KIND" == "prompt" ]]; then
        if [[ -f "$TARGET" ]]; then
            rm -f "$TARGET"
            echo "已删除提示词文件: $TARGET"
        else
            echo "文件不存在，无需卸载: $TARGET"
        fi
        exit 0
    fi
    if [[ ! -d "$TARGET" ]]; then
        echo "目录不存在，无需卸载: $TARGET"
        exit 0
    fi
    # 只删自己装的东西，避免误删用户在同一目录下的其他内容
    for item in "${ITEMS[@]}"; do
        rm -rf "${TARGET:?}/$item"
    done
    rm -f "$TARGET/school-researcher.mdc" 2>/dev/null || true
    rmdir "$TARGET" 2>/dev/null || true
    echo "已从 $TARGET 卸载 $REPO_NAME"
    exit 0
fi

# ---------------------------------------------------------------- 提示词型安装

emit_prompt() {
    local out="$1"
    case "$PLATFORM" in
        chatgpt|codex)
            # 抽取与限额校验统一由 check_limits.py 负责，避免逻辑重复后各自漂移
            if ! python3 "$SCRIPT_DIR/scripts/check_limits.py" \
                    --emit "CODEX.md" "$out" "$SCRIPT_DIR"; then
                echo "错误：提示词超出平台长度上限，已中止（详见上方提示）。" >&2
                exit 1
            fi
            ;;
        deepseek)
            python3 - "$SCRIPT_DIR" "$out" <<'PY'
import sys
src_dir, out = sys.argv[1], sys.argv[2]
sysp = open(f"{src_dir}/agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()
extra = (
    "\n\n---\n\n## DeepSeek 专用约束\n\n"
    "你无法联网取数。所有外部事实（DOI、卷期页、教授任职、题目原文）"
    "必须由本地 `scripts/verify.py` 与人工检索先行采集并写入 dossier，"
    "你只做论证结构加工。**不得自行补全或推测任何卷期页码。**\n"
)
open(out, "w", encoding="utf-8").write(sysp + extra)
print("  已写入完整规则 + 本地部署约束")
PY
            ;;
        *)
            cp "$SCRIPT_DIR/agent_rules/SYSTEM_PROMPT.md" "$out"
            echo "  已写入完整 SYSTEM_PROMPT"
            ;;
    esac
    echo
    echo "提示词已生成: $out"
    echo
    echo "下一步:"
    echo "  1. 打开该文件，全选复制"
    case "$PLATFORM" in
        chatgpt) echo "  2. 粘贴进 ChatGPT → Settings → Personalization → Custom Instructions 的第一个框" ;;
        *)       echo "  2. 作为 system prompt 粘贴进你的客户端" ;;
    esac
    echo "  3. 注意：无论哪个平台，事实核验都要在本机跑 verify.py —— 模型无法自己核实自己"
}

if [[ "$KIND" == "prompt" ]]; then
    emit_prompt "$TARGET"
    exit 0
fi

# ---------------------------------------------------------------- 目录型安装

# 防呆：目标目录若位于源码目录内部，会导致自我递归复制。
# 必须在 mkdir 之前检查，否则中止时会残留一个空目录。
# 用 python 做路径归一化：os.path.realpath 对尚不存在的路径也能正确解析
# （cd + pwd -P 则要求目录已存在，这正是原版本被迫先 mkdir 的原因）。
if ! python3 - "$SCRIPT_DIR" "$TARGET" <<'PY'
import os, sys
src, tgt = (os.path.realpath(p) for p in sys.argv[1:3])
if tgt == src or tgt.startswith(src + os.sep):
    print(f"错误：目标目录位于源码目录内部（{tgt}）。", file=sys.stderr)
    print("      这会导致自我递归复制，已中止。请改用其他 --target。", file=sys.stderr)
    sys.exit(1)
PY
then
    exit 1
fi

mkdir -p "$TARGET"

echo "=== 安装 School-Researcher ==="

# Cursor / Windsurf 用 .mdc 单文件规则，不铺一整个目录
if [[ "$PLATFORM" == "cursor" || "$PLATFORM" == "windsurf" ]]; then
    RULE="$TARGET/school-researcher.mdc"
    python3 - "$SCRIPT_DIR" "$RULE" <<'PY'
import sys
src_dir, rule = sys.argv[1], sys.argv[2]
sysp = open(f"{src_dir}/agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()
fm = (
    "---\n"
    "description: School-Researcher —— 可核验的本科选校调研与文书审计\n"
    "alwaysApply: true\n"
    "---\n\n"
)
open(rule, "w", encoding="utf-8").write(fm + sysp)
print(f"  规则文件: {rule}")
PY
    echo
    echo "已安装至: $TARGET"
    echo
    echo "下一步:"
    echo "  核验产出: python3 scripts/verify.py reports/"
    echo "  完整规则: $SCRIPT_DIR/agent_rules/SYSTEM_PROMPT.md"
    echo "  卸载:     ./install.sh --uninstall --target $TARGET"
    exit 0
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
    claude) echo "  1. 建工作区: ./install.sh --workspace ~/SchoolResearch" ;;
    gemini) echo "  1. 建工作区: ./install.sh --workspace ./SchoolResearch" ;;
esac
echo "  2. 核验产出: python3 scripts/verify.py reports/ --html report.html"
echo "  卸载:       ./install.sh --uninstall --target $TARGET"
