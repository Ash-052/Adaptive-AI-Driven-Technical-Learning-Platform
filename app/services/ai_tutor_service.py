import ast
import json
import logging
import re
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AITutorService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = None
        self._init_openai_if_configured()

    def _init_openai_if_configured(self):
        api_key = self.settings.OPENAI_API_KEY
        if api_key and api_key.strip() and not api_key.startswith("dummy") and not api_key.startswith("placeholder"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for AI Tutor Service.")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            self.openai_client = None

    def generate_hint(self, problem: dict, user_code: str, topic: str, difficulty: int) -> dict:
        """
        Generates a concise hint for the user based on their current progress.
        Tries OpenAI if configured; falls back to the intelligent pedagogical engine.
        """
        if self.openai_client:
            prompt = f"""
            Problem: {problem.get('title')}
            Description: {problem.get('description')}
            Topic: {topic}
            Difficulty: {difficulty}
            User's Current Code:
            ```python
            {user_code}
            ```
            
            Provide a helpful, concise hint to guide the user towards the solution.
            SAFETY RULES:
            - NEVER give the full solution or complete code blocks.
            - Point out logical errors or suggest the next step.
            - Focus on the '{topic}' aspect of the problem.
            
            Return JSON format: {{"response": "Your hint here", "type": "hint"}}
            """
            result = self._call_gpt(prompt)
            if result and result.get("type") != "error":
                return result

        # Pedagogical Fallback Engine
        return {
            "response": self._generate_pedagogical_hint(problem, user_code, topic, difficulty),
            "type": "hint"
        }

    def explain_solution(self, problem: dict, solution: str, skill_level: float) -> dict:
        """
        Explains a solution based on the user's skill level.
        Tries OpenAI if configured; falls back to the intelligent pedagogical engine.
        """
        if self.openai_client:
            complexity = "simple and foundational" if skill_level < 0.4 else "detailed and optimized"
            prompt = f"""
            Problem: {problem.get('title')}
            Solution Code:
            ```python
            {solution}
            ```
            User Skill Level: {skill_level} (Scale 0-1)
            
            Explain this solution in a {complexity} way.
            - For beginners, focus on logic flow and basic syntax.
            - For advanced users, focus on time/space complexity and optimization.
            
            Return JSON format: {{"response": "Your explanation here", "type": "explanation"}}
            """
            result = self._call_gpt(prompt)
            if result and result.get("type") != "error":
                return result

        # Pedagogical Fallback Engine
        return {
            "response": self._explain_pedagogical_solution(problem, solution, skill_level),
            "type": "explanation"
        }

    def analyze_code(self, problem: dict, user_code: str) -> dict:
        """
        Analyzes user code for bugs and provides suggestions.
        Tries OpenAI if configured; falls back to the intelligent pedagogical engine.
        """
        if self.openai_client:
            prompt = f"""
            Problem: {problem.get('title')}
            User Code:
            ```python
            {user_code}
            ```
            
            Analyze the code for logical errors, efficiency, and edge cases.
            - Be concise.
            - Suggest improvements without solving the entire problem.
            
            Return JSON format: {{"response": "Your analysis here", "type": "analysis"}}
            """
            result = self._call_gpt(prompt)
            if result and result.get("type") != "error":
                return result

        # Pedagogical Fallback Engine
        return {
            "response": self._analyze_pedagogical_code(problem, user_code),
            "type": "analysis"
        }

    def _call_gpt(self, prompt: str) -> Optional[dict]:
        try:
            if not self.openai_client:
                return None
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful and expert AI Programming Tutor."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"AI Tutor OpenAI call failed, falling back to local engine: {e}")
            return None

    # =========================================================================
    # Built-in Intelligent Pedagogical Tutor Engine
    # =========================================================================

    def _generate_pedagogical_hint(self, problem: dict, user_code: str, topic: str, difficulty: int) -> str:
        topic_lower = (topic or problem.get('topic') or 'basics').lower()
        title = problem.get('title', 'Active Problem')
        constraints = problem.get('constraints', '')
        hints = problem.get('hints', [])
        if isinstance(hints, str):
            try:
                hints = json.loads(hints)
            except Exception:
                hints = [hints] if hints else []

        code = (user_code or "").strip()

        # Check for syntax error first
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            line_str = f"line {se.lineno}" if se.lineno else "your code"
            return (
                f"🔍 **Syntax Hint (near {line_str})**:\n\n"
                f"There is a syntax issue: `{se.msg}`.\n"
                f"Double-check that all colons (`:`), parentheses, quotation marks, and indentation levels are consistent."
            )

        # Check if code is just default starter / pass
        is_starter = False
        if not code or re.search(r'^\s*def\s+solution\s*\([^)]*\)\s*:\s*(#.*)?\s*pass\s*$', code, re.MULTILINE):
            is_starter = True

        topic_strategies = {
            "basics": (
                "Identify what parameters `solution()` receives and what type of value it must return. "
                "Break down the problem into sequential steps: 1) Parse/prepare inputs, 2) Apply calculations or conditionals, 3) Return the result."
            ),
            "arrays": (
                "Consider how you need to traverse the elements. Will a single `for item in array:` pass suffice, "
                "or do you need indexed access (`range(len(arr))`)? If looking for pairs or subsets, consider a frequency map or two pointers."
            ),
            "strings": (
                "Python strings are immutable. For transformations or palindrome checks, consider string slicing (e.g. `s[::-1]`), "
                "or methods like `.split()`, `.strip()`, `.join()`. Watch out for case sensitivity and whitespace."
            ),
            "recursion": (
                "A strong recursive pattern requires: 1) A base case at the top to stop execution (e.g. `if n <= 1: return ...`), "
                "and 2) A recursive step that passes a strictly smaller problem (e.g. `n - 1`). Avoid infinite recursion by checking boundaries."
            ),
            "sorting": (
                "Think about your sorting invariant: should elements be placed in order iteratively (like insertion/bubble) "
                "or divided and conquered (like merge/quick sort)? Ensure you maintain O(n log n) efficiency if the input can be large."
            ),
            "searching": (
                "Is the collection sorted? If sorted, Binary Search will find the target in O(log n) time by halving boundaries (`low = mid + 1` or `high = mid - 1`). "
                "If unsorted and multiple lookups are needed, converting to a `set` gives O(1) membership checks."
            ),
            "dynamic_programming": (
                "Define your subproblem: What does `dp[i]` represent? Express the recurrence relation "
                "(e.g., `dp[i] = dp[i-1] + dp[i-2]`). Initialize base values (like `dp[0]` and `dp[1]`), then iterate to build up the solution."
            ),
            "trees": (
                "Tree problems are easiest solved recursively. Ask yourself: 'What do I need from the left subtree and the right subtree?' "
                "Combine those results at the current root, and handle `if not root:` as your base case."
            ),
            "graphs": (
                "Decide between Breadth-First Search (BFS with `collections.deque`) for shortest paths or Depth-First Search (DFS with recursion/stack) "
                "for connectivity. Always track `visited = set()` to avoid cyclic loops."
            )
        }

        default_strategy = topic_strategies.get(topic_lower, (
            "Carefully examine the input and expected output formats. Focus on implementing the core logic step-by-step."
        ))

        if is_starter:
            # First progressive hint
            db_hint = f"\n\n💡 **Problem Hint**: {hints[0]}" if hints and len(hints) > 0 else ""
            constraint_hint = f"\n\n⚡ **Target Complexity**: Aim to satisfy `{constraints}`." if constraints else ""
            return (
                f"🎯 **Getting Started on {title}**\n\n"
                f"{default_strategy}{db_hint}{constraint_hint}"
            )

        # User has written some code - check for next step hints
        has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
        has_print = any(isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'print' for node in ast.walk(tree))

        if has_print and not has_return:
            return (
                "⚠️ **Next Step Hint**:\n\n"
                "You are printing results using `print()`, but the evaluation system inspects the value returned by `solution()`. "
                "Replace `print(...)` with `return ...` so your test cases receive the output."
            )

        if not has_return:
            return (
                "⚠️ **Next Step Hint**:\n\n"
                "Your function does not currently have a `return` statement. "
                "Ensure that once your logic finishes computing the result, it explicitly returns the answer with `return result`."
            )

        # If they already have returns and some code, provide deeper hints
        if hints and len(hints) > 1:
            return (
                f"💡 **Algorithmic Hint for {topic_lower.capitalize()}**:\n\n"
                f"• {hints[1]}\n\n"
                f"Consider edge cases: What happens if the input is empty, has a single item, or contains duplicate values?"
            )

        return (
            f"💡 **Refining Your Approach**:\n\n"
            f"• Keep {topic_lower} principles in mind: {default_strategy}\n"
            f"• Check your edge cases (empty collection, boundary indices, zero values).\n"
            f"• Test your solution on the sample case to verify accuracy."
        )

    def _analyze_pedagogical_code(self, problem: dict, user_code: str) -> str:
        code = (user_code or "").strip()
        if not code:
            return (
                "📝 **Code Analysis**:\n\n"
                "• **Status**: No code provided.\n"
                "• **Next Step**: Write your function implementation inside `def solution():` and click **Analyze Code**."
            )

        # 1. Syntax Verification
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            line_snippet = ""
            lines = code.splitlines()
            if se.lineno and 1 <= se.lineno <= len(lines):
                bad_line = lines[se.lineno - 1]
                caret = " " * (max(0, (se.offset or 1) - 1)) + "^"
                line_snippet = f"\n```python\n{bad_line}\n{caret}\n```"

            return (
                f"❌ **Syntax Error Detected**:\n\n"
                f"• **Location**: Line {se.lineno}, Column {se.offset}\n"
                f"• **Issue**: `{se.msg}`{line_snippet}\n\n"
                f"💡 **Recommendation**: Check for unclosed brackets, missing colons (`:`), or mismatched indentation."
            )

        # 2. Check for empty starter
        is_starter = re.search(r'^\s*def\s+solution\s*\([^)]*\)\s*:\s*(#.*)?\s*pass\s*$', code, re.MULTILINE)
        if is_starter:
            return (
                "ℹ️ **Starter Template Detected**:\n\n"
                "• **Function**: `solution()` exists, but currently only contains `pass`.\n"
                "• **Action Required**: Replace `pass` with your algorithm logic.\n"
                "• **Tip**: Use the **Get Hint** button if you need ideas on how to begin!"
            )

        # 3. Static Code Analysis on AST
        findings = []
        recommendations = []
        function_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        # Check function name
        has_solution_func = any(f.name == "solution" for f in function_defs)
        if not has_solution_func:
            findings.append("⚠️ Missing `solution()` function definition. The test harness expects `def solution(...):`.")
            recommendations.append("Rename your primary function to `def solution(...):`.")

        # Check returns
        returns = [node for node in ast.walk(tree) if isinstance(node, ast.Return)]
        if not returns:
            findings.append("⚠️ No `return` statement found. The function currently returns `None`.")
            recommendations.append("Add a `return <result>` statement to pass computed values to test cases.")

        # Check for print calls
        print_calls = [
            node for node in ast.walk(tree) 
            if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'print'
        ]
        if print_calls:
            findings.append(f"ℹ️ Found {len(print_calls)} `print()` call(s). Note that tests evaluate `return` values, not stdout.")

        # Check for shadowed builtins
        builtin_names = {'list', 'dict', 'str', 'int', 'set', 'sum', 'min', 'max', 'id', 'type', 'input'}
        assigned_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id in builtin_names:
                    assigned_names.add(node.id)
        if assigned_names:
            findings.append(f"⚠️ Shadowing built-in name(s): `{', '.join(assigned_names)}`. This can cause subtle bugs.")
            recommendations.append(f"Rename variable(s) `{', '.join(assigned_names)}` to something descriptive (e.g. `items_list`, `total_sum`).")

        # Check for potential infinite loops
        while_true_nodes = [
            node for node in ast.walk(tree) 
            if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True
        ]
        for w in while_true_nodes:
            has_break_or_return = any(isinstance(sub, (ast.Break, ast.Return)) for sub in ast.walk(w))
            if not has_break_or_return:
                findings.append("🚨 Infinite loop risk: `while True` loop detected without an apparent `break` or `return` inside.")
                recommendations.append("Ensure every `while True` loop has a termination condition with `break` or `return`.")

        # Check loop depth for complexity
        max_loop_depth = 0
        def get_loop_depth(node, current_depth=0):
            nonlocal max_loop_depth
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                if current_depth > max_loop_depth:
                    max_loop_depth = current_depth
            for child in ast.iter_child_nodes(node):
                get_loop_depth(child, current_depth)

        get_loop_depth(tree)

        complexity_str = "O(1)"
        if max_loop_depth == 1:
            complexity_str = "O(n) linear time"
        elif max_loop_depth == 2:
            complexity_str = "O(n²) quadratic time"
        elif max_loop_depth >= 3:
            complexity_str = f"O(n^{max_loop_depth}) polynomial time"

        # Check constraints matching
        constraints = problem.get('constraints', '')
        if "O(n)" in constraints and max_loop_depth >= 2:
            findings.append(f"⚡ Complexity Warning: Problem constraint specifies `{constraints}`, but your code contains nested loops ({complexity_str}).")
            recommendations.append("Consider using a dictionary/hash table or two pointers to achieve linear O(n) performance.")

        if not findings:
            findings.append("✅ Clean code structure with proper syntax and return flow.")
        if not recommendations:
            recommendations.append("Run test cases or submit solution to verify against edge cases.")

        findings_text = "\n".join(f"• {f}" for f in findings)
        recs_text = "\n".join(f"• {r}" for r in recommendations)

        return (
            f"📊 **Code Analysis & Inspection**\n\n"
            f"**Complexity Overview**:\n"
            f"• Estimated Loop Depth: {max_loop_depth} level(s) → ~{complexity_str}\n\n"
            f"**Findings**:\n"
            f"{findings_text}\n\n"
            f"**Action Items**:\n"
            f"{recs_text}"
        )

    def _explain_pedagogical_solution(self, problem: dict, solution_code: str, skill_level: float) -> str:
        title = problem.get('title', 'Active Problem')
        topic = (problem.get('topic') or 'basics').capitalize()
        difficulty = problem.get('difficulty', 1)
        constraints = problem.get('constraints', 'O(n) time complexity')
        desc = problem.get('description', '')
        sample_in = problem.get('sample_input', '')
        sample_out = problem.get('sample_output', '')

        is_beginner = skill_level < 0.4

        if is_beginner:
            return (
                f"📘 **Foundational Walkthrough: {title}**\n\n"
                f"**1. What is this problem asking?**\n"
                f"{desc}\n\n"
                f"**2. Understanding the Sample**:\n"
                f"• Given Input: `{sample_in}`\n"
                f"• Expected Output: `{sample_out}`\n\n"
                f"**3. Step-by-Step Logic**:\n"
                f"• **Step 1 (Setup)**: Receive the input inside `def solution():`. Prepare your tracking variables.\n"
                f"• **Step 2 (Core Logic)**: Apply the fundamental `{topic}` pattern. If working with collections, loop through items one by one.\n"
                f"• **Step 3 (Return)**: Instead of printing, return the result so the automated checker can verify your solution.\n\n"
                f"**4. Edge Cases to Keep in Mind**:\n"
                f"• What if the input is empty or has only one element?\n"
                f"• What if all numbers are negative or zeros?"
            )
        else:
            return (
                f"🧠 **Algorithmic Strategy: {title}**\n\n"
                f"**Problem Classification**:\n"
                f"• Topic: **{topic}** | Difficulty: **Level {difficulty}**\n"
                f"• Target Constraints: **{constraints}**\n\n"
                f"**Optimal Solution Architecture**:\n"
                f"• **Technique**: Employ an optimal `{topic.lower()}` paradigm (such as two-pointer invariant, hash table memoization, or divide-and-conquer).\n"
                f"• **Invariant**: Maintain correctness across each iteration without redundant recomputation, ensuring time complexity stays within `{constraints}`.\n"
                f"• **Space Efficiency**: Minimize auxiliary allocations by reusing existing data structures or modifying in-place where permissible.\n\n"
                f"**Key Implementation Invariants**:\n"
                f"1. Handle boundary conditions (empty input, singular inputs, max constraint limits).\n"
                f"2. Ensure proper return type contract matches expected evaluation harness signature.\n"
                f"3. Guard against O(n²) bottlenecks on large datasets by choosing hash sets or two pointers over nested linear scans."
            )

tutor_service = AITutorService()
