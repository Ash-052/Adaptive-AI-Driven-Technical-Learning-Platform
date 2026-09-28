import subprocess
import tempfile
import os
import time
import sys
import re
import ast
import json
import shutil
import httpx

JUDGE0_LANGUAGE_IDS = {
    "c": 50,
    "cpp": 54,
    "csharp": 51,
    "go": 60,
    "java": 62,
    "javascript": 63,
    "python": 71,
    "rust": 73,
}


def _normalize_language(language: str):
    key = (language or "python").lower().replace(" ", "").replace("++", "pp")
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "nodejs": "javascript",
        "c#": "csharp",
        "cs": "csharp",
        "c++": "cpp",
        "cpp17": "cpp",
        "gcc": "c",
        "gpp": "cpp"
    }
    return aliases.get(key, key)


def _fix_python_code(user_code: str):
    func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", user_code)
    if not func_match:
        return user_code

    func_name = func_match.group(1)
    return user_code + f"\n\nimport sys, ast\ntry:\n    input_data = sys.stdin.read().strip()\n    if input_data:\n        try:\n            parsed_input = ast.literal_eval(input_data)\n            if isinstance(parsed_input, tuple):\n                print({func_name}(*parsed_input))\n            else:\n                print({func_name}(parsed_input))\n        except:\n            print({func_name}(input_data))\nexcept Exception:\n    pass\n"


