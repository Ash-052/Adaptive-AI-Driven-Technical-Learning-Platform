from app.db.supabase import supabase
import json

def check_columns():
    try:
        response = supabase.table('user_attempts').select('*').limit(1).execute()
        if response.data and len(response.data) > 0:
            print("Columns in 'user_attempts':")
            print(list(response.data[0].keys()))
        else:
            print("Table 'user_attempts' is empty. Trying to describe table if possible (not directly supported by postgrest easily).")
            # We can try to insert a row and see the error? Or just ask user.
            # But let's try to get schema info if possible.
            print("Please check your Supabase dashboard for the correct column name for 'timestamp'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
