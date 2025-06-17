from step_2_method_2_python import run_method_2_python
from step_2_method_2_java import run_method_2_java
from step_2_method_2_c_sharp import run_method_2_csharp
from step_2_method_2_c import run_method_2_c

def run_method_2(repo_path, config_dict):
    language = config_dict.get("language", "Python")
    rules_raw = config_dict.get("rules", [])

    if language == "Python":
        return run_method_2_python(repo_path, rules_raw)
    elif language == "Java":
        return run_method_2_java(repo_path, config_dict)
    elif language == "C#":
        return run_method_2_csharp(repo_path, config_dict)
    elif language == "C/C++":
        return run_method_2_c(repo_path, config_dict)
    else:
        print(f"⚠️ Ngôn ngữ không được hỗ trợ: {language}")
        return {"step_2_method_2": {}}
