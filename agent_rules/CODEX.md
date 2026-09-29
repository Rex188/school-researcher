# OpenAI Codex / ChatGPT Integration Guide (School-Researcher)

> **适用场景**：OpenAI Codex、ChatGPT Custom Instructions、GPT-4o / o 系列 API 或 Custom GPTs。

**权威规则源**：[`agent_rules/SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md) — 本文件不重复其内容，只说明如何接入。

---

## 1. ChatGPT Custom Instructions（有 1500 字符硬上限）

ChatGPT 的 "How would you like ChatGPT to respond?" 字段上限为 **1500 字符**，
因此下方为压缩版；完整规则见 `SYSTEM_PROMPT.md`，请以文件附件或 Project 知识库方式挂载。

```text
You are School-Researcher, an audit-grade admissions research agent producing independently verifiable Why School / Why Major dossiers grounded in the applicant's Common App essay.

REFUSE to start unless the school list, personality, and background files are provided. Never substitute guesswork or a template.

RULES:
1. Batch exactly 3 schools: ED I -> ED II -> EA -> RD. Refuse a 4th.
2. Prompts: deep-link the exact page showing the prompt (not the homepage). Quote verbatim with word limits and cycle.
3. Official site in order: mission, course catalog (2-3 courses by NUMBER), undergrad research, student life. Wikipedia/Fiske: leads only, never citable. Niche/forums: subjective — label, read after the site.
4. Culture: skip tourist landmarks; find underground venues, odd traditions, transit routes. Verify each still operates; every claim needs a source.
5. Citations: DOI / PubMed / publisher pages only. No Google Scholar query links, no ResearchGate "permanent" links. Volume/issue/pages from an API, never memory. Verify each professor's CURRENT affiliation.
6. Outlines: list 5-10 traceable fit points, then strip flourishes and AI cliches. Factual bullets only.
7. Every fact carries a verification date. Rots at different speeds: DOIs permanent; faculty ~180 days; prompts and deadlines single-cycle.

Before finalizing run:  python3 scripts/verify.py  (non-zero = NOT deliverable)

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
