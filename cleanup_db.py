from app.db.supabase import supabase

def cleanup_problems():
    print("Cleaning up placeholder problems...")
    try:
        # Delete problems with the placeholder description template
        res = supabase.table('problems').delete().like('description', '%improve your skill%').execute()
        
        # Also delete those with "Challenge" in title from the seed script
        res2 = supabase.table('problems').delete().like('title', '%Challenge%').execute()
        
        count1 = len(res[0][1]) if isinstance(res, tuple) else (len(res.data) if res.data else 0)
        count2 = len(res2[0][1]) if isinstance(res2, tuple) else (len(res2.data) if res2.data else 0)
        
        print(f"Cleanup complete. Removed {count1 + count2} placeholder problems.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_problems()
