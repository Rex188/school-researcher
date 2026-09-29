#!/usr/bin/env python3
"""
verify.py — 审计级引文核验器 (School-Researcher)

解析调研 dossier 中的所有链接，逐条独立核验：

  · DOI       → CrossRef API 反查标题/作者/卷期页，与文中所写逐项比对
  · PubMed    → NCBI E-utilities 反查，同上
  · 普通链接  → HTTP 实测，区分 200 / 反爬 403 / 404 / DNS 失效
  · 时效戳    → 检查「核验日期」是否超过阈值

设计立场一：不信任 dossier 里的任何自述（如"所有文献均经核验"），
            一律回到一手数据源重新取数。文中所写与 API 返回值不一致即判 ❌。

设计立场二：绝不把**本机网络故障**报成「源失效」。
            一个因为本机断网就宣布"你引用的论文页面不存在"的工具，
            比没有工具更危险。因此网络类异常一律降级为 ⚠️ 无法判定，
            且核验前先做联网自检，自检不过直接中止。

用法:
    python3 scripts/verify.py                  # 扫描 examples/ 与 reports/
    python3 scripts/verify.py path/x.md ...    # 指定文件
    python3 scripts/verify.py --json           # 机器可读（CI 用）
    python3 scripts/verify.py --strict         # WARN 也算失败（CI 保守模式）
    python3 scripts/verify.py --max-age 180    # 时效阈值，默认 365 天
    python3 scripts/verify.py --offline        # 只做格式与时效检查，不发网络请求
    python3 scripts/verify.py --force          # 联网自检失败时仍然继续

退出码:
    0 = 无 ❌ 级问题
    1 = 存在 ❌（可直接用于 CI）
    2 = 联网自检未通过而中止（此时任何「链接失效」结论都不可信）

环境变量:
    VERIFY_CONTACT  CrossRef polite pool 的联络标识（默认 school-researcher-verify）
    http_proxy / https_proxy / no_proxy  按标准语义生效

仅依赖 Python 标准库。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html import escape as esc

# ---------------------------------------------------------------- 配置

CONTACT = os.environ.get("VERIFY_CONTACT", "school-researcher-verify")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 15
DEFAULT_MAX_AGE_DAYS = 365

# 文书题目/DDL 每申请季必变，给更短的容忍窗口
PROMPT_MAX_AGE_DAYS = 180

OK, WARN, FAIL = "ok", "warn", "fail"

# ---------------------------------------------------------------- 正则

# 排除反引号与中日韩标点：避免把中文句子里的句号、以及被引号包裹的 URL 一起吞掉
URL_RE = re.compile(r"https?://[^\s)\"'<>\]`。，、；：？！（）【】《》…]+")
DOI_IN_URL_RE = re.compile(r"(?:doi\.org/|doi:)(10\.\d{4,9}/[^\s)\"'<>,;]+)", re.I)
# 不限制位数：pubmed.ncbi.nlm.nih.gov/<数字>/ 一律交给 E-utilities 判定。
# 写死 6-9 位有两个坑：超长的会被截断成前 9 位反查到**另一个真实 PMID**；
# 而够不到 6 位的会退化成普通网页检查——NCBI 对不存在的条目返回 200 软 404，
# 于是编造的 ID 反而报「通过」。交给 API 判定才是唯一可靠的做法。
PMID_IN_URL_RE = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", re.I)

# "47(2), 215–242" / "3(3), 243-249" / "12, 100–110"
CITE_RE = re.compile(
    r"(?<![\d.])"
    r"(?P<vol>\d{1,4})"
    r"(?:\s*\(\s*(?P<iss>[^)\s]{1,6})\s*\))?"
    r"\s*[,:]\s*"
    r"(?P<p1>[A-Za-z]{0,2}\d{1,6})\s*[–—−-]\s*(?P<p2>[A-Za-z]{0,2}\d{1,6})"
)

# 容忍 markdown 加粗/斜体包裹，如 **核验日期**：2026-09-29
VERIFIED_ON_RE = re.compile(
    r"(?:核验日期|verified_on)[\*_`\s]*[：:]\s*(\d{4}-\d{2}-\d{2})"
)

# 真正的违规：scholar.google.com 的动态查询链接
GSCHOLAR_URL_RE = re.compile(r"scholar\.google\.com/scholar\?", re.I)
# 裸提 "Google Scholar"：仅在**非禁止性**语境下才算违规，
# 否则规则本身的表述（"严禁使用 Google Scholar…"）会被误判为违规。
GSCHOLAR_MENTION_RE = re.compile(r"Google\s*Scholar", re.I)
PROHIBITION_RE = re.compile(r"禁止|严禁|不得|不可|杜绝|NEVER|forbid|avoid", re.I)


def norm_pages(s: str) -> str:
    """归一化页码/卷期写法，便于比较。"""
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = re.sub(r"\s+", "", s)
    return s.strip(".")


def cite_eq(claimed: str, actual: str) -> bool:
    """页码比较：容忍 '243-249' vs '243-9' 之类的简写差异。"""
    a, b = norm_pages(claimed), norm_pages(actual)
    if a == b:
        return True
    # 支持 '243-9' 表示 '243-249'
    m1 = re.match(r"^(\d+)-(\d+)$", a)
    m2 = re.match(r"^(\d+)-(\d+)$", b)
    if m1 and m2:
        if m1.group(1) == m2.group(1):
            lo, hi = m2.group(2), m1.group(2)
            if m1.group(2).startswith(m2.group(2)) or m2.group(2).startswith(m1.group(2)):
                return True
    return False


# ---------------------------------------------------------------- HTTP

def _confirm_gone(url: str, rounds: int = 3) -> bool:
    """复测 404 是否稳定。只要出现一次矛盾应答，就说明是反爬抖动而非页面消失。

    实测依据：peabody.jhu.edu 对**确实存在**的页面，约 13% 的请求返回 404，
    其余返回 403。若采信单次 404，工具就会把自己触发的反爬拦截，
    报成「你引用的页面不存在」。
    """
    for _ in range(rounds):
        time.sleep(0.3)
        req = urllib.request.Request(
            url, method="GET",
            headers={"User-Agent": UA, "Accept": "text/html,*/*"},
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status < 400:
                    return False  # 又能拿到了 → 绝不是页面消失
        except urllib.error.HTTPError as e:
            if e.code not in (404, 410):
                return False  # 403/429/5xx → 反爬或服务端故障，不是「没了」
        except Exception:  # noqa: BLE001
            return False  # 网络抖动，无法判定
    return True


def http_status(url: str) -> tuple[str, str]:
    """返回 (status, detail)。status ∈ ok / warn / fail。

    ★ 核心设计原则：核验工具绝不能把**自身的网络故障**报成「源失效」。
      那正是本工具存在的意义所要杜绝的假断言——一个因为本机断网就宣布
      「你引用的论文页面不存在」的工具，比没有工具更危险。

      因此判定规则刻意保守：
        · 服务器明确应答 404/410      → **复测确认后**才 FAIL（单次 404 可能是反爬抖动）
        · 服务器明确应答 401/403/429  → WARN（反爬，需人工点击）
        · DNS 解析失败 (NXDOMAIN)     → FAIL（域名确实不在了）
        · 超时 / 握手失败 / 连接被拒  → WARN（无法区分是源挂了还是本机网络问题）
        · TLS 证书不匹配              → WARN（可能是域名易主，也可能是本机代理）
    """
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(
            url, method=method,
            headers={"User-Agent": UA, "Accept": "text/html,*/*"},
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return OK, f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                return WARN, f"HTTP {e.code}（反爬拦截，需人工点击核验）"
            if e.code in (404, 410):
                if method == "HEAD":
                    continue  # HEAD 被 WAF 误答 404 极常见，必须用 GET 复核
                if _confirm_gone(url):
                    return FAIL, f"HTTP {e.code}（连续复核均为 404/410，页面应已不存在）"
                return WARN, f"HTTP {e.code}（应答不稳定，疑反爬抖动，需人工核验）"
            if method == "GET":
                return WARN, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            reason = e.reason
            if isinstance(reason, socket.gaierror):
                return FAIL, f"DNS 解析失败（域名不存在）: {reason}"
            text = str(reason)
            if "certificate" in text.lower() or "ssl" in text.lower():
                if method == "GET":
                    host = urllib.parse.urlparse(url).hostname or ""
                    names = probe_cert_names(host) if host else ""
                    if names and host and host not in names:
                        return FAIL, (
                            f"域名已易主：该域名现在出示的证书属于 [{names}]，"
                            f"与所引用的 {host} 无关"
                        )
                    return WARN, f"TLS 层失败，无法判定: {text[:70]}"
                continue
            if method == "GET":
                return WARN, f"网络不可达，无法判定: {text[:70]}"
        except Exception as e:  # noqa: BLE001 - 超时等
            if method == "GET":
                return WARN, f"请求异常，无法判定: {type(e).__name__}"
    return WARN, "网络不可达，无法判定"


# 这些状态码说明数据源**没有回答「有没有这一条」**，只是暂时不肯干活
TRANSIENT_STATUS = (429, 500, 502, 503, 504)


def _retry_after(e: urllib.error.HTTPError) -> float:
    try:
        return float(e.headers.get("Retry-After") or 0)
    except (TypeError, ValueError):
        return 0.0


def get_json(url: str, tries: int = 3) -> tuple[bool, dict | None, str]:
    """返回 (reached, data, error)。

    ★ reached=False 的含义是**无法判定**，不是「查无此项」：
        · 本机网络不通
        · 数据源限流 (429) 或服务端故障 (5xx)
      调用方**必须**把它降级为 WARN。只有 reached=True 且 data 为空，
      才是数据源明确回答「这一条不在册」。

    429 尤其危险：CrossRef 在高并发反查时会限流，若把 429 当成「明确应答」，
    工具就会把自己触发的限流，报成「你引用的论文不存在」——正是本文件开头
    那条设计原则要杜绝的假断言。因此这里对瞬时故障重试并退避。
    """
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return True, json.loads(r.read().decode("utf-8", "replace")), ""
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                # 数据源的明确应答：网络是通的，这一条确实不在册
                return True, None, f"HTTP {e.code}"
            if e.code in TRANSIENT_STATUS and attempt < tries - 1:
                last = f"HTTP {e.code}"
                time.sleep(min(_retry_after(e) or 2**attempt, 15))
                continue
            return False, None, f"HTTP {e.code}（限流或服务端故障，未能判定）"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {str(e)[:70]}"
            if attempt < tries - 1:
                time.sleep(2**attempt)
                continue
            return False, None, last
    return False, None, last


# ---------------------------------------------------------------- 数据源

def lookup_doi(doi: str) -> tuple[str, str, dict]:
    """CrossRef 反查。返回 (status, detail, data)。"""
    safe = urllib.parse.quote(doi, safe="")
    url = f"https://api.crossref.org/works/{safe}?mailto={CONTACT}"
    reached, d, err = get_json(url)
    if not reached:
        return WARN, f"CrossRef 未能核验（{err}）—— 这不代表该 DOI 不存在，需稍后重跑", {}
    if not d or "message" not in d:
        return FAIL, f"CrossRef 明确应答 {err or '查无此 DOI'}：该 DOI 未在册", {}
    m = d["message"]
    year = None
    for k in ("published-print", "published", "issued", "published-online"):
        dp = (m.get(k) or {}).get("date-parts") or [[None]]
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    online = (m.get("published-online") or {}).get("date-parts", [[None]])[0][0]
    return OK, "CrossRef 命中", {
        "title": (m.get("title") or [""])[0],
        "container": (m.get("container-title") or [""])[0],
        "volume": m.get("volume") or "",
        "issue": m.get("issue") or "",
        "pages": m.get("page") or "",
        "year": year,
        "year_online": online,
        "authors": [
            f"{a.get('given','')} {a.get('family','')}".strip()
            for a in m.get("author", [])
        ],
    }


def lookup_pubmed(pmid: str) -> tuple[str, str, dict]:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=pubmed&id={pmid}&retmode=json"
    )
    reached, d, err = get_json(url)
    if not reached:
        return WARN, f"PubMed 未能核验（{err}）—— 这不代表该 PMID 不存在，需稍后重跑", {}
    if not d or "result" not in d or pmid not in d["result"]:
        return FAIL, f"PubMed 明确应答 {err or '查无此 PMID'}：该 PMID 未在册", {}
    r = d["result"][pmid]
    # ★ NCBI 对不存在的 PMID 仍会返回该键，只是内容带 error 字段，
    #   形如 {"uid":"99999999","error":"cannot get document summary"}。
    #   只判断键是否存在会**放过编造的 PMID**，必须显式检查 error。
    if r.get("error"):
        return FAIL, f"PubMed 明确应答「{r['error']}」：该 PMID 未在册", {}
    return OK, "PubMed 命中", {
        "title": r.get("title", ""),
        "container": r.get("fulljournalname", ""),
        "volume": r.get("volume", ""),
        "issue": r.get("issue", ""),
        "pages": r.get("pages", ""),
        "year": (r.get("pubdate", "") or "").split(" ")[0],
        "authors": [a.get("name", "") for a in r.get("authors", [])],
    }


# ---------------------------------------------------------------- 解析

def classify(url: str) -> tuple[str, str]:
    """返回 (kind, key)。"""
    m = DOI_IN_URL_RE.search(url)
    if m:
        return "doi", m.group(1).rstrip(".")
    m = PMID_IN_URL_RE.search(url)
    if m:
        return "pubmed", m.group(1)
    if "ncbi.nlm.nih.gov/pmc" in url:
        return "pmc", url
    if "arxiv.org/abs/" in url:
        return "arxiv", url
    if "osti.gov/biblio/" in url:
        return "osti", url
    if "hdl.handle.net" in url:
        return "handle", url
    return "web", url


def _fmt_cite(m: re.Match) -> str:
    vol, iss, p1, p2 = m.group("vol"), m.group("iss"), m.group("p1"), m.group("p2")
    return f"{vol}{f'({iss})' if iss else ''}, {p1}-{p2}"


# 工具自身的登记行，不是引文。它们在「核验方式」里常把卷期页重复抄一遍，
# 那是登记，不是出处；采信即误判。
ANNOTATION_RE = re.compile(r"核验方式|核验日期|verified_on|核驗")


def find_citation(line_no: int, lines: list[str]) -> str | None:
    """取本条 DOI 上方最近一条**内容行**里的 "卷(期), 页-页" 引文。

    两个都不能省的约束，都踩过：
      · 跳过「核验方式 / 核验日期」登记行——它们会重复抄写卷期页。曾因此把
        书籍章节的 196–213 配成上一篇期刊的 47(2), 215–242，报出假 ❌，
        而假 ❌ 会让人去"修正"一条本来正确的引用。
      · 遇到第一条内容行就停，不继续向上找——否则本身没有卷期的条目
        （书籍章节、会议论文）会一路回溯到上面**无关**的期刊引文。
    """
    m = CITE_RE.search(lines[line_no])
    if m:
        return _fmt_cite(m)          # 引文与 DOI 写在同一行
    i = line_no - 1
    while i >= 0 and i > line_no - 6:
        s = lines[i]
        if not s.strip() or ANNOTATION_RE.search(s):
            i -= 1
            continue
        m = CITE_RE.search(s)
        return _fmt_cite(m) if m else None   # 最近的内容行无卷期 → 本条无卷期可比
    return None


def check_one(url: str, citation: str | None) -> dict:
    kind, key = classify(url)
    rec = {"url": url, "kind": kind, "citation": citation}

    if kind == "doi":
        st, detail, data = lookup_doi(key)
        rec.update(status=st, detail=detail, data=data)
        if st == OK and citation and data.get("pages"):
            actual = (
                f"{data['volume']}"
                + (f"({data['issue']})" if data.get("issue") else "")
                + f", {data['pages']}"
            )
            if not cite_eq(citation, actual):
                rec.update(
                    status=FAIL,
                    detail=f"引文与 CrossRef 不符：文中写 {citation}，实际 {actual}",
                )
        return rec

    if kind == "pubmed":
        st, detail, data = lookup_pubmed(key)
        rec.update(status=st, detail=detail, data=data)
        if st == OK and citation and data.get("pages"):
            actual = (
                f"{data['volume']}"
                + (f"({data['issue']})" if data.get("issue") else "")
                + f", {data['pages']}"
            )
            if not cite_eq(citation, actual):
                rec.update(
                    status=FAIL,
                    detail=f"引文与 PubMed 不符：文中写 {citation}，实际 {actual}",
                )
        return rec

    st, detail = http_status(url)
    rec.update(status=st, detail=detail, data={})
    return rec


# ---------------------------------------------------------------- 主流程

def probe_cert_names(host: str) -> str:
    """取回该主机实际出示的证书所覆盖的域名。

    当证书与请求的域名不匹配时，证书里列出的名字往往能直接说明问题：
    域名被转手、被停放、或指向了完全无关的站点。这比「证书错误」有用得多。
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert() or {}
    except Exception:  # noqa: BLE001
        try:
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ss:
                    cert = ss.getpeercert() or {}
        except Exception:  # noqa: BLE001
            return ""
    names = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    if not names:
        for rdn in cert.get("subject", ()):
            for k, v in rdn:
                if k == "commonName":
                    names.append(v)
    return ", ".join(names[:4])


