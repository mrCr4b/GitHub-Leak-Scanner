# ─────────── export_results.py ───────────
"""
Quick one-off tool.
Read every JSON result file in ./results, convert it to a
human-readable Vietnamese report, write (append) to scan_summary.txt
"""

import json
import os
from pathlib import Path
from common_helpers import base_dir
RESULTS_DIR = base_dir() / "results"
SUMMARY_FILE  = RESULTS_DIR / "scan_summary.txt"

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

STATUS_MAP_M3 = {
    "yes": "✅ Có",
    "no":  "❌ Không",
}


def format_profile(profile_name: str, data: list[dict]) -> str:
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


def main():
    if not RESULTS_DIR.exists():
        print("❌ Không tìm thấy thư mục 'results'")
        return

    SUMMARY_FILE.unlink(missing_ok=True)   # start fresh each run

    for jf in sorted(RESULTS_DIR.glob("*.json")):
        profile_name = jf.stem
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"⚠️  Bỏ qua {jf.name}: {exc}")
            continue

        pretty = format_profile(profile_name, data)

        with SUMMARY_FILE.open("a", encoding="utf-8") as f:
            f.write(pretty + "\n")

        print(f"✅ Đã ghi kết quả profile {profile_name}")

    print(f"\n📄 Xong! Kiểm tra '{SUMMARY_FILE}' để xem toàn bộ báo cáo.")


if __name__ == "__main__":
    main()
