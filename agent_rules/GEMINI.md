# Google Gemini & Antigravity Integration Guide (School-Researcher)

> **适用场景**：Google Antigravity IDE、Gemini CLI、Google GenAI Python SDK。

**权威规则源**：[`agent_rules/SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md) — 本文件不重复其内容，只说明如何接入。

---

## 1. Antigravity / Gemini CLI 本地生效

将本仓库克隆到你工作区的 Skill 目录即可，Antigravity 会自动发现并解析 `SKILL.md`：

```bash
# 在 Antigravity 工作区根目录执行
mkdir -p .agent/skills
git clone https://github.com/Rex188/school-researcher.git \
          .agent/skills/school-researcher
```

> 具体 Skills 目录约定请以你所使用的 Antigravity / Gemini CLI 版本文档为准——
> 该目录规范由客户端定义，不同版本可能不同。

安装后在聊天窗口直接输入即可触发：

- `做一下 Swarthmore 的深度选校调研`
- `执行选校表第二批（Rutgers, UVA, Georgia Tech）的 Essay Prompt Triage`

---

## 2. Google GenAI SDK 调用示例 (Python)

> **注意**：旧的 `google-generativeai` 包已停止维护，新项目请使用 `google-genai`。

```bash
pip install google-genai
```

```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_instruction = open("agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()

response = client.models.generate_content(
    model="gemini-2.5-pro",  # 请以当前最新型号为准
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
        top_p=0.95,
    ),
    contents=(
        "执行选校总表中 Swarthmore College 的 Step 4-10 深度调研，"
        "重点挖掘哲学与音乐系小众研讨课、建校宗旨与本科研究机会、教授专著及永久 DOI 链接。"
    ),
)

print(response.text)
```

---

## 3. 长上下文用法建议

Gemini 系列上下文窗口较大，适合一次性挂载整个 `SchoolResearch/` 目录
（含 `inputs/` 申请人档案 + 全部历史 dossier）做跨校一致性检查。但请注意：

- 挂载历史 dossier 时，其中的**核验日期**会一并进入上下文。若历史档案已过时效，
  模型可能沿用过期事实。跨周期复用前请先对旧档案重跑 `python3 scripts/verify.py`。