def connectivity_ok() -> tuple[bool, str]:
    """联网自检。

    核验前先确认本机网络/代理可用。若不可用，则本次核验产生的所有网络类结论
    都不可信 —— 必须显式告诉用户，而不是默默输出一堆 ❌。
    """
    probes = [
        f"https://api.crossref.org/works/10.1002/mdc3.12269?mailto={CONTACT}",
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?retmode=json",
    ]
    last = "未知错误"
    for url in probes:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                return True, f"连通性正常（已触达 {urllib.parse.urlparse(url).netloc}）"
        except urllib.error.HTTPError as e:
            # 服务器有应答即说明网络通
            return True, f"连通性正常（{urllib.parse.urlparse(url).netloc} 应答 HTTP {e.code}）"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {str(e)[:70]}"
    return False, last


def print_result(r: dict) -> None:
    icon = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}[r["status"]]
    print(f"  {icon} {r['url']}")
    print(f"      [{r['kind']}] {r['detail']}")
    d = r.get("data") or {}
    if d.get("title"):
        auth = ", ".join(d.get("authors", [])[:4])
        print(f"      实测: {d['title'][:90]}")
        print(f"            {auth} · {d.get('container','')} "
              f"{d.get('volume','')}({d.get('issue','')}) "
              f"{d.get('pages','')} · {d.get('year','')}")


