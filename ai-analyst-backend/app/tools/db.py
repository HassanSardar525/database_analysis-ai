import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")

    def execute_query(self, sql: str):
        """Executes SELECT queries safely."""
        conn = psycopg2.connect(self.db_url)
        try:
          with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            results = cur.fetchall()
            
            # --- NEW: Convert Decimal to Float for JSON compatibility ---
            clean_results = []
            for row in results:
                # Convert the RealDictRow to a regular dict
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if isinstance(value, Decimal):
                        row_dict[key] = float(value)
                clean_results.append(row_dict)
                
            return clean_results
        finally:
          conn.close()

    def get_schema(self):
        """Fetches table and column info for the AI's context."""
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public';
        """
        raw_schema = self.execute_query(query)
        schema_str = "Database Schema:\n"
        for row in raw_schema:
            schema_str += f"- {row['table_name']}.{row['column_name']} ({row['data_type']})\n"
        return schema_str

db_manager = DatabaseManager()