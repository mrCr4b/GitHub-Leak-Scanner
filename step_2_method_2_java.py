# step_2_method_2_java.py
"""
Run “method 2” on Java projects.

For every rule  "keyword:param"
    * keyword  → look for it anywhere **inside** a method body
    * param    → look for it (substring-match) in any parameter name

Returns a dict shaped exactly like the Python version:

{
    "step_2_method_2": {
        "dog:cat": {
            "result_type": "...",
            "time_found": "HH:MM:SS dd-mm-YYYY",
            "file_path": ["path\\to\\File.java", ...]
        },
        ...
    }
}
"""
from __future__ import annotations

import os
import re
from datetime import datetime

# ─────────────────────────────── regexes
# Very forgiving Java-method signature matcher
#   public static <T> Foo bar (Type p1, int x) {
_METHOD_SIG = re.compile(
    r"(?:public|protected|private|static|\s)+[\w<>\[\],\s]+\s+"   # return type
    r"(?P<name>\w+)\s*"                                          # method name
    r"\((?P<params>[^)]*)\)\s*\{",                               # params + "{"
    re.MULTILINE,
)


# ─────────────────────────────── helpers
def _extract_methods(source: str) -> list[tuple[str, str]]:
    """
    Return a list of (param_list, body) for every method found in `source`.
    Braces are naïvely balanced; strings / comments are not parsed, good enough
    for scanning keywords.
    """
    out = []
    for m in _METHOD_SIG.finditer(source):
        params = m.group("params").strip()
        body_start = m.end()          # index just after the opening '{'
        depth = 1
        i = body_start
        while i < len(source) and depth:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        body = source[body_start:i - 1]  # exclude the last '}'
        out.append((params, body))
    return out


def _param_names(param_block: str) -> list[str]:
    """
    Roughly pull out parameter names.
    e.g.  "final Map<String,List<Integer>> foo, int[] bar"
           → ["foo", "bar"]
    """
    names = []
    for chunk in filter(None, (p.strip() for p in param_block.split(","))):
        # take last word (handles varargs, generics, arrays)
        name = re.split(r"\s+", chunk.strip())[-1]
        name = name.replace("...", "")  # remove varargs dots
        names.append(name)
    return names


def _check_rule(body: str, params: list[str], keyword: str, param_kw: str) -> str:
    has_keyword = keyword in body
    has_param   = any(param_kw in p for p in params)

    if has_keyword and has_param:
        return "keyword yes param yes"
    if has_keyword and not has_param:
        return "keyword yes param no"
    if not has_keyword and has_param:
        return "keyword no param yes"
    return "keyword no param no"


# ─────────────────────────────── public API
def run_method_2_java(repo_path: str, step_cfg: dict) -> dict:
    """`step_cfg` must contain `"rules": ["dog:cat", ...]`"""
    rules_raw = step_cfg.get("rules", [])
    rules: list[tuple[str, str]] = []

    for rule in rules_raw:
        if ":" not in rule:
            print(f"⚠️  Rule không hợp lệ (thiếu ':'): {rule}")
            continue
        k, p = (s.strip() for s in rule.split(":", 1))
        rules.append((k, p))

    # initial result skeleton
    results: dict[str, dict] = {
        f"{k}:{p}": {
            "result_type": "keyword no param no",
            "file_path": []
        }
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
            if not fname.endswith(".java"):
                continue

            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, repo_path)

            try:
                source = open(fpath, "r", encoding="utf-8").read()
            except Exception as exc:
                print(f"⚠️  Lỗi đọc {fpath}: {exc}")
                continue

            # scan each method
            for param_block, body in _extract_methods(source):
                param_names = _param_names(param_block)
                for k, p in rules:
                    key = f"{k}:{p}"
                    new_type = _check_rule(body, param_names, k, p)
                    cur_type = results[key]["result_type"]

                    if priority[new_type] > priority[cur_type]:
                        results[key]["result_type"] = new_type

                    if "yes" in new_type:
                        if "time_found" not in results[key]:
                            results[key]["time_found"] = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                        if rel not in results[key]["file_path"]:
                            results[key]["file_path"].append(rel)

    # prune empty paths
    for entry in results.values():
        if not entry["file_path"]:
            entry.pop("file_path", None)

    return {"step_2_method_2": results}
