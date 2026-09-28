import json
import logging
from openai import OpenAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ProblemGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_problem(self, topic: str, difficulty: int) -> dict:
        """
        Generates a coding problem using OpenAI GPT-4o-mini.
        """
        prompt = f"""
        Generate a coding problem for the topic '{topic}' with difficulty level {difficulty} (1=Easy, 2=Medium, 3=Hard).
        
        Return the result as a raw JSON object with the following structure:
        {{
            "title": "Problem Title",
            "description": "Detailed problem description",
            "starter_code": "Python function signature. ALWAYS name the function 'solution'.",
            "test_cases": [
                {{"input": "input1", "expected": "output1"}},
                {{"input": "input2", "expected": "output2"}}
            ],
            "constraints": "Time and space complexity constraints",
            "sample_input": "example input",
            "sample_output": "example output",
            "solution": "Full reference solution code",
            "hints": ["Hint 1", "Hint 2"]
        }}
        
        Ensure the JSON is valid and the code is correct.
        """

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert competitive programming problem setter."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                problem_data = json.loads(response.choices[0].message.content)
                
                # Validation Layer
                if self.validate_problem(problem_data):
                    problem_data["topic"] = topic
                    problem_data["difficulty"] = difficulty
                    return problem_data
                else:
                    logger.warning(f"Validation failed for generated problem (attempt {attempt+1})")
            except Exception as e:
                logger.error(f"Error generating problem (attempt {attempt+1}): {e}")
        
        return None

    def validate_problem(self, data: dict) -> bool:
        """Ensures all required fields exist and are non-empty."""
        required_fields = ["title", "description", "starter_code", "test_cases", "constraints", "sample_input", "sample_output", "solution"]
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        if not isinstance(data["test_cases"], list) or len(data["test_cases"]) < 2:
            return False
            
        return True

generator = ProblemGenerator()

if __name__ == "__main__":
    import sys
    print("Testing Problem Generator...")
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)
        
    test_res = generator.generate_problem("arrays", 1)
    if test_res:
        print("Successfully generated problem:")
        print(json.dumps(test_res, indent=2))
    else:
        print("Failed to generate problem. Check logs.")
