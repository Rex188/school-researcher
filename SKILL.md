---
name: school-researcher
description: |
  本科申请深度选校调研、官方文书题目审计与小众学术穿透系统。
  从申请人 Common App 主文书出发，对目标大学做高颗粒度、全要素可溯源的 Why School / Why Major 深度调研。
  按 ED I → ED II → EA → RD 优先级推进，单批次严格限查 3 所；提供官方招生页深链与逐字英文题目原文；
  十二步穿透官网：建校宗旨、课程目录（课号级）、本科生研究机会、院系平台与专项基金；
  深挖地下先锋空间与圈内特殊传统；检索目标系所教授真实发表，必须给出永久 DOI / PubMed 直链；
  产出剔除修饰语的纯事实 Bullet-Points 文书大纲与审计级 Master Dossier。
  所有外部事实必须附核验日期，定稿前必须通过 scripts/verify.py 核验。

  Audit-grade college research skill. Produces verifiable Why School / Why Major dossiers grounded in the
  applicant's Common App essay. Batches 3 schools by ED I → ED II → EA → RD. Twelve-step official-site
  penetration: mission statements, course catalogs, undergraduate research, niche campus culture, permanent
  DOI/PubMed faculty citations, and de-AI-fied factual essay blueprints. Every claim carries a verification date;
  scripts/verify.py must pass before finalizing.

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
│   ├── 选校表.md                      # ① 必需：目标院校名单与专业诉求（至少 1 所）
│   ├── 灵魂发问.md                    # ② 必需：人格特征
│   ├── 个人信息收集表.md               # ② 必需：基本信息
│   ├── 01_申请者画像与叙事资产总档案.md   # 由 ①② + 主文书整合而成的核心画像
│   └── common_app_personal_statement.md# 申请人 Common App 主文书定稿英文全文
└── reports/                         # 【独立调研报告库】单校独立文件夹归档
    ├── JHU_Peabody/                 # 单校独立目录
    │   └── JHU_Peabody_Master_Dossier.md # 合并文书审计与深度研报的唯一权威档案
    ├── Swarthmore/
    │   └── Swarthmore_Master_Dossier.md
    └── ...
