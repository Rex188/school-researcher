# School-Researcher: 本科申请深度选校调研与学术穿透系统

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-blue.svg)](https://github.com/Rex188/school-researcher)
[![Multi-Agent Ready](https://img.shields.io/badge/Agents-Codex%20%7C%20Claude%20%7C%20Gemini%20%7C%20DeepSeek-success.svg)](./agent_rules/)
[![Verified by verify.py](https://img.shields.io/badge/Sources-verified%20by%20scripts%2Fverify.py-orange.svg)](./scripts/verify.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**School-Researcher** 是专为顶尖美本及综合大学申请打造的**审计级选校调研与学术穿透 Agent Skill**。
它旨在终结传统 AI 工具产出"维基百科式"空泛介绍、编造虚假教授论文、以及充满感性 AI 废话的顽疾，
为申请者提供可直接作为文书论据的战略情报中枢。

---

## 核心理念：可审计性来自核验回路，不是来自"要求模型别幻觉"

这是本项目与同类工具的根本分野。

在提示词里写一百遍"绝不编造"，模型依然会编——因为约束的是**意愿**，而不是**事实**。
本项目的做法是：**每一条外部事实都必须能被独立重新取数**。为此提供了 [`scripts/verify.py`](./scripts/verify.py)：

```bash
python3 scripts/verify.py reports/          # 核验全部产出
python3 scripts/verify.py reports/ --html report.html   # 另存一份可视化 HTML 报告
python3 scripts/verify.py --json            # 机器可读，可直接用于 CI
python3 scripts/verify.py --self-test       # 先证明核验器自己不误判
```

`--html` 生成的是**单文件、零外部依赖**的报告（内联 CSS，无 CDN / 无字体 / 无 JS），
双击即可用浏览器打开，也可直接发给别人或打印成 PDF。
每个 DOI / PubMed 条目都会列出**数据源实际返回的标题与卷期页**，可与文中引文逐字比对。

它会：

- **DOI** → 调 CrossRef API 反查标题/作者/**卷·期·页码**，与文中所写逐项比对，不一致即判 ❌
- **PubMed** → 调 NCBI E-utilities 反查，同上
- **普通链接** → HTTP 实测，区分 `200 / 反爬403 / 404 / DNS失效 / TLS证书不匹配`
- **时效戳** → 检查「核验日期」是否超出该类数据的时效窗口
- **铁律合规** → 扫描 Google Scholar 引用等违规写法

**退出码非 0 即表示档案不可交付。** 仅依赖 Python 标准库，无需 `pip install`。

### 核验器自身的失效模式

核验器最容易犯的错，是把**自己的故障**说成**你的来源失效**。那比不核验更糟：
它会让你删掉一条正确的引用。因此本项目对以下情形一律降级为 ⚠️「无法判定」而非 ❌：

| 现象 | 为什么不能判 ❌ |
| :--- | :--- |
| CrossRef / NCBI 返回 **429** | 是本工具并发请求触发的限流，与 DOI 是否存在无关（已加退避重试，并发降到 3） |
| 页面返回 **404，但复测出现 403/200** | 反爬抖动。实测 `peabody.jhu.edu` 对确实存在的页面约 13% 请求返回 404 |
| 仅 **HEAD** 请求返回 404 | WAF 误答 HEAD 极常见，必须用 GET 复核 |
| 超时 / 握手失败 / 连接被拒 | 无法区分是源挂了还是本机网络问题 |
| DNS 解析失败、TLS 证书域名不符 | 这两个是**可信的**失效信号，仍判 ❌ |

判定逻辑由 `--self-test` 的 12 条回归用例钉死；CI 会先跑自检，再用它去判别人的档案。

> 为什么需要这个？因为引文的**页码**和教授的**任职单位**这类事实，
> 恰恰是模型最容易"写得看起来很对"的地方：论文真实存在，但卷期页是编的；
> 教授真实存在，但早已不在那所学校。不反查一手数据源，这两类错误无法被发现。

---

## 核心设计哲学 (Core Philosophy)

1. **核验回路优先 (Verification Loop First)**：
   任何一条外部事实都必须带**核验日期**与**核验方式**。定稿前必须跑通 `verify.py`。
   无法被独立核验的条目，宁可删除，不得写入正文。
2. **认知底色互文 (Hermeneutic Alignment)**：
   文书绝非独立孤岛。系统必须首先提取申请人的 **Common App 主文书（Personal Statement）** 与底层叙事档案，
   将大学调研锚定为主文书中未决哲学/技术矛盾的"学术求解站"。
3. **三所学校单批次轮转 (Strict 3-School Batching)**：
   严格限制每次调研 3 所大学，按照 `ED I → ED II → EA → RD` 优先级有序推进，
   并在选校总表中以状态列记录进度；批次已满时拒绝追加第 4 所。
4. **官方题目逐字锁定 (Verbatim Prompt Triage)**：
   必须给出**列有该题目的官方页面深链**（不是招生办首页），提取英文原文与字数死线，并标注适用申请周期。
   针对取消补充文书的院校，出具官方证据打标 `[免写WhySchool]`。
5. **小众生态穿透 (Niche & Underground Ecology)**：
   拒绝人人皆知的大楼与排名。深挖地下先锋空间、圈内特殊传统与特定通勤动线，
   且**必须核实该实体当前是否仍在运营**——小场馆与独立书店关门迁址是常态。
6. **学术文献永久直链 (Permanent DOI / PubMed Only)**：
   严禁 Google Scholar 动态搜索链接；亦不接受把 ResearchGate 等第三方转载页当作"永久直链"。
   教授著作必须提供 **DOI / PubMed / 政府档案 / 出版社官方专页**，
   且**任职单位必须单独核验**——把外校教授当作目标院校的文书锚点是硬伤。
7. **文书大纲去 AI 化 (De-AI-fied Fact Blueprints)**：
   删去一切感性套话，以**纯事实 Bullet Points** 交代场景冲突、认知转变、教授文献承接与校内外落地行动。

---

## 目录与物理隔离规范 (Architecture)

```
SchoolResearch/
├── 00_选校总表.md                    # 全局导航与申请批次审计总台账（含状态列）
├── SOP for School Research.md       # 标准操作流程规范手册
├── inputs/                          # 【输入档案库】隔离存放原始物料
│   ├── 01_申请者画像与叙事资产总档案.md   # 整合了 Common App 主文书底座的个人核心画像
│   ├── common_app_personal_statement.md# 申请人 Common App 主文书定稿英文全文
│   └── 选校表.md                      # 原始选校与专业诉求草案
└── reports/                         # 【独立调研报告库】单校独立文件夹归档
    ├── JHU_Peabody/
    │   └── JHU_Peabody_Master_Dossier.md # 官方题目审计 + 深度研报综合 Master Dossier
    └── ...
```

本仓库自身的结构：

```
├── SKILL.md                         # Skill 定义（Claude / Gemini 等按需自动挂载）
├── install.sh                       # 安装脚本：技能安装 + 工作区脚手架
├── scripts/
│   ├── verify.py                    # 引文核验器（本项目的核心），含 --self-test
│   └── check_limits.py              # 校验各平台提示词的长度上限
├── agent_rules/                     # 多平台接入说明
│   └── SYSTEM_PROMPT.md             # 【权威规则源】其余文件均为其薄封装
├── references/verification_standards.md  # 信源核验标准
├── templates/
│   ├── master_dossier_template.md   # 产出模板（含核验戳字段）
│   └── workspace/                   # 工作区骨架（install.sh --workspace 使用）
└── examples/                        # 脱敏后的范例档案
```

> **单一权威源原则**：所有执行规则以 `agent_rules/SYSTEM_PROMPT.md` 为准；
> 所有长度上限校验以 `scripts/check_limits.py` 为准。
> 其余各平台文件只说明"如何接入"，不重复规则内容——避免同一条铁律被复述四五遍后各自漂移。
>
> 这条原则不是洁癖，是本仓库真实踩过的坑：同一段校验正则曾被内联在 CI、文档、
> install.sh 三处，三份各错各的，导致"超限就报错"的闸门从未生效。
> 重复的不只是代码，是**错误**。

---

## 多 Agent 平台全栈接入 (Multi-Agent Integration)

配置文件均位于 `agent_rules/`，各平台接入方式详见对应文件：

| 平台 | 配置文件 | 安装方式 | 说明 |
| :--- | :--- | :--- | :--- |
| **Claude Code** | [`CLAUDE.md`](./agent_rules/CLAUDE.md) | `--platform claude` | 装到 `~/.claude/skills/`，自动发现 |
| **Claude Desktop** | [`CLAUDE.md`](./agent_rules/CLAUDE.md) | 手动 | 把规则源挂进 Project Knowledge |
| **Antigravity / Gemini CLI** | [`GEMINI.md`](./agent_rules/GEMINI.md) | `--platform gemini` | 装到工作区 `.agent/skills/` |
| **Cursor** | [`SYSTEM_PROMPT.md`](./agent_rules/SYSTEM_PROMPT.md) | `--platform cursor` | 写入 `.cursor/rules/*.mdc` |
| **Windsurf** | [`SYSTEM_PROMPT.md`](./agent_rules/SYSTEM_PROMPT.md) | `--platform windsurf` | 写入 `.windsurf/rules/` |
| **ChatGPT** | [`CODEX.md`](./agent_rules/CODEX.md) | `--platform chatgpt` | 生成 1281 字符粘贴版（上限 1500） |
| **OpenAI Codex** | [`CODEX.md`](./agent_rules/CODEX.md) | `--platform codex` | 同上 |
| **DeepSeek** | [`DEEPSEEK.md`](./agent_rules/DEEPSEEK.md) | `--platform deepseek` | 附本地部署约束：事实层必须外部取数 |
| **任意 OpenAI 兼容端点** | [`SYSTEM_PROMPT.md`](./agent_rules/SYSTEM_PROMPT.md) | `--platform generic` | 生成完整 SYSTEM_PROMPT |

平台分两类，`./install.sh --list-platforms` 会标明：

- **目录型**（claude / gemini / cursor / windsurf）—— 平台有规则目录约定，脚本把文件装进去
- **提示词型**（chatgpt / codex / deepseek / generic）—— 平台没有目录约定，脚本生成一份可直接粘贴的提示词

> **唯一真正跨平台的东西是核验器。** 换个模型，提示词形态会变；
> 但 `verify.py` 在任何平台上都跑在同一台机器上，判定同一份档案。
> 这不是巧合——把事实层从模型里拿出来，正是本项目能在多个平台间迁移的原因。

各平台的 API 调用示例（Anthropic / OpenAI / Google GenAI / DeepSeek）见对应文件。

---

## 快速开始

### 0. 先看它怎么工作（60 秒，不用安装）

```bash
git clone https://github.com/Rex188/school-researcher.git
cd school-researcher
python3 scripts/verify.py examples/
```

这会核验仓库里那份真实的 JHU Peabody 范例档案 —— 每一条引文都会列出
**数据源实际返回的标题与卷期页**，你可以直接和文中写的逐字比对。
加 `--html report.html` 可另存一份可视化报告。

### 1. 安装技能

```bash
./install.sh                      # Claude Code（默认）
./install.sh --platform gemini    # Antigravity / Gemini CLI
./install.sh --list-platforms     # 看看还有哪些平台
```

### 2. 建立工作区

```bash
./install.sh --workspace ~/SchoolResearch
```

生成如下骨架（**已存在的文件不会被覆盖**）：

```
SchoolResearch/
├── 00_选校总表.md                        # 导航与批次台账（含状态列）
├── inputs/
│   ├── 01_申请者画像与叙事资产总档案.md      # ← 先填这个
│   ├── common_app_personal_statement.md  # ← 主文书定稿全文
│   └── 选校表.md                          # 原始诉求草案
└── reports/                              # 产出目录（按学校分文件夹）
```

工作区自带 `.gitignore`（忽略全部内容）——里面是你的个人信息，不要提交到公开仓库。

### 3. 填三个文件，然后开工

1. `inputs/01_申请者画像与叙事资产总档案.md` —— 关键是第 1 节「主文书核心矛盾」：
   写清主文书提出了什么**未决的**问题。所有 Why School 都要成为它的续篇，
   这一节决定产出质量的上限。
2. `inputs/common_app_personal_statement.md` —— 粘贴主文书**逐字全文**（不要摘要）。
3. `00_选校总表.md` —— 锁定第一批 3 所。注意是**硬限 3 所**，Agent 会拒绝第 4 所。

然后对 Agent 说：

```
读 agent_rules/SYSTEM_PROMPT.md，对 00_选校总表.md 里的第一批执行 Step 1–9。
```

### 4. 核验与交付

```bash
python3 scripts/verify.py reports/ --html report.html
echo "退出码: $?"      # 非 0 即不可交付
```

**退出码为 0 之前，不要在任何地方说"来源已核验"。** 那句话是关于证据状态的事实断言，
没跑过就是编的 —— 这正是整个项目要解决的问题。

> ⚠️ 项（反爬 403、限流、超时）需要**人工点开确认**，然后在档案的「核验方式」列
> 改写为 `反爬待人工`。它们不是错误，但也不等于通过。

---

## 黄金范例 (Benchmark Dossier)

👉 **[JHU Peabody Master Dossier](./examples/JHU_Peabody_Master_Dossier.md)**

该范例演示了完整的产出形态：官方题目深链与逐字原文、校园小众生态与城市暗线、
跨学科机构与专项基金、教授文献的永久 DOI 溯源、以及去 AI 化的三段式文书大纲。

> **说明**：范例中的**申请人信息为虚构演示数据**；院校、教授、文献、场馆等外部事实
> 均为真实公开信息，每条附有核验日期与核验方式，可点击核验，也可用 `verify.py` 复现核验结果。

---

## 开源协议 (License)

本项目采用 [MIT License](./LICENSE) 开源协议。
