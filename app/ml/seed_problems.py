from app.db.supabase import supabase
import json
from app.ml.problem_bank import CURATED_PROBLEMS

def seed_problems():
    print("Replacing generated placeholders with curated problems...")
    try:
        existing = supabase.table('problems').select('id,title,description').execute().data or []
        placeholders = [row for row in existing if _is_placeholder(row)]
        placeholder_ids = [row['id'] for row in placeholders]
        if placeholder_ids:
            supabase.table('problems').delete().in_('id', placeholder_ids).execute()

        existing_titles = {row.get('title') for row in existing if row not in placeholders}
        problems = []
        for problem in CURATED_PROBLEMS:
            if problem['title'] in existing_titles:
                continue
            db_problem = problem.copy()
            db_problem['test_cases'] = json.dumps(db_problem['test_cases'])
            db_problem['hints'] = json.dumps(db_problem['hints'])
            problems.append(db_problem)

        if problems:
            supabase.table('problems').insert(problems).execute()
        print(f"Seeded {len(problems)} curated problems; removed {len(placeholder_ids)} placeholders.")
    except Exception as e:
        print(f"Error seeding problems: {e}")


def _is_placeholder(problem):
    title = problem.get('title', '')
    description = problem.get('description', '')
    legacy_local = (
        description.startswith('Solve this ')
        and ' problem (Difficulty Level ' in description
        and description.endswith('. Implement solution() function.')
    )
    legacy_seed = (
        description.startswith('This is a ')
        and ' problem with difficulty ' in description
        and description.endswith('Solve it to improve your skill.')
    )
    return ' Challenge ' in title and (legacy_local or legacy_seed)

if __name__ == "__main__":
    seed_problems()