```

工作区无需手工搭建，骨架已随仓库提供：

```bash
./install.sh --workspace ~/SchoolResearch
```

它会生成上述目录、`00_选校总表.md`、`inputs/` 下三份档案的**带说明模板**，
以及 `SOP for School Research.md`（自 `references/sop_school_research.md` 复制而来，
已存在则不覆盖），并写入一个忽略全部内容的 `.gitignore`——
工作区含申请人个人信息，不得入库。

若工作区尚未建立，先执行此命令，再开始 Step 1。

---

## 3. 八大执行铁律 (Non-Negotiable Constraints)

1. **输入门槛：两样缺一不可，缺则拒绝 (Input Gate)** —— 本条排在第一位，因为它是准入条件：
   - **必需两样输入**（缺任何一样都不开工）：
     ① **选校表**（`inputs/选校表.md`）：目标院校名单与专业诉求，**至少 1 所**；
     ② **「灵魂发问」（人格特征）+「个人信息收集表」（基本信息）**
     （`inputs/灵魂发问.md` + `inputs/个人信息收集表.md`）。
   - **未提供即拒绝，不得开工。** 不得用通用模板、常识或推测替代，不得"先做着看"，
     不得用一份漂亮但通用的档案充数。只输出一句话：**缺哪一份、要补什么**。
   - **为什么这条排第一**：Why School 的实质是回答"我是谁"，不是"这所学校有多好"。
     没有 ①，就没有检索对象；没有 ②，写出来的每一句都成立，因而**对任何学校都不成立**——
     那不叫调研，叫把招生官听了上千遍的套话重排一遍。
     **缺输入时开工，产出的不是半成品，是负资产：它看起来像成品。**

2. **三所学校单批次轮转制 (Strict Batching)**：
   - 每次只排查或深研 3 所学校，严格遵循 `ED I → ED II → EA → RD` 的时间线与战略优先级，防止大段无序信息冲垮模型上下文。
   - 在 `00_选校总表.md` 中以**状态列 + 当前批次字段**记录进度：`[待调研] / [调研中] / [调研完成] / [已核验]`。
   - 当前批次未满 3 所时，允许追加；已满 3 所时，**必须拒绝**第 4 所，并提示用户先归档当前批次。

3. **官方文书题目逐字审计 (Verbatim Evidence)**：
   - 必须提供**列有该题目的官方页面深链**，不得只给招生办首页——首页无法定位到题目原文，等于不可核验。
   - 必须逐字提取官方**英文题目原文（Verbatim Quote）**与字数死线，并标注**适用申请周期**。
   - 若该校取消了补充文书（如 UNC），必须明确出示官方政策出处并打标 `[免写WhySchool]`。

4. **小众生态与圈内暗线穿透 (Niche Vibe & Micro-Resonance)**：
   - 严禁仅列举大众知名地标；必须检索出地下艺术场馆、非主流即兴圈子、历史建筑传统或特定通勤路线，且每个实体必须附带官方主页、媒体报道或历史报道链接。
   - **必须核实该实体当前是否仍在运营**。已歇业/已迁址的场所应如实标注，或改用仍在营业的替代实体。

5. **文献级学术链接规范 (Permanent DOI / PubMed Only)**：
   - 教授著作与论文必须真实在册。
   - **绝对禁止使用 Google Scholar 动态搜索链接 (`scholar.google.com/scholar?q=...`)**，以防触发人机风控拦截。
   - **禁止把 ResearchGate、Academia.edu 等第三方转载页当作"永久直链"**：它们同样是动态页、同样会被反爬拦截，且不是一手来源。
   - 必须统一提供**官方永久 DOI 解析直链 (`https://doi.org/...`)**、**PubMed 收录直链 (`https://pubmed.ncbi.nlm.nih.gov/...`)**、**政府/国家实验室官方归档**或**出版社官方专页直链**。
   - 引用文献必须给出**准确的卷、期、页码**，并以 API 反查结果为准，不得凭印象填写。

6. **文书大纲去 AI 化 (De-AI-fied Bullet Points)**：
   - 删去所有抒情、比喻与感性形容词，杜绝"灵魂共鸣"、"震撼交响"等空洞套话。
   - 严格以**纯建设性事实要点（Bullet Points）**拆解段落：明确具体事实冲突、具体行动结论、具体导师论文观点对接、具体校内外落地项目与字数建议。

7. **主文书认知底色互文 (Hermeneutic Alignment)**：
   - 深入结合 `inputs/01_申请者画像与叙事资产总档案.md` 中提炼的 Common App 主文书哲学核心，所有 Why 论据必须承接主文书未决的痛点，形成连续的精神脉络。

8. **核验回路铁律 (Verification Loop)** —— 本 Skill 存在的根基：
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
   - **信源分层，不是分可信度，是分权限**：Wikipedia 与 Fiske Guide 属**线索层**，
     只能用于下探，**不得直接写入档案作为论据**；第三方评价网站（Niche / Unigo /
     College Confidential / RateMyProfessors）属**主观层**，必须标注 `第三方主观`，
     不得单独支撑任何事实性论断，且**只能在官网穿透之后使用**。
     详见 `references/verification_standards.md` §7。

---

## 4. 十二步全流程执行 SOP (Standard Operating Procedure)

> **逐步作业规范（做什么 / 产出什么 / 核验要求 / 常见错误）见 [`references/sop_school_research.md`](./references/sop_school_research.md)。**
> 本节是可执行索引：按此推进，需要细节时回到该文件。
>
> 采集骨架整理自指导老师提供的《如何做 School Research 的一封信》，已与本仓库的核验回路合并——
> 老师定义「官网按什么顺序读、读哪几页、产出什么原材料」，本仓库定义「哪些事实必须被证明、怎么证明」。

> **开工前置检查（铁律 1）**：先确认 `inputs/选校表.md` 与
> `inputs/灵魂发问.md` + `inputs/个人信息收集表.md` 均已填写。
> **缺失即拒绝，不得开工，不得用推测或通用模板替代。** 只回答缺哪一份。