# ---------------------------------------------------------------- HTML 报告

HTML_CSS = """
:root{--bg:#fbfaf8;--fg:#1c1b19;--dim:#6b675f;--line:#e2ded6;--card:#fff;
--ok:#1a7f45;--okbg:#e8f5ed;--warn:#9a6200;--warnbg:#fdf3e0;--fail:#b3261e;--failbg:#fdecea}
@media (prefers-color-scheme:dark){:root{--bg:#17171a;--fg:#ececec;--dim:#9b978f;
--line:#33333a;--card:#202024;--ok:#5fd08a;--okbg:#12301f;--warn:#e8b44a;--warnbg:#33280f;
--fail:#ff8a80;--failbg:#3a1a18}}
*{box-sizing:border-box}
body{margin:0;padding:32px 20px;background:var(--bg);color:var(--fg);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB",sans-serif}
.wrap{max-width:1080px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}
h2{font-size:16px;margin:32px 0 10px;font-weight:600}
.sub{color:var(--dim);font-size:13px;margin-bottom:20px}
.verdict{padding:14px 18px;border-radius:10px;font-weight:600;margin-bottom:20px}
.verdict.pass{background:var(--okbg);color:var(--ok)}
.verdict.warn{background:var(--warnbg);color:var(--warn)}
.verdict.fail{background:var(--failbg);color:var(--fail)}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.card{flex:1;min-width:130px;background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:14px 16px}
.card .n{font-size:26px;font-weight:700;line-height:1.1}
.card .l{font-size:12px;color:var(--dim);margin-top:2px}
.card.ok .n{color:var(--ok)} .card.warn .n{color:var(--warn)} .card.fail .n{color:var(--fail)}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:10px;overflow:hidden}
th{text-align:left;font-size:12px;color:var(--dim);font-weight:600;
padding:9px 12px;border-bottom:1px solid var(--line);background:transparent}
td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top;font-size:13.5px}
tr:last-child td{border-bottom:none}
tr.fail td{background:var(--failbg)}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;
font-weight:600;white-space:nowrap}
.badge.ok{background:var(--okbg);color:var(--ok)}
.badge.warn{background:var(--warnbg);color:var(--warn)}
.badge.fail{background:var(--failbg);color:var(--fail)}
a{color:inherit;word-break:break-all}
.actual{color:var(--fg)} .actual .t{font-weight:600}
.actual .m{color:var(--dim);font-size:12.5px}
.dim{color:var(--dim)}
.note{margin-top:14px;padding:12px 16px;border-left:3px solid var(--line);
color:var(--dim);font-size:13px}
code{background:var(--line);padding:1px 5px;border-radius:4px;font-size:12.5px}
@media print{body{padding:0}.card,table{break-inside:avoid}}
"""


