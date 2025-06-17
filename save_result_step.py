import json
import os
from common_helpers import base_dir

def save_result_step(profile_name, repo_result):
    results_dir = base_dir() / "results"
    os.makedirs(results_dir, exist_ok=True)

    file_path = os.path.join(results_dir, f"{profile_name}.json")

    # Đọc file hiện tại (nếu có)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ File JSON {file_path} bị lỗi định dạng, sẽ khởi tạo lại.")
            data = []
    else:
        data = []


    # Kiểm tra repo đã có chưa
    for i, repo_data in enumerate(data):
        if repo_data["repo_name"] == repo_result["repo_name"]:
            # Cập nhật repo hiện có
            data[i].update(repo_result)
            break
    else:
        # Thêm mới nếu chưa có
        data.append(repo_result)

    # Ghi lại toàn bộ file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)