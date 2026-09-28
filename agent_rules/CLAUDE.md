# Anthropic Claude Integration Guide (School-Researcher)

> **适用场景**：Claude Code（Skill 或 CLAUDE.md）、Claude Desktop（Project Knowledge）、或 Anthropic Messages API。

**权威规则源**：[`agent_rules/SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md) — 本文件不重复其内容，只说明如何接入。

---

## 1. 作为 Claude Code Skill 安装（推荐）

Claude Code 会从以下位置自动发现 Skill：

- 个人级：`~/.claude/skills/school-researcher/`
- 项目级：`<repo>/.claude/skills/school-researcher/`

```bash
mkdir -p ~/.claude/skills/school-researcher
cp -r SKILL.md scripts references templates agent_rules \
      ~/.claude/skills/school-researcher/
```

> 注意：`SKILL.md` 的 `description` 字段受 **1024 字符**上限约束，超限会导致
> Skill 无法被正确加载。修改后请自检：
>
> ```bash
> python3 scripts/check_skill.py
> ```
>
> （此前文档与 CI 里各写了一份内联正则，两份都写错了——正则要求 description 块后
> 紧跟 `[a-z]+:`，而块标量后面其实是 frontmatter 结束符 `---`，于是永远匹配不到、
> 永远报 0 字符，"超限报错" 的闸门从未生效。现在校验逻辑只有 `check_skill.py` 一份。）

---

## 2. Claude Desktop Project

在 Project 的 Knowledge 中挂载以下文件即可，无需额外的 Custom Instructions：

- `agent_rules/SYSTEM_PROMPT.md`（规则源）
- `references/verification_standards.md`（信源核验标准）
- `templates/master_dossier_template.md`（产出模板）

---

## 3. 作为项目 CLAUDE.md

若不想用 Skill 机制，可在项目根目录创建 `CLAUDE.md`：

```markdown
# School-Researcher

本工作区遵循 School-Researcher 工作流。

完整规则见 `agent_rules/SYSTEM_PROMPT.md`，产出模板见
`templates/master_dossier_template.md`，信源标准见
`references/verification_standards.md`。

定稿前必须运行：`python3 scripts/verify.py reports/`
退出码非 0 不得交付。
```

---

## 4. Anthropic Messages API 调用示例

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

system_prompt = open("agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()

message = client.messages.create(
    model="claude-sonnet-5",  # 请以当前最新的模型 ID 为准
    max_tokens=8192,
    temperature=0.1,
    system=system_prompt,
    messages=[{
        "role": "user",
        "content": (
            "做一下 JHU Peabody 的深度选校调研。结合 Common App 主文书底色，"
            "深挖巴尔的摩小众先锋空间与真实的教授论文 DOI，输出 Master Dossier。"
        ),
    }],
)

print(message.content[0].text)
```
