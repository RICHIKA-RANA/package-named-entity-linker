import json
import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path=":memory:"):
        self.db_path = str(Path(db_path))
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY,
                frequency INTEGER NOT NULL,
                suggestions TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deletes (
                delete_word TEXT NOT NULL,
                real_word TEXT NOT NULL,
                PRIMARY KEY(delete_word, real_word)
            );

            CREATE INDEX IF NOT EXISTS idx_delete_word
            ON deletes(delete_word);
            """
        )

        self.conn.commit()

    # ------------------------------------------------------------------
    # metadata
    # ------------------------------------------------------------------

    def set_metadata(self, key, value):
        self.conn.execute(
            """
            INSERT INTO metadata(key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def get_metadata(self, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM metadata WHERE key=?",
            (key,),
        ).fetchone()

        if row is None:
            return default

        return json.loads(row["value"])

    # ------------------------------------------------------------------
    # words
    # ------------------------------------------------------------------

    def has_word(self, word):
        row = self.conn.execute(
            "SELECT 1 FROM words WHERE word=?",
            (word,),
        ).fetchone()

        return row is not None

    def get_frequency(self, word):
        row = self.conn.execute(
            "SELECT frequency FROM words WHERE word=?",
            (word,),
        ).fetchone()

        return 0 if row is None else row["frequency"]

    def increment_frequency(self, word):
        self.conn.execute(
            """
            UPDATE words
            SET frequency = frequency + 1
            WHERE word=?
            """,
            (word,),
        )
        self.conn.commit()

    def insert_word(self, word):
        self.conn.execute(
            """
            INSERT INTO words(word, frequency, suggestions)
            VALUES (?, 1, '[]')
            """,
            (word,),
        )
        self.conn.commit()

    def get_suggestions(self, word):
        row = self.conn.execute(
            """
            SELECT suggestions
            FROM words
            WHERE word=?
            """,
            (word,),
        ).fetchone()

        if row is None:
            return []

        return json.loads(row["suggestions"])

    def add_suggestion(self, delete_word, real_word):
        row = self.conn.execute(
            """
            SELECT suggestions
            FROM words
            WHERE word=?
            """,
            (delete_word,),
        ).fetchone()

        if row is None:
            self.conn.execute(
                """
                INSERT INTO words(word, frequency, suggestions)
                VALUES (?, 0, ?)
                """,
                (
                    delete_word,
                    json.dumps([real_word]),
                ),
            )

            self.conn.commit()
            return

        suggestions = json.loads(row["suggestions"])

        if real_word not in suggestions:
            suggestions.append(real_word)

            self.conn.execute(
                """
                UPDATE words
                SET suggestions=?
                WHERE word=?
                """,
                (
                    json.dumps(suggestions),
                    delete_word,
                ),
            )

            self.conn.commit()

    def word_count(self):
        row = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM words
            WHERE frequency > 0
            """
        ).fetchone()

        return row[0]

    # ------------------------------------------------------------------
    # delete mappings
    # ------------------------------------------------------------------

    def add_delete(self, delete_word, real_word):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO deletes(delete_word, real_word)
            VALUES (?, ?)
            """,
            (
                delete_word,
                real_word,
            ),
        )

        self.conn.commit()

    def get_delete_words(self, delete_word):
        rows = self.conn.execute(
            """
            SELECT real_word
            FROM deletes
            WHERE delete_word=?
            """,
            (delete_word,),
        ).fetchall()

        return [r["real_word"] for r in rows]

    # ------------------------------------------------------------------

    def close(self):
        self.conn.close()
