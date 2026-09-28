#!/usr/bin/env python3
"""检查 SKILL.md 的 description 长度是否符合 Claude Code 的 1024 字符上限。

为什么单独成文件：这段检查原先同时内联在 CI workflow 和文档里，两处各写一遍正则，
结果两处都写错了——正则要求 description 块后面紧跟 `[a-z_]+:`，
但块标量后面其实是 frontmatter 的结束符 `---`，于是永远匹配不到、永远报 0 字符，
"超限就报错" 的闸门实际上从未生效。校验逻辑只能有一份。

用法：python3 scripts/check_skill.py [SKILL.md]
退出码：0 合规 / 1 超限或无法解析
"""

from __future__ import annotations

import re
import sys

LIMIT = 1024


def parse_description(text: str) -> str | None:
    """从 YAML frontmatter 中取出 description 的值（支持块标量与行内两种写法）。"""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)

    # 先定位 description: 这一行，再决定它是块标量还是行内值
    dm = re.search(r"^description:[ \t]*(.*)$", fm, re.M)
    if not dm:
        return None
    first = dm.group(1).strip()
    rest = fm[dm.end():]

    if first.startswith("|") or first.startswith(">"):
        # 块标量：收下后续所有「缩进更深」的行，遇到顶格键或结束即止
        lines = []
        for line in rest.split("\n"):
            if line.strip() and not line.startswith((" ", "\t")):
                break  # 回到顶格的同级键
            if line.strip():
                lines.append(line.strip())
        return "\n".join(lines)

    if first:
        return first.strip().strip('"').strip("'")

    # 行内值可能写在下一行（缩进续行）
    for line in rest.split("\n"):
        if line.strip():
            return line.strip().strip('"').strip("'") if line.startswith((" ", "\t")) else ""
    return ""


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "SKILL.md"
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"❌ 无法读取 {path}: {e}")
        return 1

    desc = parse_description(text)
    if desc is None:
        # 解析失败必须报错，不能默默当作 0 —— 那正是本文件开头描述的失效方式
        print(f"❌ 未能从 {path} 解析出 description（frontmatter 缺失或格式异常）")
        return 1

    n = len(desc)
    status = "✅" if n <= LIMIT else "❌ 超限"
    print(f"{status} {path} description = {n} / {LIMIT} 字符")
    if n > LIMIT:
        print("   超出部分不会被加载，Skill 可能无法被正确触发。请精简后重跑。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
