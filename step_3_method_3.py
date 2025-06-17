import os
from datetime import datetime

def run_method_3(repo_path, config_dict):
    # Lấy danh sách rule strings từ config dict
    rule_strings = config_dict.get("rules", [])

    # Chuyển các rule string dạng "keyword:param" thành tuple
    rules = []
    for rule in rule_strings:
        if ':' in rule:
            keyword, param = rule.split(':', 1)
            rules.append((keyword.lower().strip(), param.lower().strip()))
        else:
            print(f"⚠️ Rule không hợp lệ (thiếu dấu ':'): {rule}")

    result = {}

    excluded_folders = {'.git', '__pycache__', '.idea'}

    for keyword, required in rules:
        matched_files = []

        for root, dirs, files in os.walk(repo_path):
            current_folder = os.path.basename(root).lower()

            if current_folder in excluded_folders:
                continue

            if keyword in current_folder:
                # Kiểm tra nếu có ít nhất một item (folder/file) bên trong chứa param
                items = dirs + files
                for item in items:
                    item_name = os.path.splitext(item)[0].lower()
                    if required in item_name:
                        rel_path = os.path.relpath(os.path.join(root, item), repo_path)
                        matched_files.append(rel_path)

                if matched_files:
                    break  # Dừng nếu đã có match

        # Ghi kết quả
        rule_key = f"{keyword}:{required}"
        if matched_files:
            result[rule_key] = {
                "found": "yes",
                "time_found": datetime.now().strftime("%H:%M:%S %d-%m-%Y"),
                "file_path": matched_files
            }
        else:
            result[rule_key] = {
                "found": "no"
            }

    return {"step_2_method_3": result}
