"""
=======================================================
  FAKE NEWS ANALYSER — PORTION 3: DATABASE
=======================================================
"""

import sqlite3
import os


class Database:

    def __init__(self, db_path: str = 'fake_news.db'):
        self.db_path = db_path
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            text        TEXT    NOT NULL,
            prediction  TEXT    NOT NULL,
            confidence  REAL    NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self._connect() as conn:
            conn.execute(sql)
            conn.commit()
        print(f"✔ Database ready: '{self.db_path}'")

    def save_analysis(self, text: str, prediction: str, confidence: float) -> int:
        sql = "INSERT INTO analyses (text, prediction, confidence) VALUES (?, ?, ?)"
        with self._connect() as conn:
            cursor = conn.execute(sql, (text[:500], prediction, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_history(self, limit: int = 20) -> list:
        sql = """
        SELECT id, text, prediction, confidence, analyzed_at
        FROM analyses
        ORDER BY analyzed_at DESC
        LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
        return [
            {
                'id'         : row['id'],
                'text'       : row['text'][:100] + ('...' if len(row['text']) > 100 else ''),
                'prediction' : row['prediction'],
                'confidence' : row['confidence'],
                'analyzed_at': row['analyzed_at'],
            }
            for row in rows
        ]

    def get_stats(self) -> dict:
        with self._connect() as conn:
            total      = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            fake_count = conn.execute("SELECT COUNT(*) FROM analyses WHERE prediction='FAKE'").fetchone()[0]
            real_count = conn.execute("SELECT COUNT(*) FROM analyses WHERE prediction='REAL'").fetchone()[0]
            avg_conf   = conn.execute("SELECT AVG(confidence) FROM analyses").fetchone()[0]
        return {
            'total_analyzed'  : total,
            'fake_count'      : fake_count,
            'real_count'      : real_count,
            'fake_percentage' : round(fake_count / total * 100, 1) if total else 0,
            'real_percentage' : round(real_count / total * 100, 1) if total else 0,
            'avg_confidence'  : round(avg_conf, 1) if avg_conf else 0,
        }

    # ── DELETE ONE ──────────────────────────────────
    def delete_analysis(self, item_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM analyses WHERE id = ?", (item_id,))
            conn.commit()

    # ── DELETE ALL ──────────────────────────────────
    def delete_all_analyses(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM analyses")
            conn.commit()


# ── Quick test ──────────────────────────────────────
if __name__ == '__main__':
    db = Database(':memory:')
    db.save_analysis("Scientists confirm vaccines are safe", "REAL", 92.3)
    db.save_analysis("Government hiding alien technology",   "FAKE", 88.7)
    print("\nHistory:", db.get_history())
    db.delete_analysis(1)
    print("After delete one:", db.get_history())
    db.delete_all_analyses()
    print("After delete all:", db.get_history())