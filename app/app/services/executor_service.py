import subprocess
import tempfile
import os
import time
import sys
import re

def run_code(code: str, test_cases: list):
    """
    Executes user code against a list of test cases and returns the results.
    """
    results = []
    passed_count = 0
    
    # Dynamically detect the function name from the code (e.g., def my_func(args):)
    func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code)
    if func_match:
        func_name = func_match.group(1)
        # Append a driver that reads from stdin, evals the input as arguments,
        # and prints the result of calling the detected function.
        code += f"\n\nimport sys, ast\ntry:\n    input_data = sys.stdin.read().strip()\n    if input_data:\n        try:\n            # Try to parse as a safe Python literal (handles lists, dicts, quoted strings)\n            parsed_input = ast.literal_eval(input_data)\n            if isinstance(parsed_input, tuple):\n                print({func_name}(*parsed_input))\n            else:\n                print({func_name}(parsed_input))\n        except:\n            # If literal_eval fails, it might be a raw unquoted string or comma-separated raw values\n            # For simple unquoted strings (like '(a+b)'), we pass as is\n            print({func_name}(input_data))\nexcept Exception as e:\n    # print(f'DRIVER ERROR: {{e}}', file=sys.stderr)\n    pass\n"

    # Create a temporary file for the user's code
    with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        for tc in test_cases:
            start_time = time.time()
            try:
                # Run the code using subprocess
                process = subprocess.Popen(
                    [sys.executable, tmp_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Pass test case input to stdin and set timeout
                stdout, stderr = process.communicate(input=str(tc['input']), timeout=2)
                execution_time = time.time() - start_time
                
                actual_output = stdout.strip()
                expected_output = str(tc.get('expected') or tc.get('output')).strip()
                
                passed = (actual_output == expected_output)
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
        # Cleanup: remove the temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    total_cases = len(test_cases)
    status = "Accepted" if passed_count == total_cases else "Wrong Answer"
    
    return {
        "status": status,
        "passed": passed_count,
        "total": total_cases,
        "results": results
    }