def _fmt_actual(data: dict) -> str:
    """把 API 反查回来的元数据渲染成「实测」单元格——这是核验的物证。"""
    if not data:
        return ""
    out = []
    if data.get("title"):
        out.append(f'<div class="t">{esc(data["title"])}</div>')
    meta = []
    if data.get("authors"):
        meta.append(esc(", ".join(data["authors"][:6])))
    if data.get("container"):
        meta.append(esc(data["container"]))
    loc = esc(str(data.get("volume") or "")) + (
        f'({esc(str(data["issue"]))})' if data.get("issue") else ""
    )
    if data.get("pages"):
        loc += f' {esc(str(data["pages"]))}'
    if loc.strip():
        meta.append(loc.strip())
    if data.get("year"):
        meta.append(str(data["year"]))
    if meta:
        out.append(f'<div class="m">{esc(" · ".join(meta))}</div>')
    return f'<div class="actual">{"".join(out)}</div>'


def render_html(reports: list[dict], total: dict, source: str) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if total.get(FAIL):
        vcls, vtxt = "fail", f"❌ 存在 {total[FAIL]} 项硬错误，档案不可交付"
    elif total.get(WARN):
        vcls, vtxt = "warn", f"⚠️ 无硬错误，但有 {total[WARN]} 项需人工点击核验"
    else:
        vcls, vtxt = "pass", "✅ 全部通过"

    parts = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>引文核验报告</title>",
        f"<style>{HTML_CSS}</style></head><body><div class='wrap'>",
        "<h1>引文核验报告</h1>",
        f"<div class='sub'>生成于 {now} ｜ 核验对象 <code>{esc(source)}</code> "
        f"｜ 由 <code>scripts/verify.py</code> 生成</div>",
        f"<div class='verdict {vcls}'>{vtxt}</div>",
        "<div class='cards'>",
        f"<div class='card ok'><div class='n'>{total.get(OK, 0)}</div>"
        f"<div class='l'>✅ 通过</div></div>",
        f"<div class='card warn'><div class='n'>{total.get(WARN, 0)}</div>"
        f"<div class='l'>⚠️ 需人工核验</div></div>",
        f"<div class='card fail'><div class='n'>{total.get(FAIL, 0)}</div>"
        f"<div class='l'>❌ 失败</div></div>",
        "</div>",
    ]

    for rep in reports:
        c = rep["counts"]
        parts.append(f"<h2>{esc(rep['file'])}</h2>")
        bits = [f"✅ {c.get(OK, 0)}", f"⚠️ {c.get(WARN, 0)}", f"❌ {c.get(FAIL, 0)}"]
        bits.append(f"核验日期戳 {rep.get('stamps', 0)} 处")
        parts.append(f"<div class='sub' style='margin-bottom:8px'>{' ｜ '.join(bits)}</div>")
        parts.append(
            "<table><thead><tr><th style='width:76px'>状态</th>"
            "<th style='width:34%'>来源</th><th style='width:44%'>实测（数据源返回）</th>"
            "<th>说明</th></tr></thead><tbody>"
        )
        for r in rep["links"]:
            st = r["status"]
            label = {OK: "✅ 通过", WARN: "⚠️ 待人工", FAIL: "❌ 失败"}[st]
            cite = r.get("citation") or ""
            src = f"<a href='{esc(r['url'])}' target='_blank' rel='noopener'>{esc(r['url'])}</a>"
            cite_html = (
                f"<div class='dim' style='margin-top:3px'>文中引文 {esc(cite)}</div>"
                if cite else ""
            )
            parts.append(
                f"<tr class='{st}'>"
                f"<td><span class='badge {st}'>{label}</span></td>"
                f"<td>{src}{cite_html}"
                f"<div class='dim' style='font-size:12px;margin-top:3px'>[{esc(r['kind'])}]</div></td>"
                f"<td>{_fmt_actual(r.get('data') or {})}</td>"
                f"<td>{esc(r.get('detail', ''))}</td></tr>"
            )
        parts.append("</tbody></table>")

        if rep.get("gscholar"):
            parts.append(
                f"<div class='note' style='border-color:var(--fail)'>"
                f"❌ 违反铁律 4：出现 {rep['gscholar']} 处 Google Scholar 动态搜索链接</div>"
            )
        if rep.get("gscholar_mention"):
            parts.append(
                f"<div class='note'>"
                f"⚠️ {rep['gscholar_mention']} 处把 Google Scholar 列为核验基准"
                f"（非链接；事实层应以 DOI / PubMed 为准）</div>"
            )
        if rep.get("stale"):
            parts.append(
                f"<div class='note'>⚠️ {len(rep['stale'])} 处核验日期已超出该类数据的时效窗口</div>"
            )

    parts.append(
        "<div class='note'><b>怎么读这张表：</b><br>"
        "❌ 失败 = 数据源的<b>明确应答</b>说这条不存在（404/410 经复测确认、DOI/PMID 查无此条、"
        "引文卷期页与 API 不符）。这类必须修正后才能交付。<br>"
        "⚠️ 待人工 = 反爬 403/429、网络超时、限流等，<b>不构成「来源失效」的证据</b>，"
        "需人工点开确认。<br>"
        "✅ 通过 = 数据源已返回内容，DOI/PubMed 项同时列出 API 实测的标题与卷期页，"
        "可直接与文中引文逐字比对。</div>",
    )
    parts.append("</div></body></html>")
    return "\n".join(parts)


