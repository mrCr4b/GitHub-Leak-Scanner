import os
import subprocess
from datetime import datetime

def get_current_time():
    return datetime.now().strftime("%H:%M:%S %d-%m-%Y")

def search_string_in_file(file_path, target_string):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return target_string in f.read()
    except Exception:
        return False

def search_string_in_repo_files(repo_path, keyword):
    matched_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            if search_string_in_file(file_path, keyword):
                rel_path = os.path.relpath(file_path, repo_path)
                matched_files.append(rel_path)
    return matched_files

def search_string_in_git_history(repo_path, keyword):
    commits = {}
    try:
        result = subprocess.run(
            ["git", "log", "-S", keyword, "--all", "--pretty=format:%H|%an <%ae>|%ad", "--name-only"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        output = result.stdout.strip().split('\n')

        commit_index = 1
        i = 0
        while i < len(output):
            if "|" in output[i]:
                sha, author, date = output[i].split("|")
                i += 1
                file_paths = []
                while i < len(output) and output[i].strip() != "":
                    file_paths.append(output[i].strip())
                    i += 1
                if file_paths:
                    commits[f"commit_{commit_index}"] = {
                        "sha": sha,
                        "author": author,
                        "commit_date": date,
                        "file_path": file_paths
                    }
                    commit_index += 1
            i += 1
    except Exception as e:
        print(f"❌ Lỗi khi tìm trong git history: {e}")
    return commits

def run_method_1(repo_path: str, config_dict: dict) -> dict:
    """
    Thực hiện method 1 trên repo đã clone.

    Input:
        - repo_path: đường dẫn đến repo.
        - config_dict: dict chứa config, phải có khóa "strings".

    Output:
        - dict kết quả theo định dạng:
          {
              "step_2_method_1": {
                  "keyword1": {...},
                  "keyword2": {...},
                  ...
              }
          }
    """
    keywords = config_dict.get("strings", [])
    result = {}

    for keyword in keywords:
        current_time = get_current_time()
        matched_files = search_string_in_repo_files(repo_path, keyword)
        if matched_files:
            result[keyword] = {
                "type": "code",
                "time_found": current_time,
                "file_path": matched_files
            }
            continue

        commits = search_string_in_git_history(repo_path, keyword)
        if commits:
            result[keyword] = {
                "type": "commit history",
                "time_found": current_time,
                **commits
            }
        else:
            result[keyword] = {
                "type": "notfound"
            }

    return {"step_2_method_1": result}
