from app.db.supabase import supabase
import random
import json

TOPICS = ["basics", "arrays", "strings", "recursion", "sorting", "searching", "dynamic_programming", "graphs", "trees"]
DIFFICULTIES = [1, 2, 3]

def seed_problems():
    print("Seeding problems...")
    problems = []
    
    for topic in TOPICS:
        for diff in DIFFICULTIES:
            # Create 2 problems for each topic/difficulty combination
            for i in range(2):
                problem = {
                    "title": f"{topic.capitalize()} Challenge {diff}.{i+1}",
                    "description": f"This is a {topic} problem with difficulty {diff}. Solve it to improve your skill.",
                    "topic": topic,
                    "difficulty": diff,
                    "starter_code": "def solution():\n    # Write your code here\n    pass",
                    "test_cases": json.dumps([
                        {"input": "1 2 3", "expected": "Case 1: Success"},
                        {"input": "4 5 6", "expected": "Case 2: Success"}
                    ]),
                    "constraints": "O(n) time, O(1) space",
                    "sample_input": "1 2 3",
                    "sample_output": "Case 1: Success",
                    "solution": "print('Success')",
                    "hints": json.dumps(["Think about loops.", "Use a dictionary."])
                }
                problems.append(problem)
    
    try:
        data, count = supabase.table('problems').insert(problems).execute()
        print(f"Successfully seeded {len(problems)} problems.")
    except Exception as e:
        print(f"Error seeding problems: {e}")

if __name__ == "__main__":
    seed_problems()
