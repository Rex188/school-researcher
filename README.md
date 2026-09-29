# School-Researcher

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-blue.svg)](https://github.com/Rex188/school-researcher)
[![Multi-Agent Ready](https://img.shields.io/badge/Agents-Codex%20%7C%20Claude%20%7C%20Gemini%20%7C%20DeepSeek-success.svg)](./agent_rules/)
[![Verified by verify.py](https://img.shields.io/badge/Sources-verified%20by%20scripts%2Fverify.py-orange.svg)](./scripts/verify.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**School-Researcher** 是一个服务于美国本科申请的**选校调研Agent Skill**。
它很大程度上解决了传统 AI 工具产出"维基百科式"空泛介绍、编造虚假教授论文的问题。
为申请者提供可直接作为小文书论据。

---

## 对于幻觉的处理办法

**不用提示词软性要求，用链接重跑检验**

这是本项目与同类工具的根本区别。

在提示词里写一百遍"绝不编造"，模型依然会编——因为约束的是**意愿**，而不是**事实**。
本项目的做法是：**每一条外部事实都必须能被独立重新取数**。为此提供了 [`scripts/verify.py`](./scripts/verify.py)：

```bash
python3 scripts/verify.py reports/          # 核验全部产出
python3 scripts/verify.py reports/ --html report.html   # 另存一份可视化 HTML 报告
python3 scripts/verify.py --json            # 机器可读，可直接用于 CI
python3 scripts/verify.py --self-test       # 先证明核验器自己不误判
```


生成的报告双击即可用浏览器打开，也可直接发给别人或打印成 PDF。
每个 DOI / PubMed 条目都会列出**数据源实际返回的标题与卷期页**，可与文中引文逐字比对。

它会：

- **DOI** → 调 CrossRef API 反查标题/作者/**卷·期·页码**，与文中所写逐项比对，不一致即判 ❌
- **PubMed** → 调 NCBI E-utilities 反查，同上
- **普通链接** → HTTP 实测，区分 `200 / 反爬403 / 404 / DNS失效 / TLS证书不匹配`
- **时效戳** → 检查「核验日期」是否超出该类数据的时效窗口
- **铁律合规** → 扫描 Google Scholar 引用等违规写法

**退出码非 0 即表示档案不可交付。** 仅依赖 Python 标准库，无需 `pip install`。

秉持一个宁缺毋滥的一个做法。
   任何一条外部事实都必须带**核验日期**与**核验方式**。定稿前必须跑通 `verify.py`。
   无法被独立核验的条目，宁可删除，不得写入正文。

---

## 其他设计

1. **保证Personlization**
   系统必须拿到申请人的 **选校表** ，**个人信息调查表**和**灵魂发问**

2. **深度优先搜索**
   严格限制每次调研 3 所大学，按照 `ED I → ED II → EA → RD` 优先级有序推进，
   并在选校总表中以状态列记录进度；批次已满时拒绝追加第 4 所。
3. **给出原文引用**：
   必须给出**列有该题目的官方页面深链**（不是招生办首页），提取英文原文与字数死线，并标注适用申请周期。
   针对取消补充文书的院校，出具官方证据打标 `[免写WhySchool]`。
4. **主要查找比较小众的内容**：
   拒绝人人皆知的大楼与排名。深挖街区相关、圈内特殊传统与特定活动；


5. **文书大纲去 AI 化 (De-AI-fied Fact Blueprints)**：
   删去套话，以**纯事实 Bullet Points** 交代场景冲突、认知转变、教授文献承接与校内外落地行动。
6. **不是一站式完全放手**，申请者必须在这个report的基础上，自己再做更深一层的搜索，比如niche等网站，需要申请者自己评估之后才能决定。

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
├── references/
│   ├── sop_school_research.md       # 【程序权威源】十二步 SOP + 信源分层
│   └── verification_standards.md    # 信源核验标准
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


---

## 十二步 SOP：官网+核验

程序规范见 **[`references/sop_school_research.md`](./references/sop_school_research.md)**（工作区里会下发为 `SOP for School Research.md`）。

它回答两个不同的问题，分别由两方定义，合并成一套流程：

- **采集骨架**（读什么、按什么顺序读、每步产出什么原材料）整理自于老师提供的
  《如何做 School Research 的一封信》。官网为主，且要按固定顺序读——
  `About/Mission → Academics 课程目录 → Research 本科研究机会 → Resources/Student Life → People`。
  **课程目录要记到课号级**；**本科生研究机会要单独查**（准入时间、先修课、前人课题范例）。
- **证据标准**（哪些事实必须被证明、怎么证明）由本仓库的核验回路定义。

| 阶段 | Step | 名称 |
| :--- | :--- | :--- |
| **A 自省与选校** | 1–3 | 选校总表 → 自我调查（学习风格 / 未来倾向 / 最在乎的 3 个特质）→ 基础资料与 3 个关键词 |
| **B 官方一手穿透** | 4–9 | Prompt 逐字审计 → 建校宗旨 → **课程目录（课号级）** → **本科研究机会** → 教授文献溯源 → 社团与校园生态 |
| **C 交叉验证** | 10 | 第三方学生视角与风格匹配自检（标注主观，且必须在官网之后） |
| **D 成文与核验** | 11–12 | 5–10 个匹配点 → 因果链大纲 → Master Dossier → `verify.py` 回写 |

**一条贯穿全流程的反面清单**（出现即判无效论据）：排名高、声誉好、地理位置、
"课程范围广泛"、"师资雄厚"、官网宣传语。区别只在"具体"二字——

> 你有**这门课**（课号 `XXXX 199`）能让我学到 xxxx；
> 你有**这位导师**（姓名 xxx），方向是 yyyy，而我做的是 zzzz，我想延伸到 yyyy。

这些细节，只能来自 Step 5–9 的采集。这也是为什么 SOP 把它拆成十二步而不是一句话。

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
| **ChatGPT** | [`CODEX.md`](./agent_rules/CODEX.md) | `--platform chatgpt` | 生成 Custom Instructions 粘贴版（1500 字符硬上限，超限即中止） |
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

## Quickstart



### 0. Workflow

本项目需要Python
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
├── SOP for School Research.md            # 十二步作业规范（可点选勾选的 checklist）
├── inputs/
│   ├── 选校表.md                          # ① 必需：目标院校名单与专业诉求
│   ├── 灵魂发问.md                        # ② 必需：人格特征
│   ├── 个人信息收集表.md                   # ② 必需：基本信息
│   ├── 01_申请者画像与叙事资产总档案.md      # 由 ①② + 主文书整合而成
│   └── common_app_personal_statement.md  # 主文书定稿全文
└── reports/                              # 产出目录（按学校分文件夹）
```

工作区自带 `.gitignore`（忽略全部内容）——里面是你的个人信息，不要提交到公开仓库。

### 3. 填必需输入，然后开工

> [!IMPORTANT]
> **两样输入是必须的。缺任何一样，Agent 会直接拒绝开始**
> 不因为 Why School 的实质是回答"我是谁"：
> 没有选校表就没有检索对象；没有人格与背景，写出来的每一句都成立，
> 因而**对任何学校都不成立**。缺输入时开工，产出的不是半成品

1. `inputs/选校表.md`（**必需 ①**）—— 目标院校名单与专业诉求，至少 1 所。
2. `inputs/灵魂发问.md`（**必需 ②**，人格特征）+ `inputs/个人信息收集表.md`（**必需 ②**，基本信息）。

3. `inputs/01_申请者画像与叙事资产总档案.md` —— 把上面两份 + 主文书整合进来。两个关键节：
   - §1「主文书核心矛盾」：主文书提出了什么**未决的**问题。所有 Why School 都要成为它的续篇。
   - §2「自我调查」：学习风格 / 未来倾向 / 最在乎的 3 个大学特质。
     这三项是 Agent 检索时的**筛选标准**——没有它，官网穿透会退化成漫无目的的信息收集。
     注意必须是**可判定的**表述：「我喜欢小班」不可判定，「我在 40 人以下的研讨课里产出明显高于 200 人讲座」可判定。
4. `inputs/common_app_personal_statement.md` —— 粘贴主文书**逐字全文**（不要摘要）。
5. `00_选校总表.md` —— 锁定第一批 3 所。注意是**硬限 3 所**，Agent 会拒绝第 4 所。

### 4. 核验与交付

直接让你的agent交付就可以，会生成report

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
