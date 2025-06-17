"""
Method-2 implementation for C# repositories.

Given a repo path and a profile config dict:
{
    "use": "yes",
    "language": "csharp",
    "rules": ["dog:cat", "black:white"]
}

it classifies each rule for every *.cs file:

    keyword yes param yes
    keyword yes param no
    keyword no  param yes
    keyword no  param no

and returns:
{
  "step_2_method_2": { ... }
}
"""

from __future__ import annotations
import os
import re
from datetime import datetime

# ─────────────────────────────── regexes
_METHOD_SIG = re.compile(
    r"(?:public|private|protected|internal|static|async|sealed|\s)+"  # modifiers
    r"[\w<>\[\],\s]+\s+"                                              # return type
    r"(?P<name>\w+)\s*"                                               # method name
    r"\((?P<params>[^\)]*)\)\s*{"                                     # param list + {
)

# ─────────────────────────────── helpers
def _extract_methods(source: str) -> list[tuple[str, str]]:
    """
    Naïvely extract (param_block, body) tuples for each method.
    Assumes braces are balanced outside string literals – good enough for scan.
    """
    res = []
    for m in _METHOD_SIG.finditer(source):
        param_block = m.group("params").strip()
        i = m.end()
        depth = 1
        while i < len(source) and depth:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        body = source[m.end(): i - 1]
        res.append((param_block, body))
    return res


def _param_names(param_block: str) -> list[str]:
    """
    Return last identifier in each parameter declaration.
    int cat, string[] dogList → ['cat', 'dogList']
    """
    names = []
    for chunk in filter(None, (p.strip() for p in param_block.split(","))):
        name = re.split(r"\s+", chunk)[-1].replace("...", "")
        names.append(name)
    return names


def _classify(body: str, params: list[str], kw: str, param_kw: str) -> str:
    has_kw  = kw in body
    has_par = any(param_kw in p for p in params)
    if has_kw and has_par:
        return "keyword yes param yes"
    if has_kw:
        return "keyword yes param no"
    if has_par:
        return "keyword no param yes"
    return "keyword no param no"


# ─────────────────────────────── main entry
def run_method_2_csharp(repo_path: str, cfg: dict) -> dict:
    rules_raw = cfg.get("rules", [])
    rules: list[tuple[str, str]] = []
    for rule in rules_raw:
        if ":" not in rule:
            print(f"⚠️  Rule không hợp lệ (thiếu ':'): {rule}")
            continue
        a, b = (s.strip() for s in rule.split(":", 1))
        rules.append((a, b))

    # init
    results: dict[str, dict] = {
        f"{k}:{p}": {"result_type": "keyword no param no", "file_path": []}
        for k, p in rules
    }
    priority = {
        "keyword yes param yes": 4,
        "keyword yes param no": 3,
        "keyword no param yes": 2,
        "keyword no param no": 1,
    }

    for root, _, files in os.walk(repo_path):
        for fname in files:
            if not fname.endswith(".cs"):
                continue
            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, repo_path)

            try:
                src = open(fpath, "r", encoding="utf-8").read()
            except Exception as exc:
                print(f"⚠️  Lỗi đọc {fpath}: {exc}")
                continue

            for param_blk, body in _extract_methods(src):
                params = _param_names(param_blk)
                for k, p in rules:
                    key = f"{k}:{p}"
                    typ = _classify(body, params, k, p)
                    if priority[typ] > priority[results[key]["result_type"]]:
                        results[key]["result_type"] = typ
                    if "yes" in typ:
                        if "time_found" not in results[key]:
                            results[key]["time_found"] = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                        if rel not in results[key]["file_path"]:
                            results[key]["file_path"].append(rel)

    for entry in results.values():
        if not entry["file_path"]:
            entry.pop("file_path", None)

    return {"step_2_method_2": results}
