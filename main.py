# main.py
import os
import json
import threading
import shutil

from step_1           import basic_search
from clone_repos      import clone_repo
from step_2_method_1  import run_method_1
from step_2_method_2  import run_method_2
from step_3_method_3  import run_method_3
from save_result_step import save_result_step
from result_formatter import export_one       #  ⇦  new helper
from email_summary import send_summary_email
from common_helpers import base_dir

PROFILES_DIR = base_dir() / "profiles"
REPOS_DIR = base_dir() / "repos"


def load_profile(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run_pipeline(display_callback=None, stop_event: threading.Event | None = None):
    for profile_file in os.listdir(PROFILES_DIR):
        if stop_event and stop_event.is_set():
            print("🔴 Pipeline cancelled by user.")
            break
        if not profile_file.endswith(".json"):
            continue

        file_stem     = os.path.splitext(profile_file)[0]                 # e.g. profile_A
        profile_path  = os.path.join(PROFILES_DIR, profile_file)

        # ── read config to get logical display name ────────────────────
        profile_cfg   = load_profile(profile_path)
        display_name  = profile_cfg.get("profile_name", file_stem)        # e.g. project_1

        print(f"\n🚀 Đang xử lý profile: {display_name}")

        keywords          = profile_cfg.get("step_1_keywords", [])
        keywords_method_1 = profile_cfg.get("step_2_method_1", [])

        # 1️⃣  basic search
        repos = basic_search(keywords)
        print(f"🔗 Tìm được {len(repos)} repo")

        # 2️⃣  clone + scan each repo -----------------------------------
        for repo_fullname in repos:
            if stop_event and stop_event.is_set():
                print("🔴 Pipeline cancelled while cloning.")
                break
            # … clone + scan logic …
            url       = f"https://github.com/{repo_fullname}"
            repo_path = clone_repo(url)
            if not repo_path:
                continue    # skip if clone failed

            # init result stub
            repo_result = {
                "repo_name": repo_fullname,
                "url": url,
            }

            method_map = {
                "step_2_method_1": run_method_1,
                "step_2_method_2": run_method_2,
                "step_2_method_3": run_method_3,
            }

            for method_key, method_func in method_map.items():
                step_cfg = profile_cfg.get(method_key, {})
                if step_cfg.get("use", "no") == "yes":
                    res = method_func(repo_path, step_cfg)
                    repo_result[method_key] = res.get(method_key, {})

            # append this repo’s block to the profile’s results file
            save_result_step(file_stem, repo_result)

            # --- delete working copy right after saving ---
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
            except Exception as exc:
                print("⚠️  Không xoá được thư mục repo:", exc)

        # cancel the whole pipeline, not just this profile
        if stop_event and stop_event.is_set():
            break

        # 3️⃣  one-time post-processing for the whole profile -----------
        if not (stop_event and stop_event.is_set()):
            try:
                pretty = export_one(file_stem, display_name=display_name)
                if display_callback:
                    display_callback(pretty)
                print("📄 Đã xuất báo cáo tạm thời cho", display_name)
            except FileNotFoundError:
                print("⚠️  Không tìm thấy file kết quả cho", display_name)
    
    if not (stop_event and stop_event.is_set()):
        send_summary_email()


if __name__ == "__main__":
    run_pipeline()