def collect_files(paths: list[str]) -> list[str]:
    if paths:
        found = []
        for p in paths:
            if os.path.isfile(p):
                found.append(p)
            elif os.path.isdir(p):
                for dirpath, _, names in os.walk(p):
                    found += [
                        os.path.join(dirpath, n)
                        for n in names if n.endswith(".md")
                    ]
            else:
                print(f"⚠️  跳过（路径不存在）: {p}")
        return sorted(set(found))

    found = []
    for root in ("examples", "reports"):
        if not os.path.isdir(root):
            continue
        for dirpath, _, names in os.walk(root):
            found += [
                os.path.join(dirpath, n) for n in names if n.endswith(".md")
            ]
    return sorted(found)


def scan(path: str, max_age: int, offline: bool) -> dict:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    print(f"\n📄 {path}")

    # --- 时效戳
    stamps = []
    for ln, line in enumerate(lines, 1):
        m = VERIFIED_ON_RE.search(line)
        if m:
            stamps.append((ln, m.group(1)))
    today = dt.date.today()
    stale = []
    for ln, s in stamps:
        try:
            age = (today - dt.date.fromisoformat(s)).days
        except ValueError:
            continue
        if age > max_age:
            stale.append((ln, s, age))

    # --- Google Scholar（铁律 4 禁的是**动态搜索链接**）
    #     三种情形必须分开，早前版本把它们合并报成「出现引用」，
    #     结果把一句列举核验基准的散文误判成引用违规：
    #       ① scholar.google.com/scholar? 链接          → FAIL（真正违规）
    #       ② 「严禁使用 Google Scholar」这句规定本身    → 不报（规则自述，必误判）
    #       ③ 把 Scholar 列为核验基准的散文（无链接）    → WARN（不是引用，但与
    #          「以 DOI/PubMed 为准」的取向冲突，值得提醒，不该判失败）
    gs_url, gs_mention = [], []
    for ln, l in enumerate(lines, 1):
        if GSCHOLAR_URL_RE.search(l):
            gs_url.append((ln, l.strip()))
        elif GSCHOLAR_MENTION_RE.search(l) and not PROHIBITION_RE.search(l):
            gs_mention.append((ln, l.strip()))

    # --- 链接
    targets = []
    seen = set()
    for ln, line in enumerate(lines):
        for url in URL_RE.findall(line):
            url = url.rstrip(".,;")
            if url in seen:
                continue
            seen.add(url)
            targets.append((ln, url, find_citation(ln, lines)))

    if offline:
        results = [
            {"url": u, "kind": classify(u)[0], "citation": c,
             "status": WARN, "detail": "offline 模式跳过", "data": {}}
            for _, u, c in targets
        ]
        for r in results:
            print_result(r)
    else:
        # 流式输出：谁先回来先打印，避免慢站点拖住整个报告
        results = []
        # 并发压到 3：CrossRef 对突发请求会返回 429，
        # 而 429 一旦被误判就是「假报论文不存在」，宁可慢也不要踩限流
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(check_one, u, c): i
                    for i, (_, u, c) in enumerate(targets)}
            for f in concurrent.futures.as_completed(futs):
                r = f.result()
                results.append((futs[f], r))
                print_result(r)
        results = [r for _, r in sorted(results, key=lambda x: x[0])]

    counts = {OK: 0, WARN: 0, FAIL: 0}
    for r in results:
        counts[r["status"]] += 1

    if gs_url:
        print(f"  ❌ 违反铁律 4：出现 Google Scholar 动态搜索链接（{len(gs_url)} 处）")
        for ln, t in gs_url[:3]:
            print(f"      L{ln}: {t[:80]}")
        counts[FAIL] += 1
    if gs_mention:
        print(f"  ⚠️  把 Google Scholar 列为核验基准（{len(gs_mention)} 处，非链接；"
              f"事实层应以 DOI / PubMed 为准）")
        for ln, t in gs_mention[:3]:
            print(f"      L{ln}: {t[:80]}")
        counts[WARN] += len(gs_mention)
    if stale:
        print(f"  ⚠️  时效戳超过 {max_age} 天（{len(stale)} 处）")
        for ln, s, age in stale[:5]:
            print(f"      L{ln}: 核验于 {s}，已 {age} 天")
        counts[WARN] += len(stale)
    if not stamps and targets:
        print("  ⚠️  全文无「核验日期」戳，无法判断数据时效")

    return {
        "file": path,
        "links": results,
        "counts": counts,
        "gscholar": len(gs_url),
        "gscholar_mention": len(gs_mention),
        "stale": stale,
        "stamps": len(stamps),
    }


