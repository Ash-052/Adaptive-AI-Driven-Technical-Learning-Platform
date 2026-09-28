import re
from app.db.supabase import supabase

def standardize_function_names():
    print("Standardizing all function names to 'solution'...")
    try:
        # Fetch all problems
        res = supabase.table('problems').select('id, starter_code').execute()
        
        # Handle the tuple pattern or response object
        if isinstance(res, tuple):
            problems = res[0][1] if len(res[0]) > 1 else []
        else:
            problems = res.data
            
        if not problems:
            print("No problems found.")
            return

        updated_count = 0
        for prob in problems:
            old_code = prob['starter_code']
            if not old_code:
                continue
            
            # Replace 'def function_name(' with 'def solution('
            new_code = re.sub(r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(", "def solution(", old_code)
            
            if new_code != old_code:
                supabase.table('problems').update({"starter_code": new_code}).eq('id', prob['id']).execute()
                updated_count += 1
        
        print(f"Successfully updated {updated_count} problems to use 'def solution'.")
    except Exception as e:
        print(f"Error standardizing names: {e}")

if __name__ == "__main__":
    standardize_function_names()
