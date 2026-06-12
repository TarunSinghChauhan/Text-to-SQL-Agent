import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

PROJECT_ROOT = "C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project"
FEEDBACK_DIR = os.path.join(PROJECT_ROOT, "feedback")
os.makedirs(FEEDBACK_DIR, exist_ok=True)

class FeedbackManager:
    def __init__(self, db_path: str = os.path.join(FEEDBACK_DIR, "feedback.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_feedback (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT,
            generated_sql TEXT,
            execution_success BOOLEAN,
            execution_time FLOAT,
            user_rating INTEGER, -- 1 for thumbs up, -1 for thumbs down
            user_correction TEXT,
            query_type TEXT,
            tables_used TEXT,
            timestamp DATETIME
        )
        """)
        conn.commit()
        conn.close()

    def log_query(self, data: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO query_feedback (
            query_text, generated_sql, execution_success, execution_time, 
            user_rating, query_type, tables_used, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['query_text'], data['generated_sql'], data['execution_success'], 
            data['execution_time'], data.get('user_rating', 0), data.get('query_type', 'unknown'),
            json.dumps(data.get('tables_used', [])), datetime.now()
        ))
        conn.commit()
        conn.close()

class PromptOptimizer:
    def __init__(self, feedback_db: str):
        self.feedback_db = feedback_db

    def get_few_shot_examples(self, top_k: int = 5):
        conn = sqlite3.connect(self.feedback_db)
        # Get highly rated or successful queries
        query = "SELECT query_text, generated_sql FROM query_feedback WHERE execution_success = 1 AND user_rating >= 0 ORDER BY query_id DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(top_k,))
        conn.close()
        
        examples = ""
        for _, row in df.iterrows():
            examples += f"Question: {row['query_text']}\nSQL: {row['generated_sql']}\n\n"
        return examples

class FeedbackAnalyzer:
    def __init__(self, feedback_db: str):
        self.feedback_db = feedback_db

    def generate_weekly_report(self):
        conn = sqlite3.connect(self.feedback_db)
        df = pd.read_sql_query("SELECT * FROM query_feedback", conn)
        conn.close()
        
        if df.empty: return "No data available."
        
        total_queries = len(df)
        success_rate = df['execution_success'].mean() * 100
        
        # Identify failure patterns (simplified)
        report = f"## Weekly Performance Report\n"
        report += f"- **Total Queries**: {total_queries}\n"
        report += f"- **Success Rate**: {success_rate:.2f}%\n"
        report += f"- **Avg Latency**: {df['execution_time'].mean():.2f}s\n"
        
        return report

if __name__ == "__main__":
    fm = FeedbackManager()
    print("Feedback system initialized.")
