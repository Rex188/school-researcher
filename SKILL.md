---
name: school-researcher
description: |
  本科申请深度选校调研、官方文书题目审计与小众学术穿透系统。
  从申请人 Common App 主文书出发，对目标大学做高颗粒度、全要素可溯源的 Why School / Why Major 深度调研。
  按 ED I → ED II → EA → RD 优先级推进，单批次严格限查 3 所；提供官方招生页深链与逐字英文题目原文；
  深挖地下先锋空间与圈内特殊传统；检索目标系所教授真实发表，必须给出永久 DOI / PubMed 直链；
  产出剔除修饰语的纯事实 Bullet-Points 文书大纲与审计级 Master Dossier。
  所有外部事实必须附核验日期，定稿前必须通过 scripts/verify.py 核验。

  Audit-grade college research skill. Produces verifiable Why School / Why Major dossiers grounded in the
  applicant's Common App essay. Batches 3 schools by ED I → ED II → EA → RD. Enforces verbatim prompts,
  niche campus culture, permanent DOI/PubMed faculty citations, and de-AI-fied factual essay blueprints.
  Every claim carries a verification date; scripts/verify.py must pass before finalizing.

  关键词: school-research, why-school, why-major, college-admissions, essay-prompts, supplemental-essays, faculty-papers, doi-verification, common-app
---

# School-Researcher: 本科申请深度选校调研与学术穿透系统

## 1. 核心使命与触发条件 (Core Mission & Triggers)

### 何时触发：
- 当用户提出"做一下 [大学名称] 的 school research"、"查一下选校表的小文书题目"、"准备写 [大学名称] 的 Why School / Why Major 文书"时触发。
- 当用户提供或维护申请选校名单，需要进行批次梳理与学术弹药库挖掘时触发。

### 核心使命：
彻底杜绝"维基百科式"的大路货信息罗列，将 School Research 打造为**文书级、可直接作为学术论据且 100% 可被第三方审计溯源的战略武器库**。

> **本 Skill 的根本设计立场**：可审计性不靠"要求模型别幻觉"来实现，而靠**独立核验回路**。
> 任何一条外部事实，都必须能被 `scripts/verify.py` 或人工点击从一手来源重新取数验证。
> 无法被独立核验的条目，宁可删除，不得写入正文。

---

## 2. 核心架构与物理隔离规范 (Directory Architecture)

所有产出必须严格遵守输入与输出的物理隔离，统一在工作区根目录下的 `SchoolResearch/` 内维护：

```
SchoolResearch/
├── 00_选校总表.md                    # 全局导航与申请批次审计总台账
├── SOP for School Research.md       # 标准操作流程规范手册
├── inputs/                          # 【输入档案库】隔离存放原始物料
│   ├── 01_申请者画像与叙事资产总档案.md   # 整合了 Common App 主文书底座的个人核心画像
│   ├── common_app_personal_statement.md# 申请人 Common App 主文书定稿英文全文
│   └── 选校表.md                      # 原始选校与专业诉求草案
└── reports/                         # 【独立调研报告库】单校独立文件夹归档
    ├── JHU_Peabody/                 # 单校独立目录
    │   └── JHU_Peabody_Master_Dossier.md # 合并文书审计与深度研报的唯一权威档案
    ├── Swarthmore/
    │   └── Swarthmore_Master_Dossier.md
    └── ...
```

---

## 3. 七大执行铁律 (Non-Negotiable Constraints)

1. **三所学校单批次轮转制 (Strict Batching)**：
   - 每次只排查或深研 3 所学校，严格遵循 `ED I → ED II → EA → RD` 的时间线与战略优先级，防止大段无序信息冲垮模型上下文。
   - 在 `00_选校总表.md` 中以**状态列 + 当前批次字段**记录进度：`[待调研] / [调研中] / [调研完成] / [已核验]`。
   - 当前批次未满 3 所时，允许追加；已满 3 所时，**必须拒绝**第 4 所，并提示用户先归档当前批次。

2. **官方文书题目逐字审计 (Verbatim Evidence)**：
   - 必须提供**列有该题目的官方页面深链**，不得只给招生办首页——首页无法定位到题目原文，等于不可核验。
   - 必须逐字提取官方**英文题目原文（Verbatim Quote）**与字数死线，并标注**适用申请周期**。
   - 若该校取消了补充文书（如 UNC），必须明确出示官方政策出处并打标 `[免写WhySchool]`。

3. **小众生态与圈内暗线穿透 (Niche Vibe & Micro-Resonance)**：
   - 严禁仅列举大众知名地标；必须检索出地下艺术场馆、非主流即兴圈子、历史建筑传统或特定通勤路线，且每个实体必须附带官方主页、媒体报道或历史报道链接。
   - **必须核实该实体当前是否仍在运营**。已歇业/已迁址的场所应如实标注，或改用仍在营业的替代实体。

