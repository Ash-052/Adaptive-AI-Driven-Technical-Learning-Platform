import subprocess
import tempfile
import os
import time
import sys
import re
import json

SUPPORTED_LANGUAGES = {
    "python": {"label": "Python", "extension": ".py", "runtime": sys.executable},
    "javascript": {"label": "JavaScript", "extension": ".js", "runtime": "node"},
    "cpp": {"label": "C++", "extension": ".cpp", "compiler": "g++"},
    "c": {"label": "C", "extension": ".c", "compiler": "gcc"},
    "java": {"label": "Java", "extension": ".java", "compiler": "javac"}
}


def _normalize_language(language: str):
    key = (language or "python").lower().replace(" ", "").replace("++", "pp")
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "nodejs": "javascript",
        "ts": "javascript",
        "c++": "cpp",
        "cpp17": "cpp",
        "c#": "csharp",
        "cs": "csharp",
        "java": "java",
        "gcc": "c",
        "gpp": "cpp"
    }
    return aliases.get(key, key)


def _fix_python_code(code: str):
    func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code)
    if not func_match:
        return code

    func_name = func_match.group(1)
    return code + f"\n\nimport sys, ast\ntry:\n    input_data = sys.stdin.read().strip()\n    if input_data:\n        try:\n            parsed_input = ast.literal_eval(input_data)\n            if isinstance(parsed_input, tuple):\n                print({func_name}(*parsed_input))\n            else:\n                print({func_name}(parsed_input))\n        except:\n            print({func_name}(input_data))\nexcept Exception:\n    pass\n"


def _run_python(code: str, test_cases: list):
    code = _fix_python_code(code)
    with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    results = []
    passed_count = 0

    try:
        for tc in test_cases:
            start_time = time.time()
            try:
                process = subprocess.Popen(
                    [sys.executable, tmp_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate(input=str(tc['input']), timeout=2)
                execution_time = time.time() - start_time

                actual_output = stdout.strip()
                expected_output = str(tc.get('expected') or tc.get('output')).strip()
                passed = actual_output == expected_output
                if passed:
                    passed_count += 1

                results.append({
                    "input": tc['input'],
                    "expected": expected_output,
                    "actual": actual_output,
                    "passed": passed,
                    "error": stderr if stderr else None,
                    "time": round(execution_time, 3)
                })
            except subprocess.TimeoutExpired:
                process.kill()
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "TLE",
                    "passed": False,
                    "status": "Time Limit Exceeded"
                })
            except Exception as e:
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "Error",
                    "passed": False,
                    "status": f"Runtime Error: {str(e)}"
                })
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return passed_count, results


def _run_javascript(code: str, test_cases: list):
    with tempfile.NamedTemporaryFile(suffix=".js", mode='w', delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    results = []
    passed_count = 0

    try:
        for tc in test_cases:
            start_time = time.time()
            try:
                process = subprocess.Popen(
                    ["node", tmp_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate(input=str(tc['input']), timeout=2)
                execution_time = time.time() - start_time

                actual_output = stdout.strip()
                expected_output = str(tc.get('expected') or tc.get('output')).strip()
                passed = actual_output == expected_output
                if passed:
                    passed_count += 1

                results.append({
                    "input": tc['input'],
                    "expected": expected_output,
                    "actual": actual_output,
                    "passed": passed,
                    "error": stderr if stderr else None,
                    "time": round(execution_time, 3)
                })
            except subprocess.TimeoutExpired:
                process.kill()
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "TLE",
                    "passed": False,
                    "status": "Time Limit Exceeded"
                })
            except Exception as e:
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "Error",
                    "passed": False,
                    "status": f"Runtime Error: {str(e)}"
                })
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return passed_count, results


def _compile_and_run_native(code: str, test_cases: list, language: str):
    if language == "cpp":
        compiler = "g++"
        ext = ".cpp"
    elif language == "c":
        compiler = "gcc"
        ext = ".c"
    else:
        compiler = "javac"
        ext = ".java"

    if shutil.which(compiler) is None:
        raise RuntimeError(f"{compiler} is not installed on this machine.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        if language == "java":
            class_name = "Main"
            if "class " not in code and "public class" not in code:
                code = f"public class {class_name} {{\n{code}\n}}"
            src_path = os.path.join(tmp_dir, f"{class_name}.java")
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(code)

            subprocess.run([compiler, src_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
            exe = ["java", "-cp", tmp_dir, class_name]
        else:
            src_path = os.path.join(tmp_dir, f"program{ext}")
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(code)
            out_path = os.path.join(tmp_dir, "program")
            subprocess.run([compiler, src_path, "-o", out_path], cwd=tmp_dir, check=True, capture_output=True, text=True)
            exe = [out_path]

        results = []
        passed_count = 0
        for tc in test_cases:
            start_time = time.time()
            try:
                process = subprocess.Popen(
                    exe,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = process.communicate(input=str(tc['input']), timeout=2)
                actual_output = stdout.strip()
                expected_output = str(tc.get('expected') or tc.get('output')).strip()
                passed = actual_output == expected_output
                if passed:
                    passed_count += 1
                results.append({
                    "input": tc['input'],
                    "expected": expected_output,
                    "actual": actual_output,
                    "passed": passed,
                    "error": stderr if stderr else None,
                    "time": round(time.time() - start_time, 3),
                })
            except subprocess.TimeoutExpired:
                process.kill()
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "TLE",
                    "passed": False,
                    "status": "Time Limit Exceeded"
                })
            except Exception as e:
                results.append({
                    "input": tc['input'],
                    "expected": tc.get('expected') or tc.get('output'),
                    "actual": "Error",
                    "passed": False,
                    "status": f"Runtime Error: {str(e)}"
                })
        return passed_count, results


def run_code(code: str, test_cases: list, language: str = "python"):
    """
    Executes user code against a list of test cases and returns the results.
    """
    normalized = _normalize_language(language)
    if normalized == "python":
        passed_count, results = _run_python(code, test_cases)
    elif normalized == "javascript":
        if shutil.which("node") is None:
            raise RuntimeError("Node.js is not installed on this machine.")
        passed_count, results = _run_javascript(code, test_cases)
    elif normalized in {"cpp", "c", "java"}:
        passed_count, results = _compile_and_run_native(code, test_cases, normalized)
    else:
        raise RuntimeError(f"Unsupported language: {language}")

    total_cases = len(test_cases)
    status = "Accepted" if passed_count == total_cases else "Wrong Answer"
    return {
        "status": status,
        "passed": passed_count,
        "total": total_cases,
        "results": results,
    }


import shutil