def _execute_local(user_code: str, test_cases: list, language: str = "python"):
    """
    Executes user code against test cases and returns pass/fail results.
    """
    normalized = _normalize_language(language)
    results = []
    passed = 0

    if normalized == "python":
        user_code = _fix_python_code(user_code)
        with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as tmp:
            tmp.write(user_code)
            tmp_path = tmp.name

        try:
            for tc in test_cases:
                start_time = time.time()
                try:
                    process = subprocess.Popen([
                        sys.executable, tmp_path
                    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    tc_input = str(tc.get('input', ''))
                    stdout, stderr = process.communicate(input=tc_input, timeout=2)
                    actual = stdout.strip()
                    expected = str(tc.get('expected') or tc.get('output', '')).strip()
                    is_passed = (actual == expected)
                    if is_passed:
                        passed += 1

                    results.append({
                        "input": tc_input,
                        "expected": expected,
                        "output": actual,
                        "status": "Passed" if is_passed else "Failed",
                        "error": stderr.strip() if stderr else None,
                        "time": round(time.time() - start_time, 3)
                    })
                except subprocess.TimeoutExpired:
                    process.kill()
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "TLE",
                        "status": "Time Limit Exceeded"
                    })
                except Exception as e:
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "Error",
                        "status": f"Runtime Error: {str(e)}"
                    })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    elif normalized == "javascript":
        if shutil.which("node") is None:
            raise RuntimeError("Node.js is not installed on this machine.")
        with tempfile.NamedTemporaryFile(suffix=".js", mode='w', delete=False) as tmp:
            tmp.write(user_code)
            tmp_path = tmp.name
        try:
            for tc in test_cases:
                start_time = time.time()
                try:
                    process = subprocess.Popen(["node", tmp_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    tc_input = str(tc.get('input', ''))
                    stdout, stderr = process.communicate(input=tc_input, timeout=2)
                    actual = stdout.strip()
                    expected = str(tc.get('expected') or tc.get('output', '')).strip()
                    is_passed = (actual == expected)
                    if is_passed:
                        passed += 1
                    results.append({
                        "input": tc_input,
                        "expected": expected,
                        "output": actual,
                        "status": "Passed" if is_passed else "Failed",
                        "error": stderr.strip() if stderr else None,
                        "time": round(time.time() - start_time, 3)
                    })
                except subprocess.TimeoutExpired:
                    process.kill()
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "TLE",
                        "status": "Time Limit Exceeded"
                    })
                except Exception as e:
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "Error",
                        "status": f"Runtime Error: {str(e)}"
                    })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    elif normalized in {"cpp", "c", "java", "go", "rust", "csharp"}:
        compiler = {
            "cpp": "g++",
            "c": "gcc",
            "java": "javac",
            "go": "go",
            "rust": "rustc",
            "csharp": "dotnet" if shutil.which("dotnet") else "csc",
        }[normalized]
        if shutil.which(compiler) is None:
            raise RuntimeError(f"A compiler/runtime for {normalized} is not installed on this machine.")

        with tempfile.TemporaryDirectory() as tmp_dir:
            if normalized == "java":
                class_name = "Main"
                if "class " not in user_code and "public class" not in user_code:
                    user_code = f"public class {class_name} {{\n{user_code}\n}}"
                src_path = os.path.join(tmp_dir, f"{class_name}.java")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                subprocess.run([compiler, src_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = ["java", "-cp", tmp_dir, class_name]
            elif normalized == "go":
                src_path = os.path.join(tmp_dir, "main.go")
                out_path = os.path.join(tmp_dir, "program.exe" if os.name == "nt" else "program")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                subprocess.run([compiler, "build", "-o", out_path, src_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = [out_path]
            elif normalized == "rust":
                src_path = os.path.join(tmp_dir, "main.rs")
                out_path = os.path.join(tmp_dir, "program.exe" if os.name == "nt" else "program")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                subprocess.run([compiler, src_path, "-o", out_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = [out_path]
            elif normalized == "csharp" and compiler == "dotnet":
                project_path = os.path.join(tmp_dir, "Runner.csproj")
                src_path = os.path.join(tmp_dir, "Program.cs")
                output_dir = os.path.join(tmp_dir, "build")
                with open(project_path, "w", encoding="utf-8") as project_file:
                    project_file.write('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
                with open(src_path, "w", encoding="utf-8") as source_file:
                    source_file.write(user_code)
                subprocess.run([compiler, "build", project_path, "--configuration", "Release", "--output", output_dir, "--nologo"], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = [compiler, os.path.join(output_dir, "Runner.dll")]
            elif normalized == "csharp":
                src_path = os.path.join(tmp_dir, "Program.cs")
                out_path = os.path.join(tmp_dir, "program.exe")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                subprocess.run([compiler, "/nologo", f"/out:{out_path}", src_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = [out_path]
            else:
                src_path = os.path.join(tmp_dir, "program.cpp" if normalized == "cpp" else "program.c")
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                out_path = os.path.join(tmp_dir, "program")
                subprocess.run([compiler, src_path, "-o", out_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
                command = [out_path]

            for tc in test_cases:
                start_time = time.time()
                try:
                    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=tmp_dir)
                    tc_input = str(tc.get('input', ''))
                    stdout, stderr = process.communicate(input=tc_input, timeout=2)
                    actual = stdout.strip()
                    expected = str(tc.get('expected') or tc.get('output', '')).strip()
                    is_passed = (actual == expected)
                    if is_passed:
                        passed += 1
                    results.append({
                        "input": tc_input,
                        "expected": expected,
                        "output": actual,
                        "status": "Passed" if is_passed else "Failed",
                        "error": stderr.strip() if stderr else None,
                        "time": round(time.time() - start_time, 3)
                    })
                except subprocess.TimeoutExpired:
                    process.kill()
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "TLE",
                        "status": "Time Limit Exceeded"
                    })
                except Exception as e:
                    results.append({
                        "input": tc.get('input'),
                        "expected": tc.get('expected'),
                        "output": "Error",
                        "status": f"Runtime Error: {str(e)}"
                    })
    else:
        raise RuntimeError(f"Unsupported language: {language}")

    return {
        "total": len(test_cases),
        "passed": passed,
        "failed": len(test_cases) - passed,
        "results": results
    }


def _parse_case_arguments(input_text: str):
    try:
        parsed = ast.literal_eval(input_text)
        return list(parsed) if isinstance(parsed, tuple) else [parsed]
    except (SyntaxError, ValueError):
        return None


def _normalize_output(output: str):
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(output.strip())
            return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        except (json.JSONDecodeError, SyntaxError, ValueError, TypeError):
            continue
    return output.strip()


def _javascript_harness(code: str):
    has_function = re.search(r"(?:function\s+solution\s*\(|(?:const|let|var)\s+solution\s*=)", code)
    reads_stdin = re.search(r"^\s*(?!//).*readFileSync\s*\(\s*0", code, re.MULTILINE)
    if has_function and not reads_stdin:
        return code + "\nconst __judge0Args = JSON.parse(require('fs').readFileSync(0, 'utf8'));\nconsole.log(JSON.stringify(solution(...__judge0Args)));\n"
    return code


def _cpp_type(values):
    present = [value for value in values if value is not None]
    if not present:
        return "int"
    value = present[0]
    if isinstance(value, list):
        children = [child for item in present if isinstance(item, list) for child in item]
        child_type = _cpp_type(children)
        return f"std::vector<{child_type}>"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "std::string"
    return "int"


def _cpp_literal(value, value_type):
    if value is None:
        return "std::nullopt"
    if value_type.startswith("std::vector<"):
        child_type = value_type[len("std::vector<"):-1]
        return f"{value_type}{{{', '.join(_cpp_literal(item, child_type) for item in value)}}}"
    if value_type == "std::string":
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def _cpp_harness(code: str, test_cases: list, case_arguments):
    main_match = re.search(r"int\s+main\s*\(\s*\)\s*\{([^}]*)\}", code)
    if not main_match or not re.fullmatch(r"\s*return\s+0\s*;\s*", main_match.group(1)):
        return code, None

    all_arguments = [_parse_case_arguments(str(case.get("input", ""))) for case in test_cases]
    if any(arguments is None for arguments in all_arguments):
        return code, None
    argument_types = []
    for position in range(len(case_arguments)):
        argument_types.append(_cpp_type([arguments[position] for arguments in all_arguments if position < len(arguments)]))
    expressions = [_cpp_literal(value, argument_types[index]) for index, value in enumerate(case_arguments)]
    helper = """
template <typename T> void __print_answer(const std::vector<T>& values);
template <typename T> void __print_answer(const T& value) { std::cout << value; }
template <typename T> void __print_answer(const std::vector<T>& values) {
    std::cout << '[';
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ", ";
        __print_answer(values[i]);
    }
    std::cout << ']';
}
"""
    driver = f"int main() {{ auto __answer = solution({', '.join(expressions)}); __print_answer(__answer); return 0; }}"
    wrapped = code[:main_match.start()] + helper + driver + code[main_match.end():]
    return wrapped, ""


def _java_type(values):
    present = [value for value in values if value is not None]
    if not present:
        return "int"
    value = present[0]
    if isinstance(value, list):
        children = [child for item in present if isinstance(item, list) for child in item]
        return _java_type(children) + "[]"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "String"
    return "int"


def _java_literal(value, value_type):
    if value is None:
        return "null"
    if value_type.endswith("[]"):
        element_type = value_type[:-2]
        return f"new {element_type}[]{{{', '.join(_java_literal(item, element_type) for item in value)}}}"
    if value_type == "String":
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value)


def _java_harness(code: str, test_cases: list, case_arguments):
    main_match = re.search(r"public\s+static\s+void\s+main\s*\(\s*String\[\]\s+\w+\s*\)\s*\{([^}]*)\}", code)
    empty_main = main_match and not re.sub(r"//[^\n]*", "", main_match.group(1)).strip()
    if not empty_main:
        return code, None

    all_arguments = [_parse_case_arguments(str(case.get("input", ""))) for case in test_cases]
    if any(arguments is None for arguments in all_arguments):
        return code, None
    argument_types = [
        _java_type([arguments[position] for arguments in all_arguments if position < len(arguments)])
        for position in range(len(case_arguments))
    ]
    expressions = [_java_literal(value, argument_types[index]) for index, value in enumerate(case_arguments)]
    driver = f"Object __answer = solution({', '.join(expressions)}); if (__answer instanceof int[]) System.out.print(java.util.Arrays.toString((int[]) __answer)); else if (__answer instanceof Object[]) System.out.print(java.util.Arrays.deepToString((Object[]) __answer)); else System.out.print(__answer);"
    wrapped = code[:main_match.start(1)] + driver + code[main_match.end(1):]
    return wrapped, ""


def _c_harness(code: str, case_arguments):
    main_match = re.search(r"int\s+main\s*\(\s*\)\s*\{([^}]*)\}", code)
    if not main_match or not re.fullmatch(r"\s*return\s+0\s*;\s*", main_match.group(1)):
        return code, None
    if len(case_arguments) == 1 and isinstance(case_arguments[0], list) and all(isinstance(value, int) for value in case_arguments[0]):
        values = case_arguments[0] or [0]
        array_values = ", ".join(str(value) for value in values)
        driver = f"int __nums[] = {{{array_values}}}; printf(\"%d\", solution(__nums, {len(case_arguments[0])})); return 0;"
        wrapped = code[:main_match.start(1)] + driver + code[main_match.end(1):]
        return wrapped, ""
    return code, None


def _prepare_judge0_submission(code: str, language: str, test_cases: list, case_arguments, input_text: str):
    if language == "python":
        return _fix_python_code(code), input_text
    if language == "javascript":
        return _javascript_harness(code), json.dumps(case_arguments, separators=(",", ":"))
    if language == "cpp":
        return _cpp_harness(code, test_cases, case_arguments)
    if language == "java":
        return _java_harness(code, test_cases, case_arguments)
    if language == "c":
        return _c_harness(code, case_arguments)
    if language in {"go", "rust", "csharp"}:
        return code, json.dumps(case_arguments, separators=(",", ":"))
    return code, str(test_cases[0].get("input", ""))


def _execute_with_judge0(user_code: str, test_cases: list, language: str):
    normalized = _normalize_language(language)
    language_id = JUDGE0_LANGUAGE_IDS.get(normalized)
    if language_id is None:
        raise RuntimeError(f"Unsupported language: {language}")

    judge0_url = os.getenv("JUDGE0_API_URL", "https://ce.judge0.com").rstrip("/")
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("JUDGE0_API_KEY")
    if api_key:
        headers["X-Auth-Token"] = api_key

    results = []
    passed = 0
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for case in test_cases:
            input_text = str(case.get("input", ""))
            arguments = _parse_case_arguments(input_text)
            source_code, stdin = _prepare_judge0_submission(user_code, normalized, test_cases, arguments, input_text) if arguments is not None else (user_code, input_text)
            body = {
                "source_code": source_code,
                "language_id": language_id,
                "stdin": stdin if stdin is not None else input_text,
                "cpu_time_limit": 2,
                "cpu_extra_time": 0.5,
                "wall_time_limit": 5,
                "memory_limit": 128000,
                "max_processes_and_or_threads": 20,
                "enable_network": False,
            }
            response = client.post(f"{judge0_url}/submissions?base64_encoded=false&wait=true", headers=headers, json=body)
            response.raise_for_status()
            execution = response.json()
            status = execution.get("status", {}).get("description", "Unknown Error")
            actual = execution.get("stdout") or ""
            expected = str(case.get("expected") or case.get("output", ""))
            is_passed = status == "Accepted" and _normalize_output(actual) == _normalize_output(expected)
            if is_passed:
                passed += 1
            error = execution.get("compile_output") or execution.get("stderr") or execution.get("message")
            results.append({
                "input": input_text,
                "expected": expected,
                "output": actual.strip() if actual else (error or status),
                "status": "Passed" if is_passed else status if status != "Accepted" else "Wrong Answer",
                "passed": is_passed,
                "error": error,
                "time": float(execution["time"]) if execution.get("time") else None,
            })

    return {"total": len(test_cases), "passed": passed, "failed": len(test_cases) - passed, "results": results}


def execute_user_code(user_code: str, test_cases: list, language: str = "python"):
    if len(user_code) > 20000:
        raise ValueError("Code exceeds the 20,000 character submission limit.")
    if len(test_cases) > 10:
        raise ValueError("A problem may contain at most 10 test cases.")
    return _execute_with_judge0(user_code, test_cases, language)