4. **文献级学术链接规范 (Permanent DOI / PubMed Only)**：
   - 教授著作与论文必须真实在册。
   - **绝对禁止使用 Google Scholar 动态搜索链接 (`scholar.google.com/scholar?q=...`)**，以防触发人机风控拦截。
   - **禁止把 ResearchGate、Academia.edu 等第三方转载页当作"永久直链"**：它们同样是动态页、同样会被反爬拦截，且不是一手来源。
   - 必须统一提供**官方永久 DOI 解析直链 (`https://doi.org/...`)**、**PubMed 收录直链 (`https://pubmed.ncbi.nlm.nih.gov/...`)**、**政府/国家实验室官方归档**或**出版社官方专页直链**。
   - 引用文献必须给出**准确的卷、期、页码**，并以 API 反查结果为准，不得凭印象填写。

5. **文书大纲去 AI 化 (De-AI-fied Bullet Points)**：
   - 删去所有抒情、比喻与感性形容词，杜绝"灵魂共鸣"、"震撼交响"等空洞套话。
   - 严格以**纯建设性事实要点（Bullet Points）**拆解段落：明确具体事实冲突、具体行动结论、具体导师论文观点对接、具体校内外落地项目与字数建议。

6. **主文书认知底色互文 (Hermeneutic Alignment)**：
   - 深入结合 `inputs/01_申请者画像与叙事资产总档案.md` 中提炼的 Common App 主文书哲学核心，所有 Why 论据必须承接主文书未决的痛点，形成连续的精神脉络。

7. **核验回路铁律 (Verification Loop)** —— 本 Skill 存在的根基：
   - 每一条外部事实（题目、链接、教授任职、文献卷期页、资助项目）都必须带**核验日期**与**核验方式**。
   - **定稿前必须运行 `python3 scripts/verify.py`，退出码非 0 不得交付。**
   - 时效分级（不同数据腐朽速度不同）：
     | 数据类型 | 时效窗口 |
     | :--- | :--- |
     | DOI / PubMed 文献 | 永久 |
     | 教授任职、招生政策 | 约 180 天 |
     | 文书题目、字数限制、DDL | **单申请季，跨周期必须全部重查** |
     | 场馆、节庆、学生项目、资助 | 约 365 天 |
   - **教授任职必须单独核实**：写 Why School 前确认该教授在本申请季确实属于目标院校编制。把外校教授当作目标院校的文书锚点是硬伤。
   - **不得把 ⚠️「无法判定」当成 ❌「来源失效」**：反爬 403/429、HEAD 误答 404、超时
     都不构成"来源失效"的证据。把工具自身的故障说成引用有问题，会导致删掉正确的引用，
     比不核验更糟。详见 `references/verification_standards.md` §0.1。

---

## 4. 九步全流程执行 SOP (Standard Operating Procedure)

- **Step 1: 确定选校名单并维护总表**：在 `00_选校总表.md` 中按批次锁定专业与 DDL，写入状态列。
- **Step 2: 建立个人叙事资产库**：萃取「灵魂发问」+「信息采集表」+「Common App 主文书」，归档至 `inputs/01_申请者画像与叙事资产总档案.md`。
- **Step 3: 官方 Essay Prompt 审计 (Prompt Triage)**：每批限查 3 所，出具官方深链、原文、字数与适用周期。
- **Step 4: 校园生态与微观共鸣检索 (Vibe & Micro-Resonance)**：挖掘小众先锋空间、圈内传统与通勤意象，附媒体报道源，并核实当前运营状态。
- **Step 5: 院系交叉平台与专项资助挖掘 (Programs & Grants)**：定位核心交叉中心、硬件实验室与学生专属自主基金，确认当季仍在运行。
- **Step 6: 教授学术图谱与文献级检索 (Faculty & Publications)**：锁定 2-3 位导师，**核对其当前任职单位**，检索真实著作与论文，给出永久 DOI / PubMed / 出版社直链及准确卷期页。
- **Step 7: Why 文书论证因果链与事实大纲 (Narrative Logic Chain)**：编写去 AI 化的三段式事实与学术对接 Bullet Points 大纲。
- **Step 8: 交付独立单校 Master Dossier**：在 `reports/[School]/` 下生成终版档案，每条外部事实附核验日期。
- **Step 9: 核验与回写**：先跑 `python3 scripts/verify.py --self-test` 确认核验器本身不误判，再运行 `python3 scripts/verify.py reports/[School]/`；退出码为 0 后，向选校总表回写状态 `[已核验]`。若存在 ❌ 项，修正后重跑，直至通过；⚠️ 项须人工点击确认并改写「核验方式」列。
