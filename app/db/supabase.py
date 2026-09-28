import os
import sqlite3
import uuid
import json
import logging
from datetime import datetime
from app.core.config import get_settings
from app.ml.problem_bank import CURATED_PROBLEMS

logger = logging.getLogger(__name__)

class SupabaseResponse:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count if count is not None else (len(data) if isinstance(data, list) else (1 if data is not None else 0))

    def __getitem__(self, item):
        if item == 0: return self.data
        if item == 1: return self.count
        raise IndexError(item)

    def __iter__(self):
        return iter((self.data, self.count))


class LocalQueryBuilder:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self._action = "SELECT"
        self._select_cols = "*"
        self._where_clauses = []
        self._where_params = []
        self._insert_data = None
        self._update_data = None
        self._upsert_data = None
        self._on_conflict = None
        self._order_by = None
        self._limit_val = None
        self._is_single = False
        self._not_clause = False

    @property
    def not_(self):
        self._not_clause = True
        return self

    def select(self, cols="*", count=None):
        self._select_cols = cols
        return self

    def eq(self, col, val):
        self._where_clauses.append(f"{col} = ?")
        self._where_params.append(val)
        return self

    def neq(self, col, val):
        self._where_clauses.append(f"{col} != ?")
        self._where_params.append(val)
        return self

    def lt(self, col, val):
        self._where_clauses.append(f"{col} < ?")
        self._where_params.append(val)
        return self

    def gt(self, col, val):
        self._where_clauses.append(f"{col} > ?")
        self._where_params.append(val)
        return self

    def in_(self, col, vals):
        if not vals:
            if self._not_clause:
                self._not_clause = False
                return self
            else:
                self._where_clauses.append("1 = 0")
                return self
        placeholders = ",".join(["?"] * len(vals))
        if self._not_clause:
            self._where_clauses.append(f"{col} NOT IN ({placeholders})")
            self._not_clause = False
        else:
            self._where_clauses.append(f"{col} IN ({placeholders})")
        self._where_params.extend(vals)
        return self

    def order(self, col, desc=False):
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{col} {direction}"
        return self

    def limit(self, val):
        self._limit_val = val
        return self

    def single(self):
        self._is_single = True
        return self

    def insert(self, data):
        self._action = "INSERT"
        self._insert_data = data
        return self

    def update(self, data):
        self._action = "UPDATE"
        self._update_data = data
        return self

    def upsert(self, data, on_conflict=None):
        self._action = "UPSERT"
        self._upsert_data = data
        self._on_conflict = on_conflict
        return self

    def execute(self):
        conn = self.client.get_connection()
        cursor = conn.cursor()

        try:
            if self._action == "INSERT":
                items = self._insert_data if isinstance(self._insert_data, list) else [self._insert_data]
                inserted_rows = []
                for item in items:
                    item_copy = dict(item)
                    if "id" not in item_copy and self.table_name in ["problems", "users"]:
                        item_copy["id"] = str(uuid.uuid4())
                    if "created_at" not in item_copy and self.table_name in ["users", "user_attempts"]:
                        item_copy["created_at"] = datetime.now().isoformat()
                    
                    cols = list(item_copy.keys())
                    vals = list(item_copy.values())
                    placeholders = ",".join(["?"] * len(cols))
                    sql = f"INSERT INTO {self.table_name} ({','.join(cols)}) VALUES ({placeholders})"
                    cursor.execute(sql, vals)
                    inserted_rows.append(item_copy)
                conn.commit()
                res_data = inserted_rows if isinstance(self._insert_data, list) else (inserted_rows[0] if inserted_rows else None)
                return SupabaseResponse(res_data)

            elif self._action == "UPDATE":
                set_clauses = []
                params = []
                for k, v in self._update_data.items():
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
                
                sql = f"UPDATE {self.table_name} SET {','.join(set_clauses)}"
                if self._where_clauses:
                    sql += " WHERE " + " AND ".join(self._where_clauses)
                    params.extend(self._where_params)
                
                cursor.execute(sql, params)
                conn.commit()
                return SupabaseResponse([self._update_data])

            elif self._action == "UPSERT":
                items = self._upsert_data if isinstance(self._upsert_data, list) else [self._upsert_data]
                upserted = []
                for item in items:
                    cols = list(item.keys())
                    vals = list(item.values())
                    placeholders = ",".join(["?"] * len(cols))
                    sql = f"INSERT OR REPLACE INTO {self.table_name} ({','.join(cols)}) VALUES ({placeholders})"
                    cursor.execute(sql, vals)
                    upserted.append(item)
                conn.commit()
                return SupabaseResponse(upserted)

            elif self._action == "SELECT":
                has_join = "problems(title)" in str(self._select_cols)
                
                if has_join and self.table_name == "user_attempts":
                    sql = """
                        SELECT user_attempts.*, problems.title as problem_title 
                        FROM user_attempts 
                        LEFT JOIN problems ON user_attempts.problem_id = problems.id
                    """
                else:
                    cols_str = "*" if (self._select_cols == "*" or "problems(" in str(self._select_cols)) else self._select_cols
                    sql = f"SELECT {cols_str} FROM {self.table_name}"

                if self._where_clauses:
                    clauses = [c if not has_join else f"user_attempts.{c}" for c in self._where_clauses]
                    sql += " WHERE " + " AND ".join(clauses)

                if self._order_by:
                    order_col = self._order_by if not has_join else f"user_attempts.{self._order_by}"
                    sql += f" ORDER BY {order_col}"

                if self._limit_val is not None:
                    sql += f" LIMIT {self._limit_val}"

                cursor.execute(sql, self._where_params)
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    d = dict(row)
                    if has_join and "problem_title" in d:
                        d["problems"] = {"title": d.pop("problem_title")}
                    results.append(d)

                if self._is_single:
                    res_data = results[0] if results else None
                else:
                    res_data = results

                return SupabaseResponse(res_data, count=len(results))

        except Exception as e:
            logger.error(f"Local SQLite error on table {self.table_name}: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()


class LocalDatabaseClient:
    def __init__(self, db_path="data/local_app.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                username TEXT,
                password TEXT,
                skill_score REAL DEFAULT 0.3,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_topic_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                topic TEXT,
                skill REAL,
                attempt_count INTEGER DEFAULT 0,
                last_updated TEXT,
                UNIQUE(user_id, topic)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                topic TEXT,
                difficulty INTEGER,
                starter_code TEXT,
                test_cases TEXT,
                constraints TEXT,
                sample_input TEXT,
                sample_output TEXT,
                solution TEXT,
                hints TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                problem_id TEXT,
                topic TEXT,
                accuracy REAL,
                time_taken REAL,
                attempts INTEGER DEFAULT 1,
                difficulty INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)

        cursor.execute("""
            DELETE FROM problems
            WHERE title LIKE '% Challenge %'
              AND (
                description LIKE 'Solve this % problem (Difficulty Level %). Implement solution() function.'
                OR description LIKE 'This is a % problem with difficulty %. Solve it to improve your skill.'
              )
        """)
        existing_titles = {row[0] for row in cursor.execute("SELECT title FROM problems")}
        self._seed_default_problems(cursor, existing_titles)

        conn.commit()
        cursor.close()
        conn.close()

    def _seed_default_problems(self, cursor, existing_titles=None):
        existing_titles = existing_titles or set()
        sql = """INSERT INTO problems
                 (id, title, description, topic, difficulty, starter_code, test_cases, constraints, sample_input, sample_output, solution, hints, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        for problem in CURATED_PROBLEMS:
            if problem["title"] in existing_titles:
                continue
            cursor.execute(sql, (
                str(uuid.uuid4()),
                problem["title"],
                problem["description"],
                problem["topic"],
                problem["difficulty"],
                problem["starter_code"],
                json.dumps(problem["test_cases"]),
                problem["constraints"],
                problem["sample_input"],
                problem["sample_output"],
                problem["solution"],
                json.dumps(problem["hints"]),
                datetime.now().isoformat(),
            ))
            existing_titles.add(problem["title"])

    def table(self, table_name):
        return LocalQueryBuilder(self, table_name)


class SupabaseClient:
    _instance = None

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            settings = get_settings()
            url = settings.SUPABASE_URL
            key = settings.SUPABASE_KEY

            # If Supabase credentials are missing or default placeholder, use local SQLite DB
            if not url or not key or "placeholder" in url or "placeholder" in key:
                logger.info("Using Local SQLite Database Client for storage.")
                cls._instance = LocalDatabaseClient()
            else:
                try:
                    from supabase import create_client
                    logger.info("Initializing remote Supabase client...")
                    cls._instance = create_client(url, key)
                    logger.info("Supabase client initialized successfully.")
                except Exception as e:
                    logger.warning(f"Failed to initialize remote Supabase client ({e}). Falling back to Local SQLite DB.")
                    cls._instance = LocalDatabaseClient()
        return cls._instance

def get_db():
    return SupabaseClient.get_client()

supabase = get_db()