def self_test(offline: bool = False) -> int:
    """回归自检。

    用例全部来自实际踩过的坑：一个会把「本机限流」报成「论文不存在」的核验器，
    比没有核验器更危险。所以每修掉一个误判，就把它钉成一条用例。
    """
    results: list[tuple[bool, str, str]] = []

    def chk(name: str, got, want) -> None:
        results.append((got == want, name, f"期望 {want!r}，实得 {got!r}"))

    # ① PMID 不得被截断。/99999999999/ 曾被 \d{6,9} 截成前 9 位去反查，
    #    有机会撞上**另一个真实存在的 PMID**，把编造的 ID 报成通过。
    chk("classify: 超长 PMID 不截断",
        classify("https://pubmed.ncbi.nlm.nih.gov/99999999999/"),
        ("pubmed", "99999999999"))
    chk("classify: 正常 PMID",
        classify("https://pubmed.ncbi.nlm.nih.gov/27340683/"),
        ("pubmed", "27340683"))
    chk("classify: DOI",
        classify("https://doi.org/10.1002/mdc3.12269"),
        ("doi", "10.1002/mdc3.12269"))

    # ② 时效戳要容忍 markdown 加粗（`**核验日期**：…` 曾整篇判不出时效）
    for s in ("核验日期：2026-09-29", "**核验日期**：2026-09-29",
              "- **核验日期**： 2026-09-29"):
        m = VERIFIED_ON_RE.search(s)
        chk(f"VERIFIED_ON_RE 命中: {s}", m.group(1) if m else None, "2026-09-29")

    # ③ 「禁止使用 Google Scholar」这句规定本身，不是违规
    rule = "禁止 Google Scholar 动态搜索链接"
    chk("Google Scholar: 禁止性表述不算违规",
        bool(GSCHOLAR_MENTION_RE.search(rule) and not PROHIBITION_RE.search(rule)),
        False)
    chk("Google Scholar: 真实搜索链接算违规",
        bool(GSCHOLAR_URL_RE.search("https://scholar.google.com/scholar?q=x")), True)
    # ④ 「把 Scholar 列为核验基准」是散文列举，不是引用。
    #    曾整句误判成「出现 Google Scholar 引用」并计入 FAIL——
    #    而该行恰恰是在陈述核验标准，判它违规等于惩罚一句规范说明。
    basis = "> **核验基准**：全要素官方可溯源（官网 / Google Scholar / DOI / 地方报道）"
    chk("Google Scholar: 列举核验基准 → 不是链接违规",
        bool(GSCHOLAR_URL_RE.search(basis)), False)
    chk("Google Scholar: 列举核验基准 → 仍应提示（非禁止语境）",
        bool(GSCHOLAR_MENTION_RE.search(basis) and not PROHIBITION_RE.search(basis)), True)

    # ⑤ DOI 的卷期页必须取自**本条**上方最近的内容行。书籍章节、会议论文本身
    #    没有卷期，不得一路回溯上去认领前面期刊的页码。曾因此报出假 ❌——
    #    而假 ❌ 会让人去"修正"一条本来正确的引用，比漏报更糟。
    doc = [
        '- Helmuth, M., & Schedel, M. (2022). *"Links between sonification and generative music."* '
        '*Interdisciplinary Science Reviews*, 47(2), 215–242.',
        '   - [永久 DOI 直链](https://doi.org/10.1080/03080188.2022.2035106)',
        '3. **著作章节**：Green, S., & Schedel, M. (2022). *"Cynosuric Bodies."* '
        'In *The Body in Sound, Music and Performance*, Focal Press, 196–213.',
        '   - **核验方式**：DOI 反查（Taylor & Francis, 47(2), 215–242, 2022）',
        '   - [永久 DOI 直链](https://doi.org/10.4324/9781003008217-19)',
    ]
    chk("find_citation: 期刊条目取到自己的卷期页", find_citation(1, doc), "47(2), 215-242")
    chk("find_citation: 书籍章节不认领上一条的卷期页", find_citation(4, doc), None)

    if not offline:
        # ④ 联网方向性用例：假 ID 必须报错，真 ID 必须通过。
        #    曾出现 CrossRef 429 限流被当成「该 DOI 未在册」，
        #    以及 NCBI 对不存在 PMID 返回带 error 字段的记录被当成命中。
        for name, got, want in (
            ("假 DOI 必须 FAIL", lookup_doi("10.9999/nope-xyz123")[0], FAIL),
            ("假 PMID 必须 FAIL", lookup_pubmed("99999999")[0], FAIL),
            ("真 DOI 必须 OK", lookup_doi("10.1002/mdc3.12269")[0], OK),
            ("真 PMID 必须 OK", lookup_pubmed("27340683")[0], OK),
        ):
            chk(name, got, want)

    print("自检用例：")
    for good, name, detail in results:
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← {detail}"))
    bad = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(bad)}/{len(results)} 通过"
          + ("（--offline：已跳过联网用例）" if offline else ""))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="School-Researcher 引文核验器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("paths", nargs="*", help="待核验的 markdown 文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE_DAYS,
                    help=f"核验日期时效阈值（天），默认 {DEFAULT_MAX_AGE_DAYS}")
    ap.add_argument("--offline", action="store_true", help="跳过所有网络请求")
    ap.add_argument("--force", action="store_true",
                    help="联网自检失败时仍然继续")
    ap.add_argument("--strict", action="store_true",
                    help="把「无法判定」的 WARN 也视为失败（CI 保守模式）")
    ap.add_argument("--self-test", action="store_true",
                    help="运行判定逻辑的回归自检，不扫描文件")
    ap.add_argument("--html", metavar="PATH",
                    help="额外输出一份自包含的 HTML 核验报告（可直接用浏览器打开）")
    args = ap.parse_args()

    if args.self_test:
        return self_test(args.offline)

    files = collect_files(args.paths)
    if not files:
        print("未找到待核验的 .md 文件（默认扫描 examples/ 与 reports/）")
        return 0

    if not args.offline:
        net_ok, net_msg = connectivity_ok()
        if not net_ok:
            print("=" * 62)
            print("⛔ 联网自检未通过 —— 本次核验的网络类结论不可信")
            print(f"   原因: {net_msg}")
            print("   本机网络或代理不可用时，任何「链接失效」都可能是误报。")
            print("   请检查网络 / 代理设置后重跑，或改用 --offline 只做格式与时效检查。")
            print("=" * 62)
            if not args.force:
                print("\n已中止（如确要继续，加 --force）。")
                return 2
        else:
            print(f"✓ {net_msg}")

    reports = [scan(f, args.max_age, args.offline) for f in files]

    total = {OK: 0, WARN: 0, FAIL: 0}
    for r in reports:
        for k in total:
            total[k] += r["counts"][k]

    if args.json:
        print(json.dumps({"reports": reports, "total": total},
                         ensure_ascii=False, indent=2))
    else:
        print("\n" + "═" * 62)
        print(f"总计：✅ {total[OK]} 项通过 ｜ ⚠️  {total[WARN]} 项需人工 ｜ ❌ {total[FAIL]} 项失败")
        if total[FAIL]:
            print("\n❌ 存在问题，核验未通过。修正后重新运行本脚本。")
        elif total[WARN]:
            print("\n⚠️  无硬错误，但存在需人工点击核验的项目。")
        else:
            print("\n✅ 全部通过。")

    if args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(render_html(reports, total, " ".join(args.paths or ["examples/", "reports/"])))
            print(f"\n📊 HTML 报告已写入 {args.html}")
        except OSError as e:
            print(f"\n⚠️  HTML 报告写入失败: {e}")

    if args.strict:
        return 1 if (total[FAIL] or total[WARN]) else 0
    return 1 if total[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
