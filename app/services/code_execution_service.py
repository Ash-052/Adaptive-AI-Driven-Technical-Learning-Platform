import subprocess
import tempfile
import os
import time
import sys
import re
import ast
import shutil


def _normalize_language(language: str):
    key = (language or "python").lower().replace(" ", "").replace("++", "pp")
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "nodejs": "javascript",
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


def execute_user_code(user_code: str, test_cases: list, language: str = "python"):
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

