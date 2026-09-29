#!/usr/bin/env python3
"""校验各平台提示词的硬性长度上限。

为什么单独成文件：这段检查原先内联在 CI、文档、install.sh 三处，各写一遍正则，
结果各错各的——那个正则要求 description 块后紧跟 `[a-z_]+:`，而块标量后面其实是
frontmatter 结束符 `---`，于是永远匹配不到、永远报 0 字符，
"超限就报错" 的闸门实际上从未生效。

校验逻辑只能有一份。新增平台时在 LIMITS 里加一行即可。

用法：python3 scripts/check_limits.py [仓库根目录]
退出码：0 全部合规 / 1 有超限或无法解析
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def skill_description(text: str) -> str | None:
    """从 SKILL.md 的 YAML frontmatter 取 description 值（支持块标量与行内）。"""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)

    dm = re.search(r"^description:[ \t]*(.*)$", fm, re.M)
    if not dm:
        return None
    first = dm.group(1).strip()
    rest = fm[dm.end():]

    if first.startswith("|") or first.startswith(">"):
        lines = []
        for line in rest.split("\n"):
            if line.strip() and not line.startswith((" ", "\t")):
                break  # 回到顶格的同级键
            if line.strip():
                lines.append(line.strip())
        return "\n".join(lines)

    if first:
        return first.strip().strip('"').strip("'")

    for line in rest.split("\n"):
        if line.strip():
            return line.strip().strip('"').strip("'") if line.startswith((" ", "\t")) else ""
    return ""


def fenced_block(text: str, lang: str = "text") -> str | None:
    """取第一个 ```<lang> 代码块的内容。"""
    m = re.search(rf"```{lang}\n(.*?)```", text, re.S)
    return m.group(1).rstrip() if m else None


# (说明, 文件, 提取函数, 上限)
LIMITS: list[tuple[str, str, object, int]] = [
    ("SKILL.md description（Claude Code Skill）", "SKILL.md", skill_description, 1024),
    (
        "CODEX.md 压缩提示词（ChatGPT Custom Instructions）",
        "agent_rules/CODEX.md",
        lambda t: fenced_block(t, "text"),
        1500,
    ),
]


def emit(root: Path, needle: str, out: str) -> int:
    """校验并写出某个平台的提示词，供 install.sh 生成粘贴版使用。

    抽取逻辑放在这里而不是 install.sh 里，是为了让「哪个文件、取哪一段、上限多少」
    只有一处定义——重复实现正是本文件开头那个失效闸门的成因。
    """
    for label, rel, extract, limit in LIMITS:
        if needle not in rel:
            continue
        path = root / rel
        if not path.exists():
            print(f"错误：文件不存在: {rel}", file=sys.stderr)
            return 1
        value = extract(path.read_text(encoding="utf-8"))  # type: ignore[operator]
        if value is None:
            print(f"错误：未能从 {rel} 解析出提示词", file=sys.stderr)
            return 1
        n = len(value)
        if n > limit:
            print(f"错误：{rel} 的提示词 {n} 字符，超出上限 {limit}", file=sys.stderr)
            return 1
        Path(out).write_text(value + "\n", encoding="utf-8")
        print(f"  提示词 {n} / {limit} 字符 ✅")
        return 0
    print(f"错误：没有匹配 {needle!r} 的限额配置", file=sys.stderr)
    return 1


def main() -> int:
    argv = sys.argv[1:]

    if "--emit" in argv:
        i = argv.index("--emit")
        remaining = argv[i + 1:]
        if len(remaining) < 2:
            print("用法: check_limits.py --emit <文件匹配串> <输出路径> [仓库根]", file=sys.stderr)
            return 2
        needle, out = remaining[0], remaining[1]
        root = Path(remaining[2]) if len(remaining) > 2 else Path(".")
        return emit(root, needle, out)

    root = Path(argv[0] if argv else ".")
    bad = 0

    for label, rel, extract, limit in LIMITS:
        path = root / rel
        if not path.exists():
            print(f"❌ {label}\n   ← 文件不存在: {rel}")
            bad += 1
            continue
        try:
            value = extract(path.read_text(encoding="utf-8"))  # type: ignore[operator]
        except Exception as e:  # noqa: BLE001
            print(f"❌ {label}\n   ← 解析失败: {e}")
            bad += 1
            continue

        if value is None:
            # 解析失败必须报错，不能默默当作 0 —— 那正是本文件开头描述的失效方式
            print(f"❌ {label}\n   ← 未能从 {rel} 中解析出内容（格式可能已改）")
            bad += 1
            continue

        n = len(value)
        if n > limit:
            print(f"❌ {label}\n   {n} / {limit} 字符，超出 {n - limit} 字符")
            print("      超出部分不会被加载。请精简后重跑。")
            bad += 1
        else:
            pct = n / limit * 100
            print(f"✅ {label}\n   {n} / {limit} 字符（{pct:.0f}%）")

    print()
    print("全部合规。" if not bad else f"{bad} 项不合规。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
