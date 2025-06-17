"""
step_2_method_2_c.py
====================

Method-2 implementation for C and C++ projects.

Expected profile snippet
------------------------
"step_2_method_2": {
    "use": "yes",
    "language": "C",
    "rules": ["dog:cat", "black:white"]
}

Return shape is identical to the other language scanners:
{
  "step_2_method_2": {
     "dog:cat": {
        "result_type": "...",
        "time_found": "HH:MM:SS dd-mm-YYYY",
        "file_path": ["src/foo.c", ...]
     },
     ...
  }
}
"""

from __future__ import annotations
import os, re, time, stat
from datetime import datetime

# ─────────────────────────── simple C/C++ function regex
FUNC_SIG = re.compile(
    r"""
    ^[^\S\r\n]*                       # optional leading spaces
    (?:[\w\*\&]+\s+)+?                # return type(s)  e.g.  'static int *'
    (?P<name>\w+)\s*                  # func name
    \((?P<params>[^\)]*)\)            # param list
    \s*(\{)                           # opening brace
    """,
    re.MULTILINE | re.VERBOSE
)

# ─────────────────────────── helpers
def _extract_funcs(source: str):
    """Yield (params_block, body) for every function found."""
    for m in FUNC_SIG.finditer(source):
        params = m.group("params")
        idx = m.end()                 # position after '{'
        depth = 1
        while idx < len(source) and depth:
            if source[idx] == "{":
                depth += 1
            elif source[idx] == "}":
                depth -= 1
            idx += 1
        body = source[m.end(): idx - 1]
        yield params, body

def _param_names(param_block: str):
    """Return list of parameter names extracted heuristically."""
    names = []
    for part in filter(None, (p.strip() for p in param_block.split(","))):
        token = re.split(r"\s+", part.strip())[-1]    # last token is name
        token = token.replace("*", "").replace("&", "")
        names.append(token)
    return names

def _classify(body: str, params: list[str], kw: str, prm: str):
    has_kw  = kw in body
    has_prm = any(prm in p for p in params)
    if has_kw and has_prm: return "keyword yes param yes"
    if has_kw:             return "keyword yes param no"
    if has_prm:            return "keyword no param yes"
    return                       "keyword no param no"

PRIORITY = {
    "keyword yes param yes": 4,
    "keyword yes param no":  3,
    "keyword no param yes":  2,
    "keyword no param no":   1,
}

# ─────────────────────────── main entry
def run_method_2_c(repo_path: str, cfg: dict) -> dict:
    rules = []
    for rule in cfg.get("rules", []):
        if ":" in rule:
            kw, prm = (t.strip() for t in rule.split(":", 1))
            rules.append((kw, prm))
        else:
            print("⚠️  Rule thiếu dấu ':' ->", rule)

    results = {
        f"{k}:{p}": {"result_type": "keyword no param no", "file_path": []}
        for k, p in rules
    }

    for root, _, files in os.walk(repo_path):
        for fname in files:
            if not fname.endswith((".c", ".cpp", ".cc", ".h", ".hpp")):
                continue
            path = os.path.join(root, fname)
            rel  = os.path.relpath(path, repo_path)

            try:
                src = open(path, "r", encoding="utf-8", errors="ignore").read()
            except Exception as exc:
                print("⚠️  Lỗi đọc", path, exc)
                continue

            for params_block, body in _extract_funcs(src):
                param_names = _param_names(params_block)
                for kw, prm in rules:
                    key  = f"{kw}:{prm}"
                    new  = _classify(body, param_names, kw, prm)
                    cur  = results[key]["result_type"]
                    if PRIORITY[new] > PRIORITY[cur]:
                        results[key]["result_type"] = new
                    if "yes" in new:
                        if "time_found" not in results[key]:
                            results[key]["time_found"] = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                        if rel not in results[key]["file_path"]:
                            results[key]["file_path"].append(rel)

    # prune empty paths
    for entry in results.values():
        if not entry["file_path"]:
            entry.pop("file_path", None)

    return {"step_2_method_2": results}
