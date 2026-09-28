import subprocess
import tempfile
import os
import time
import sys
import re
import ast

def execute_user_code(user_code: str, test_cases: list):
    """
    Executes user code against test cases and returns pass/fail results.
    """
    results = []
    passed = 0
    
    # 1. Detect function name (default to 'solution' if not found)
    func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", user_code)
    func_name = func_match.group(1) if func_match else "solution"
    
    # 2. Append Driver Script
    driver = f"""
import sys, ast
try:
    input_data = sys.stdin.read().strip()
    if input_data:
        try:
            parsed_input = ast.literal_eval(input_data)
            if isinstance(parsed_input, tuple):
                print({func_name}(*parsed_input))
            else:
                print({func_name}(parsed_input))
        except:
            print({func_name}(input_data))
except Exception as e:
    print(f"RUNTIME_ERROR: {{e}}", file=sys.stderr)
"""
    full_code = user_code + "\n" + driver
    
    # 3. Create Temp File
    with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as tmp:
        tmp.write(full_code)
        tmp_path = tmp.name

    try:
        for tc in test_cases:
            start_time = time.time()
            try:
                process = subprocess.Popen(
                    [sys.executable, tmp_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Input from test case
                tc_input = str(tc.get('input', ''))
                stdout, stderr = process.communicate(input=tc_input, timeout=2)
                exec_time = time.time() - start_time
                
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
                    "error": stderr.strip() if stderr else None
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
            
    return {
        "total": len(test_cases),
        "passed": passed,
        "failed": len(test_cases) - passed,
        "results": results
    }
