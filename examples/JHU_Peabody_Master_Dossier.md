# 院校文书审计与深度研报：约翰霍普金斯大学皮博迪音乐学院 (JHU Peabody)

> [!WARNING]
> **本示例中的申请人信息（姓名、高中、活动经历、项目名称）均为虚构演示数据。**
> 院校、教授、文献、场馆等外部事实均为真实公开信息，每条附核验日期与核验方式，
> 可点击核验，也可用 `python3 scripts/verify.py examples/` 复现核验结果。

> **目标院校**：Johns Hopkins University (Peabody Institute & Homewood Campus)  
> **申请轮次**：ED I（截止日期：2026-11-01）  
> **申请周期**：2026–27  
> **申请项目**：Peabody-Homewood Double Degree（5年制双学位）  
> - Peabody 端：计算机音乐（BM in Computer Music / Music Technology）  
> - Homewood 端：计算机科学 / 认知科学（BA/BS in Computer Science / Cognitive Science）  
> **最后核验**：2026-09-29  
> **核验基准**：官方招生页深链 / 永久 DOI / PubMed / 官方机构页面

---

## 1. 官方文书 Prompt 与字数限制

- **题目出处**：[JHU 招生办官方页面：Advice For Crafting Your Supplemental Essay](https://apply.jhu.edu/hopkins-insider/advice-for-crafting-your-supplemental-essay/)
- **字数上限**：350 词
- **适用申请周期**：2026–27
- **英文原文 (Verbatim Quote)**：
  > "At Johns Hopkins, community is built through dialogue, collaboration, and a willingness to engage across differences. Whether on campus or in the broader world, community depends on bridge builders who can listen to differing perspectives, challenge their own assumptions, or work together toward shared goals. Drawing on your own experiences, what have you learned about engaging across differences and how has it shaped the way you think about building bridges, enhancing community, and working with others?"
- **考核重点**：拒绝抽象议论，必须提供申请人作为 Bridge Builder 处理微观差异、打破自身既定假设的具体事实证据链。
- **核验方式**：官方页面直接抓取（题面含 "(350-word limit)"）｜ **核验日期**：2026-09-29

> [!IMPORTANT]
> **JHU 几乎每季更换补充文书题目。** 上一季的题目是"人生中一个重要的第一次"，
> 本季已替换为上述 Bridge Builder 题目。**跨申请季必须重新核验，旧草稿不可直接沿用。**
>
> 另注：JHU 本科申请**只有这一篇**补充文书（350 词），无独立的 Why Hopkins 题。
> 因此本文承担了全部"Why Hopkins"的表达功能，学术对接必须写实。

---

## 2. 校园小众生态与城市暗线

### A. The Red Room 与 High Zero Festival（巴尔的摩非主流即兴实验音乐）

- **实体载体**：
  - [Normal's Books & Records](https://normals.com/) 地下室 [The Red Room](https://redroom.org/)（地址：425 E 31st St，距 Homewood 校区步行约 5 分钟）
  - [Baltimore Theatre Project](https://www.theatreproject.org/)（45 West Preston Street）
- **背景与可信源**：
  - [High Zero Foundation 官方 About 页](https://highzero.org/2026_site/about/)
  - [High Zero Foundation 机构档案（马里兰州艺术委员会）](https://msac.org/directory/organizations/high-zero-foundation)
- **核验方式**：HTTP 实测（normals.com / redroom.org / theatreproject.org / highzero.org 均 200）｜ **核验日期**：2026-09-29
- **文书结合点**：
  - High Zero 发源于 The Red Room——1996 年起在该书店地下室持续举办即兴演出，2002 年注册为 501(c)3 基金会，自 1999 年起每年举办 High Zero 音乐节，2001 年起固定在 Theatre Project 场地。
  - 区别于传统古典音乐会，这是全球无规则即兴（Non-idiomatic Improvised Music）重镇，长期与 Peabody 师生合作实验演出。
  - 承接主文书关于自制手腕传感器"放弃预设规则、留出空白界面"的实践，作为课外接入本地先锋声音社群的切入点。

### B. Griswold Hall 万圣节午夜管风琴即兴传统

- **实体载体**：
  - [Peabody Griswold Hall 官方介绍](https://peabody.jhu.edu/about/campuses-halls/griswold-hall/)
- **背景与可信源**：
  - 官方院系页（配备 1960 年代 3,000 管 Holtkamp 机械追踪管风琴）
- **核验方式**：⚠️ `反爬待人工`——peabody.jhu.edu 对自动请求返回 403，**须人工点击确认该传统当季仍在举办，以及管风琴规格描述准确** ｜ **核验日期**：2026-09-29
- **文书结合点**：
  - 学生在大厅黑暗中利用物理声学风管即兴为无声默片配乐，展示对该校特定声学空间历史与学生圈内传统的具象认知。

> [!CAUTION]
> 此条目**未经自动核验**。学生年度传统这类事实极易过期（停办、改期、换场地）。
> 在写入正式文书前必须由人工确认——未经确认不得直接使用。

### C. 穿梭于 Station North 艺术区的校车路线

- **实体载体**：
  - [JHU 官方校车系统 (Homewood-Peabody-JHMI Shuttle)](https://ts.jhu.edu/Shuttles/)
  - [Station North Arts & Entertainment District 官网](https://www.stationnorth.org/)
- **核验方式**：stationnorth.org HTTP 200；ts.jhu.edu ⚠️ `反爬待人工` ｜ **核验日期**：2026-09-29
- **文书结合点**：
  - 校车沿 Charles Street 穿过 Station North 艺术区，连接 Mount Vernon（古典）与 Charles Village（工科）。可作为跨越两个学科校区的具象场景。

---

## 3. 跨学科院系机构与专项基金

### A. Center for Music and Medicine (CMM)

- **官方主页**：[JHU 医学院音乐与医学中心](https://www.hopkinsmedicine.org/center-for-music-and-medicine)
- **负责人**：Dr. Alexander Pantelyat（神经内科副教授）
- **针对性课题**：鼓圈律动对帕金森步态障碍的干预；职业乐手手部局灶性肌张力障碍
- **核验方式**：⚠️ `反爬待人工`（403）｜ **核验日期**：2026-09-29

### B. Peabody Computer Music Studios (CMS)

- **官方主页**：[Peabody 计算机音乐系与工作室](https://peabody.jhu.edu/academics/instruments-areas-of-study/computer-music/)
- **硬件配置**：多声道环绕立体声工作站、模块化合成器机架、硬件传感交互实验室
- **核验方式**：⚠️ `反爬待人工`（403）｜ **核验日期**：2026-09-29

### C. 学生专项资助

- **官方主页**：[Peabody LAUNCHPad（职业与创业办公室）](https://peabody.jhu.edu/life-at-peabody/career-services/)
- **资助性质**：⚠️ **待核实**
- **核验方式**：❌ 未能核实 ｜ **核验日期**：2026-09-29

> [!CAUTION]
> **本条为反面示例。** 原稿声称存在"单项数千美元的 Peabody LaunchPad 学生创新资助"，
> 但既无法从官方页面确认该项目名称，也无法确认资助额度与当季是否仍在运行。
>
> 资助项目名称与额度每学年都可能变动。**在得到官方页面证实之前，此条不得写入正文。**
> 这正是 `verify.py` 要拦住的那类问题：听起来合理、但没有任何一手来源支撑的断言。

---

## 4. 教授核心文献与永久学术溯源索引

> **铁律**：禁止 Google Scholar 动态搜索链接；禁止把 ResearchGate 等第三方转载页当作"永久直链"。

### A. Margaret Schedel（**Stony Brook University** 音乐系副教授 / IACS 核心教员；同时在 Peabody 教授计算机音乐）

> [!IMPORTANT]
> **任职单位已核正。** Schedel 的主要编制在 **Stony Brook University**（音乐系副教授、
> 艺术系主任、计算机音乐联合主任、IACS 核心教员）。她**同时在 Peabody 教授计算机音乐作曲**，
> 并联合执导 Peabody Laptop Ensemble，本人亦为 Peabody 计算机音乐作曲硕士（'01）。
>
> 因此以她作为 Peabody 的文书锚点是**成立的**，但**不可将她表述为"Peabody 全职教授"**——
> 招生官一查即知。准确表述应为"在 Peabody 授课的 Stony Brook 副教授"，
> 或更稳妥地改以 Peabody 全职教授为锚点（见 B）。

1. **会议论文（替代原稿中无法核实的专著）**:
   - Beattie, E., & Schedel, M. (2018). *"Inscribing Bodies: Notating Gesture."* *Lecture Notes in Computer Science*, Springer, 273–283.
   - [永久 DOI 直链](https://doi.org/10.1007/978-3-030-01692-0_19)
   - *核心要点*：讨论如何为"身体动作"建立可传递的记谱系统——直接对应申请人"保留手腕生理微动、而非将其量化掉"的技术主张。
   - **核验方式**：`verify.py` DOI 反查（Springer, 2018, 273–283）｜ **核验日期**：2026-09-29

2. **权威期刊论文**:
   - Helmuth, M., & Schedel, M. (2022). *"Links between sonification and generative music."* *Interdisciplinary Science Reviews*, 47(2), 215–242.
   - [永久 DOI 直链](https://doi.org/10.1080/03080188.2022.2035106)
   - *核心要点*：探讨数据声音化与生成算法的边界，指出过度追求算法确定性往往剥夺艺术主体的能动性。
   - **核验方式**：`verify.py` DOI 反查（Taylor & Francis, 47(2), 215–242, 2022）｜ **核验日期**：2026-09-29

3. **著作章节**:
   - Green, S., & Schedel, M. (2022). *"Cynosuric Bodies."* In *The Body in Sound, Music and Performance*, Focal Press, 196–213.
   - [永久 DOI 直链](https://doi.org/10.4324/9781003008217-19)
   - **核验方式**：`verify.py` DOI 反查（Focal Press, 2022, 196–213）｜ **核验日期**：2026-09-29

4. **学者官方页面**:
   - [Stony Brook 音乐系教职页](https://www.llrc.stonybrook.edu/commcms/art/people/faculty-staff/margaret-schedel) ｜ [IACS 主页](https://iacs.stonybrook.edu/people/_faculty/margaret-schedel.php) ｜ [ORCID 0000-0001-6897-9866](https://orcid.org/0000-0001-6897-9866)

> [!CAUTION]
> **原稿此处的引用已废弃。** 原稿引用 Schedel & Perry 专著 *Machines We Imagine*
> (Taylor & Francis, 2026)，唯一证据是 `schedel.net/research/`（刻意不写成可点击链接）。
> 核验结果：**该域名已易主**——其现行 TLS 证书归属 `secretshame.ca`，与 Schedel 无关；
> 且在 CrossRef、OpenLibrary 及公开检索中均查无此书。
> 该条引文**不可验证**，已替换为经 DOI 反查确认的在册文献。

### B. Geoffrey Wright & McGregor Boyle（Peabody 计算机音乐）

1. **ICMC 核心论文**:
   - Wright, G., & Boyle, M. (2015). *"Peabody Computer Music: 46 Years of Looking to the Future."* *International Computer Music Conference Proceedings*.
   - **永久链接**：⚠️ **无 DOI**。ICMC 论文集未注册 DOI，需经 ICMC 官方档案库人工检索定位。
   - **核验方式**：❌ 未找到可自动核验的永久直链（原稿使用的 `smartech.gatech.edu` 已失效——该域名现为 CNAME 指向不解析的 `smartech.library.gatech.edu`；ResearchGate 页面则属第三方转载，按铁律不可作为"永久直链"） ｜ **核验日期**：2026-09-29

> [!NOTE]
> **会议论文的处理原则。** 并非所有真实存在的论文都有 DOI。遇到无 DOI 的会议论文，
> 正确处理是**如实标注"无 DOI，需人工核验"**，而不是退而使用第三方转载页充数——
> 后者会让人误以为来源已被核验。此条即为此原则的演示。

2. **硬件交互项目**:
   - *The Virtual Orchestra System*（红外传感指挥棒实时触发声音，时代广场千禧年实演）
   - **核验方式**：⚠️ `反爬待人工`（pages.jh.edu 返回 403）｜ **核验日期**：2026-09-29

### C. Dr. Alexander Pantelyat（JHU 医学院神经科 / CMM 主任）

1. **打击乐干预临床论文**:
   - Pantelyat, A., Syres, C., Reichwein, S., & Willis, A. (2016). *"DRUM-PD: The use of a drum circle to improve the symptoms and signs of Parkinson's disease (PD)."* *Movement Disorders Clinical Practice*, 3(3), 243–249.
   - [永久 DOI 直链](https://doi.org/10.1002/mdc3.12269) ｜ [PubMed 收录 (PMID: 27340683)](https://pubmed.ncbi.nlm.nih.gov/27340683/)
   - **核验方式**：`verify.py` DOI + PubMed 双重反查（均为 3(3), 243–249, 2016）｜ **核验日期**：2026-09-29

> [!CAUTION]
> **原稿此处的卷期页码是错的。** 原稿写作 `3(6), 561–567`，
> CrossRef 与 PubMed 一致返回 **`3(3), 243–249`**（在线 2015-12-21，纸本 2016 年 5 月）。
> 论文本身真实存在，但错误页码属于**事实性编造**——这正是"论文是真的"最容易掩盖的问题。

---

## 5. 文书结构大纲 (纯建设性事实要点，删去全部修饰语)

**题目要求**：350 词，围绕"Bridge Builder"展开。  
**写作策略**：三段式递进，直接交代事实与研究对应点。

### 段落 1：事实冲突与认知破壁 (目标: 90–100 词)
- **事实切入**：在校内创客社团与音乐社联合举办的期末展演中担任技术统筹（虚构经历）。
- **具体冲突**：灯光与音效控制系统要求毫秒级固定时间码，与现场乐手即兴延展的需求发生摩擦。
- **行动与结论**：
  - 未采取强制统一时间表的简单做法。
  - 设计弹性缓冲触发机制，在控制序列中保留未量化的触发点。
  - 核心领悟：构建桥梁不是消灭差异，而是建立能兼容阻抗与摩擦的协作接口。

### 段落 2：跨学科研究对接 (目标: 160–180 词)
- **学科桥梁**：将上述反思延伸至学术路径——从纯工程方向转向 CS + 音乐科技交叉领域。
- **自身项目**：自制手腕传感器原型（虚构，代号 Cadence）中面临的矛盾——算法越精确，越容易消除手腕击打的非线性微动。
- **JHU 资源对接**：
  - 选择 **Peabody-Homewood Double Degree**，利用校车往返于两个校区。
  - 承接 **Margaret Schedel** 关于"为身体动作建立记谱系统"的研究（*Inscribing Bodies: Notating Gesture*, 2018），探讨在交互界面中保留手腕生理抖动的算法机制。
  - 结合 **Center for Music and Medicine**（Pantelyat 团队关于打击乐对帕金森及手部肌张力障碍的研究），探究神经运动与声音反馈的临床机制。

### 段落 3：社群落地与行动计划 (目标: 70–80 词)
- **校内行动**：申报校级学生创新项目，推进软硬件交互乐器原型。
- **校外连结**：走出学院封闭空间，将自研原型带至 **The Red Room (Normal's Books & Records)** 及 **High Zero Festival** 参与非预设即兴实验。
- **总结收尾**：以技术与声学物理性的平衡，充当 Homewood 严密工程与 Peabody 艺术实践之间的常态化联络人。

---

## 6. 审计与可溯源文献总表

| 要素 | 检索与证明源 | 核验方式 | 核验日期 |
| :--- | :--- | :--- | :--- |
| 补充题目与 350 词限制 | [apply.jhu.edu 官方页](https://apply.jhu.edu/hopkins-insider/advice-for-crafting-your-supplemental-essay/) | 官方页面 | 2026-09-29 |
| 双学位申请规程 | Common App 勾选 + Peabody Slate 作品集 | ⚠️ 待人工 | 2026-09-29 |
| The Red Room | [redroom.org](https://redroom.org/) | HTTP 200 | 2026-09-29 |
| Normal's Books & Records | [normals.com](https://normals.com/) | HTTP 200 | 2026-09-29 |
| High Zero Foundation | [官方 About 页](https://highzero.org/2026_site/about/) | HTTP 200 | 2026-09-29 |
| Baltimore Theatre Project | [theatreproject.org](https://www.theatreproject.org/) | HTTP 200 | 2026-09-29 |
| Station North 艺术区 | [stationnorth.org](https://www.stationnorth.org/) | HTTP 200 | 2026-09-29 |
| JHU 校车系统 | [ts.jhu.edu](https://ts.jhu.edu/Shuttles/) | ⚠️ 反爬待人工 | 2026-09-29 |
| Griswold Hall 管风琴 | [Peabody 官方页](https://peabody.jhu.edu/about/campuses-halls/griswold-hall/) | ⚠️ 反爬待人工 | 2026-09-29 |
| Schedel 任职单位 | [Stony Brook 教职页](https://www.llrc.stonybrook.edu/commcms/art/people/faculty-staff/margaret-schedel) ｜ [ORCID](https://orcid.org/0000-0001-6897-9866) | 官方页面 | 2026-09-29 |
| Schedel 论文 (2018) | *Inscribing Bodies: Notating Gesture* ([DOI](https://doi.org/10.1007/978-3-030-01692-0_19)) | DOI 反查 | 2026-09-29 |
| Schedel 论文 (2022) | *Links between sonification and generative music* ([DOI](https://doi.org/10.1080/03080188.2022.2035106)) | DOI 反查 | 2026-09-29 |
| Schedel 著作章节 (2022) | *Cynosuric Bodies* ([DOI](https://doi.org/10.4324/9781003008217-19)) | DOI 反查 | 2026-09-29 |
| Wright ICMC 论文 (2015) | 无 DOI，需人工检索 ICMC 官方档案 | ❌ 未核实 | 2026-09-29 |
| Pantelyat 论文 (2016) | *DRUM-PD* ([DOI](https://doi.org/10.1002/mdc3.12269) / [PubMed](https://pubmed.ncbi.nlm.nih.gov/27340683/)) | DOI + PMID 反查 | 2026-09-29 |
| CMM 机构 | [hopkinsmedicine.org](https://www.hopkinsmedicine.org/center-for-music-and-medicine) | ⚠️ 反爬待人工 | 2026-09-29 |
| Peabody 学生资助 | — | ❌ **未能核实，不得写入正文** | 2026-09-29 |
