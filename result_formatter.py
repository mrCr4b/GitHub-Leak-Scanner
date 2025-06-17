# result_formatter.py
import json
from pathlib import Path
from common_helpers import base_dir

RESULTS_DIR = base_dir() / "results"
SUMMARY_FILE  = RESULTS_DIR / "scan_summary.txt"

# ▼ same maps as before
TYPE_MAP_M1 = {
    "code": "Trong code",
    "commit history": "Trong lịch sử commit",
}
STATUS_MAP_M2 = {
    "keyword yes param yes": "✅ Có từ khóa trong cả tên hàm và tham số",
    "keyword yes param no":  "🟡 Chỉ có từ khóa trong tên hàm",
    "keyword no param yes":  "🟡 Chỉ có từ khóa trong tham số",
    "keyword no param no":   "❌ Không có từ khóa trong cả tên hàm và tham số",
}
STATUS_MAP_M3 = {"yes": "✅ Có", "no": "❌ Không"}


def _format_profile(profile_name: str, data: list[dict]) -> str:
    """Return a pretty, multi-line string for one profile."""
    out: list[str] = [f"🔍 Kết quả quét:\nProfile: {profile_name}\n"]

    for repo in data:
        out.append(f"\n📁 Repo: {repo['repo_name']}")
        out.append(f"🔗 URL: {repo['url']}\n")

        # ── Phương pháp 1 ─────────────────────────────────────
        m1 = repo.get("step_2_method_1", {})
        if m1:
            out.append("━━━━━━━━━━━━━━━━━━━━━━━")
            out.append("🧩 Phương pháp 1 – Tìm chuỗi trong mã nguồn & lịch sử commit:\n")
            for kw, info in m1.items():
                out.append(f"➤ Đã phát hiện chuỗi \"{kw}\"")
                out.append(f"   • Kiểu: {TYPE_MAP_M1.get(info['type'], info['type'])}")
                
                # AFTER   (prints only if the key exists)
                if "time_found" in info:
                    out.append(f"   • Thời gian: {info['time_found']}")
                if info["type"] == "code":
                    out.append("   • Đường dẫn:")
                    for p in info["file_path"]:
                        out.append(f"     - {p}")
                else:
                    out.append("   • Danh sách commit:")
                    for key in sorted(k for k in info if k.startswith("commit_")):
                        c = info[key]
                        out.append(f"     - SHA: `{c['sha']}`")
                        author = c['author'].split('<')[0].strip()
                        out.append(f"       • Tác giả: {author}")
                        out.append(f"       • Ngày: {c['commit_date']}")
                        for p in c["file_path"]:
                            out.append(f"       • Tệp: {p}")

        # ── Phương pháp 2 ─────────────────────────────────────
        m2 = repo.get("step_2_method_2", {})
        if m2:
            out.append("\n━━━━━━━━━━━━━━━━━━━━━━━")
            out.append("🧩 Phương pháp 2 – Tìm hàm & tham số chứa từ khóa:\n")
            for rule, info in m2.items():
                k, p = rule.split(":")
                out.append(f"➤ Hàm chứa '{k}' và tham số chứa '{p}'")
                out.append(f"   • Trạng thái: {STATUS_MAP_M2.get(info['result_type'])}")
                if "time_found" in info:
                    out.append(f"   • Thời gian: {info['time_found']}")
                if "file_path" in info:
                    out.append("   • Đường dẫn:")
                    for path in info["file_path"]:
                        out.append(f"     - {path}")

        # ── Phương pháp 3 ─────────────────────────────────────
        m3 = repo.get("step_2_method_3", {})
        if m3:
            out.append("\n━━━━━━━━━━━━━━━━━━━━━━━")
            out.append("🧩 Phương pháp 3 – Tìm thư mục chứa từ khóa + nội dung liên quan:\n")
            for rule, info in m3.items():
                k, p = rule.split(":")
                out.append(f"➤ Thư mục chứa '{k}', có tệp chứa '{p}'")
                out.append(f"   • Trạng thái: {STATUS_MAP_M3[info['found']]}")
                if "time_found" in info:
                    out.append(f"   • Thời gian: {info['time_found']}")
                if "file_path" in info:
                    out.append("   • Đường dẫn:")
                    for path in info["file_path"]:
                        out.append(f"     - {path}")

        out.append("")   # blank line between repos

    return "\n".join(out)

# add the new parameter display_name
def export_one(file_stem: str, *, display_name: str | None = None, append: bool = True) -> str:
    """
    file_stem      → 'profile_A'
    display_name   → 'project_1'  (optional; falls back to file_stem)
    """
    json_path = RESULTS_DIR / f"{file_stem}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # <display_name> is what will appear in the human-readable report header
    pretty = _format_profile(display_name or file_stem, data)

    if append:
        SUMMARY_FILE.parent.mkdir(exist_ok=True, parents=True)
        with SUMMARY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(pretty + "\n")

    return pretty

