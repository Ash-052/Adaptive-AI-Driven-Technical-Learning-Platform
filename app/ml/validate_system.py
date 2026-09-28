import asyncio
import httpx
import time
import json
from app.db.supabase import supabase

BASE_URL = "http://localhost:8000/api/v1"

# Mock User IDs (UUIDs)
WEAK_USER_ID = "00000000-0000-0000-0000-000000000001"
MED_USER_ID = "00000000-0000-0000-0000-000000000002"
STRONG_USER_ID = "00000000-0000-0000-0000-000000000003"

async def setup_test_users():
    print("Setting up test users in DB...")
    users = [
        {"id": WEAK_USER_ID, "email": "weak@test.com", "username": "weak_user", "password": "hashed_password_123", "skill_score": 0.2},
        {"id": MED_USER_ID, "email": "med@test.com", "username": "medium_user", "password": "hashed_password_123", "skill_score": 0.5},
        {"id": STRONG_USER_ID, "email": "strong@test.com", "username": "strong_user", "password": "hashed_password_123", "skill_score": 0.85},
    ]
    for u in users:
        supabase.table('users').upsert(u).execute()
        
    # Mock Mastery
    topics = ["basics", "arrays", "strings", "recursion", "sorting", "searching", "dynamic_programming", "graphs", "trees"]
    
    # Weak User: Bad at recursion/DP
    mastery_weak = []
    for t in topics:
        skill = 0.1 if t in ["recursion", "dynamic_programming"] else 0.4
        mastery_weak.append({"user_id": WEAK_USER_ID, "topic": t, "skill": skill})
    supabase.table('user_topic_mastery').upsert(mastery_weak, on_conflict='user_id, topic').execute()
    
    # Strong User: Good at everything
    mastery_strong = [{"user_id": STRONG_USER_ID, "topic": t, "skill": 0.9} for t in topics]
    supabase.table('user_topic_mastery').upsert(mastery_strong, on_conflict='user_id, topic').execute()

async def test_recommendation(user_id, expected_difficulty):
    print(f"\nTesting Recommendation for user {user_id}...")
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/problems/next/{user_id}")
    latency = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        rec = data["recommendation"]
        prob = data["problem"]
        print(f"PASS: Rec Topic={rec['topic']}, Diff={rec['difficulty']}, Confidence={rec['confidence']:.2f}")
        print(f"Problem: {prob['title']} (D{prob['difficulty']})")
        print(f"Latency: {latency:.2f}s")
        return True, rec['difficulty'] == expected_difficulty
    else:
        print(f"FAIL: {response.text}")
        return False, False

async def test_tutor():
    print("\nTesting AI Tutor Endpoints...")
    async with httpx.AsyncClient() as client:
        # Hint Test
        hint_payload = {
            "problem_id": "test",
            "user_code": "def solve():\n    # I am stuck",
            "topic": "recursion",
            "difficulty": 2
        }
        res = await client.post(f"{BASE_URL}/tutor/hint", json=hint_payload)
        if res.status_code == 200 and "response" in res.json():
            print("PASS: Hint provided.")
        else:
            print(f"FAIL: Hint error: {res.text}")

        # Explain Test
        explain_payload = {
            "problem_id": "test",
            "solution_code": "def solve(): return True",
            "skill_level": 0.2
        }
        res = await client.post(f"{BASE_URL}/tutor/explain", json=explain_payload)
        if res.status_code == 200 and "response" in res.json():
            print("PASS: Explanation provided.")
        else:
            print(f"FAIL: Explain error: {res.text}")

async def run_validation():
    await setup_test_users()
    
    results = []
    
    # Test Weak User
    success, diff_match = await test_recommendation(WEAK_USER_ID, 1)
    results.append(("Weak User", success))
    
    # Test Strong User
    success, diff_match = await test_recommendation(STRONG_USER_ID, 3)
    results.append(("Strong User", success))
    
    # Tutor Validation
    await test_tutor()
    
    print("\nValidation Summary:")
    for task, res in results:
        print(f"{task}: {'PASS' if res else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(run_validation())
