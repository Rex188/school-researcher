# DeepSeek Integration Guide (School-Researcher)

> **适用场景**：DeepSeek 开放平台 API（`deepseek-chat` / `deepseek-reasoner`）、本地 Ollama / vLLM 部署、或 DeepSeek 网页端。

**权威规则源**：[`agent_rules/SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md) — 本文件不重复其内容，只说明如何接入。

---

## 1. 推理模型适合承担哪一环

`deepseek-reasoner` 的长链推理能力适合处理**不需要联网取数的纯逻辑环节**：

1. **因果链构建**：从主文书的微观冲突到认识论转变的推导是否严密。
2. **自我审查**：检验文书大纲中是否存在 AI 腔调、套话或逻辑断裂。
3. **观点匹配度复核**：判断导师论文的学术观点是否真正呼应申请人痛点，而非牵强附会。

> ⚠️ **推理模型不能替代核验回路。** 因果链再严密，也无法判断一个 DOI 的页码对不对，
> 也无法知道某位教授是否已经换了学校。**事实层必须由 `scripts/verify.py` 负责**，
> 推理层只负责论证结构。不要把"推理模型想了一遍"当作事实已被核实的证据。

---

## 2. API 调用示例 (OpenAI 兼容协议)

```python
import os
from openai import OpenAI

# DeepSeek 兼容 OpenAI 客户端协议
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

system_prompt = open("agent_rules/SYSTEM_PROMPT.md", encoding="utf-8").read()

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": """
请根据 JHU Peabody Master Dossier 中【已通过 verify.py 核验】的文献与事实，
推导一段 350 字文书的论证逻辑链。

要求：
1. 彻底剔除修饰性套话。
2. 严格按因果机制（事实冲突 -> 认知转变 -> 学术对接 -> 社群反哺）以纯 Bullet Points 输出。
3. 学术承接必须引用档案中已核验的文献，不得自行补全或推测卷期页码。
""",
        },
    ],
)

print("=== Reasoning Chain ===")
print(response.choices[0].message.reasoning_content)
print("\n=== Final Outline ===")
print(response.choices[0].message.content)
```

---

## 3. 本地部署提示

使用 Ollama / vLLM 本地部署时，模型无法联网取数，所有外部事实**必须**由外部工具
（`scripts/verify.py`、手动检索）先行采集并写入 dossier，再由本地模型做论证加工。
本地模型只做加工，不做断言来源。
