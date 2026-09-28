from app.db.supabase import supabase

def get_a_user():
    try:
        # Try to get a user from 'users' table or 'user_topic_mastery'
        response = supabase.table('user_topic_mastery').select('user_id').limit(1).execute()
        if response.data and len(response.data) > 0:
            print(f"Found existing user_id: {response.data[0]['user_id']}")
        else:
            print("No users found in 'user_topic_mastery'.")
            # Try 'users' table
            try:
                res = supabase.table('users').select('id').limit(1).execute()
                if res.data:
                    print(f"Found existing user_id from 'users': {res.data[0]['id']}")
            except:
                print("Could not query 'users' table.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_a_user()
