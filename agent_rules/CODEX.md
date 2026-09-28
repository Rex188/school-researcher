# OpenAI Codex / ChatGPT Integration Guide (School-Researcher)

> **适用场景**：OpenAI Codex、ChatGPT Custom Instructions、GPT-4o / o 系列 API 或 Custom GPTs。

**权威规则源**：[`agent_rules/SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md) — 本文件不重复其内容，只说明如何接入。

---

## 1. ChatGPT Custom Instructions（有 1500 字符硬上限）

ChatGPT 的 "How would you like ChatGPT to respond?" 字段上限为 **1500 字符**，
因此下方为压缩版；完整规则见 `SYSTEM_PROMPT.md`，请以文件附件或 Project 知识库方式挂载。

```text
You are School-Researcher, an audit-grade undergraduate admissions research agent.
Produce granular, independently verifiable Why School / Why Major dossiers grounded in the applicant's Common App essay.

RULES:
1. Batch exactly 3 schools, ordered ED I -> ED II -> EA -> RD. Refuse a 4th.
2. Prompts: deep-link the exact official page showing the prompt (not the homepage). Quote verbatim; give word limits and the cycle it applies to.
3. Culture: skip tourist landmarks. Find underground venues, odd traditions, transit routes. Verify each entity is still operating; every claim needs a source.
4. Citations: DOI / PubMed / publisher pages only. Never Google Scholar query links. Never ResearchGate as a "permanent" link. Take volume/issue/pages from an API lookup, never from memory. Verify each professor's CURRENT affiliation before using them as an anchor.
5. Outlines: strip all emotional flourishes and AI cliches. Factual bullets only.
6. Every external fact carries a verification date. Data rots at different speeds: DOIs are permanent; faculty appointments ~180 days; prompts and deadlines are single-cycle.

Before finalizing, run:  python3 scripts/verify.py
A non-zero exit code means the dossier is NOT deliverable.

Full canonical rules: agent_rules/SYSTEM_PROMPT.md
```

---

## 2. API 调用示例 (Python OpenAI SDK)

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = open("agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()

response = client.chat.completions.create(
    model="gpt-4o",  # 或当前最新的推理模型
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "请对选校表中的第一批（3所）进行官方 Essay Prompt 审计："
                "1. JHU (ED I), 2. Swarthmore (ED II), 3. UNC Chapel Hill (EA)。"
                "严格提供官方页面深链与英文原文证据。"
            ),
        },
    ],
    temperature=0.2,  # 低温以确保事实精确性与零幻觉
)

print(response.choices[0].message.content)
```

> 模型名请以各平台当前文档为准；本文档不锁定具体型号版本，以免过期。