### 阶段 A｜自省与选校（Step 1–3）

- **Step 1: 确定选校名单并维护总表**：在 `00_选校总表.md` 中按批次锁定专业与 DDL，写入状态列。
- **Step 2: 自我调查与叙事资产库**：先向内看再向外看。产出**学习风格**（大课/小班、讲座/讨论）、
  **未来倾向**（学术研究 / 就业 / 交叉探索）、**最在乎的 3 个大学特质**，叠加主文书的**未决问题**，
  归档至 `inputs/01_申请者画像与叙事资产总档案.md`。这三组自述是后续检索的**筛选标准**。
- **Step 3: 基础资料概览与学校关键词**：以 Wikipedia 与 Fiske Guide 建立整体印象（地理位置、历史、学风），
  产出该校最突出的 **3 个关键词**。**本层属线索层，不得直接写入档案作为论据**，必须回溯官方来源复核。

### 阶段 B｜官方一手材料穿透（Step 4–9）

- **Step 4: 官方 Essay Prompt 审计 (Prompt Triage)**：每批限查 3 所，出具官方深链、逐字原文、字数与适用周期。
- **Step 5: 建校宗旨与 About/Mission 契合度**：逐字摘抄官方 **mission statement**（**不得引用第三方转述**），
  回答「它的哪一句话解释了我为什么要做我正在做的事」。宗旨是筛选器，不是可堆砌的漂亮话。
- **Step 6: 课程目录逐课穿透 (Course Catalog)**：进入目标系所 `Undergraduate` 课程目录，
  **课号级**记录 2–3 门特色课程（与同专业在其他学校开课不同者）与 syllabus 链接，附吸引理由。
  **必须区分本科课程与研究生课程**——引用一门本科生选不上的课是硬伤。
- **Step 7: 本科生研究机会与跨学科平台 (Undergraduate Research)**：查针对本科生的研究项目、
  准入**时间与资格要求**（含先修课、国籍、考核）、在读生已完成课题范例；
  另查跨学科中心、硬件实验室与学生专项基金。**必须确认当季仍在运行**。
- **Step 8: 教授学术图谱与文献级溯源 (Faculty & Publications)**：锁定 2-3 位导师，
  **核对其当前任职单位**，检索真实著作与论文，给出永久 DOI / PubMed / 出版社直链及准确卷期页。
- **Step 9: 学生社团、校园文化与城市微观生态 (Student Life & Niche Ecology)**：学术性/服务性社团、
  校园特殊传统与体育、小众先锋空间与通勤动线；每个实体附官方或媒体报道源，并**核实当前运营状态**。

### 阶段 C｜第三方交叉验证（Step 10）

- **Step 10: 第三方学生视角与风格匹配自检**：参考 Niche / Unigo / College Confidential 等，
  记录 2 条学生体验与该校「典型学生」画像关键词，做**风格匹配自检**。
  **必须在 Step 4–9 之后执行**（先刷论坛会被其偏见锚定）；必须标注 `第三方主观`，
  **不得单独支撑任何事实性论断**，与官网冲突时以官网为准。

### 阶段 D｜成文与核验（Step 11–12）

- **Step 11: 匹配点清单与 Why 因果链大纲 (Narrative Logic Chain)**：**先列 5–10 个吸引点**
  （每条 = 具体名词 + 与我何干 + 可回溯的 Step 编号），**再**压缩为去 AI 化的三段式事实与学术对接
  Bullet Points 大纲。写不满 5 条说明前面查得不够；回溯不到的吸引点宁可删除。
- **Step 12: 交付 Master Dossier 与核验回写**：在 `reports/[School]/` 下生成终版档案，每条外部事实附核验日期。
  先跑 `python3 scripts/verify.py --self-test` 确认核验器本身不误判，再运行
  `python3 scripts/verify.py reports/[School]/ --html reports/[School]/核验报告.html`；
  退出码为 0 后，向选校总表回写状态 `[已核验]`。若存在 ❌ 项，修正后重跑，直至通过；
  ⚠️ 项须人工点击确认并改写「核验方式」列。HTML 报告随档案一并交付，供人工复核。
