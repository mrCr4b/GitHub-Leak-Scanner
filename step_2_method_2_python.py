import os
import ast
from datetime import datetime  # Thêm ở đầu file

def check_function_rule(node, source_code, keyword, param):
    func_body = ast.get_source_segment(source_code, node) or ""
    func_args = [arg.arg for arg in node.args.args]

    has_keyword = keyword in func_body
    has_param = any(param in arg for arg in func_args)

    if has_keyword and has_param:
        result_type = "keyword yes param yes"
    elif has_keyword and not has_param:
        result_type = "keyword yes param no"
    elif not has_keyword and has_param:
        result_type = "keyword no param yes"
    else:
        result_type = "keyword no param no"

    return result_type

def run_method_2_python(repo_path, rules_raw):
    results = {}

    # Parse rules dạng "keyword:param" thành tuple (keyword, param)
    rules = []
    for rule in rules_raw:
        if ':' in rule:
            keyword, param = rule.split(':', 1)
            rules.append((keyword.strip(), param.strip()))
        else:
            print(f"⚠️ Rule không hợp lệ (thiếu dấu ':'): {rule}")
            continue

    for keyword, param in rules:
        rule_key = f"{keyword}:{param}"
        results[rule_key] = {
            "result_type": "keyword no param no",
            "file_path": []
        }

    for root, _, files in os.walk(repo_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)
            except Exception as e:
                print(f"⚠️ Lỗi khi parse {file_path}: {e}")
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for keyword, param in rules:
                        rule_key = f"{keyword}:{param}"
                        result_type = check_function_rule(node, source, keyword, param)

                        # Nếu kết quả tốt hơn (ưu tiên yes > no), thì ghi đè result_type
                        current_type = results[rule_key]["result_type"]
                        priority = {
                            "keyword yes param yes": 4,
                            "keyword yes param no": 3,
                            "keyword no param yes": 2,
                            "keyword no param no": 1
                        }

                        if priority[result_type] > priority[current_type]:
                            results[rule_key]["result_type"] = result_type

                        # Nếu có từ khóa hoặc tham số thì lưu path
                        if "yes" in result_type:
                            # Ghi lại thời gian phát hiện nếu chưa có
                            if "time_found" not in results[rule_key]:
                                now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                                results[rule_key]["time_found"] = now

                            if relative_path not in results[rule_key]["file_path"]:
                                results[rule_key]["file_path"].append(relative_path)

    # Xóa key file_path nếu rỗng
    for entry in results.values():
        if not entry["file_path"]:
            del entry["file_path"]

    return {"step_2_method_2": results}
