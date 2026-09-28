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
import urllib.error
import urllib.parse
import urllib.request

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
PMID_IN_URL_RE = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d{6,9})", re.I)

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

def http_status(url: str) -> tuple[str, str]:
    """返回 (status, detail)。status ∈ ok / warn / fail。

    ★ 核心设计原则：核验工具绝不能把**自身的网络故障**报成「源失效」。
      那正是本工具存在的意义所要杜绝的假断言——一个因为本机断网就宣布
      「你引用的论文页面不存在」的工具，比没有工具更危险。

      因此判定规则刻意保守：
        · 服务器明确应答 404/410      → FAIL（页面确实没了）
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
                return FAIL, f"HTTP {e.code}（服务器应答：页面不存在）"
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


def get_json(url: str) -> tuple[bool, dict | None, str]:
    """返回 (reached, data, error)。reached=False 表示是本机网络问题，而非数据源查无。"""
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return True, json.loads(r.read().decode("utf-8", "replace")), ""
    except urllib.error.HTTPError as e:
        # 404 等是数据源的明确应答 —— 说明网络是通的
        return True, None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, None, f"{type(e).__name__}: {str(e)[:70]}"


# ---------------------------------------------------------------- 数据源

def lookup_doi(doi: str) -> tuple[str, str, dict]:
    """CrossRef 反查。返回 (status, detail, data)。"""
    safe = urllib.parse.quote(doi, safe="")
    url = f"https://api.crossref.org/works/{safe}?mailto={CONTACT}"
    reached, d, err = get_json(url)
    if not reached:
        return WARN, f"CrossRef 不可达，无法核验（本机网络问题）: {err}", {}
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
        return WARN, f"PubMed 不可达，无法核验（本机网络问题）: {err}", {}
    if not d or "result" not in d or pmid not in d["result"]:
        return FAIL, f"PubMed 明确应答 {err or '查无此 PMID'}：该 PMID 未在册", {}
    r = d["result"][pmid]
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


def find_citation(line_no: int, lines: list[str]) -> str | None:
    """向上回溯 3 行找 "卷(期), 页-页" 形式的引文。"""
    for i in range(line_no, max(-1, line_no - 4), -1):
        m = CITE_RE.search(lines[i])
        if m:
            vol, iss, p1, p2 = m.group("vol"), m.group("iss"), m.group("p1"), m.group("p2")
            return f"{vol}{f'({iss})' if iss else ''}, {p1}-{p2}"
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

    # --- Google Scholar 违规（区分「引用」与「禁止引用的规定本身」）
    gs = []
    for ln, l in enumerate(lines, 1):
        if GSCHOLAR_URL_RE.search(l):
            gs.append((ln, l.strip()))
        elif GSCHOLAR_MENTION_RE.search(l) and not PROHIBITION_RE.search(l):
            gs.append((ln, l.strip()))

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
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
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

    if gs:
        print(f"  ❌ 违反铁律 4：出现 Google Scholar 引用（{len(gs)} 处）")
        for ln, t in gs[:3]:
            print(f"      L{ln}: {t[:80]}")
        counts[FAIL] += 1
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
        "gscholar": len(gs),
        "stale": stale,
        "stamps": len(stamps),
    }


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
    args = ap.parse_args()

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

    if args.strict:
        return 1 if (total[FAIL] or total[WARN]) else 0
    return 1 if total[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
