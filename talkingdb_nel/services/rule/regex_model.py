from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict

from smart_slugify import slugify


@dataclass(slots=True)
class RegexRule:
    pattern: str
    compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self):
        self.compiled = re.compile(self.pattern, re.IGNORECASE)


class RegexModel:
    def __init__(self):
        self.rules: Dict[str, list[RegexRule]] = {}

    @staticmethod
    def make_id(name: str) -> str:
        return f"regex::{slugify(name)}"

    @staticmethod
    def init_db(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;

            CREATE TABLE IF NOT EXISTS regex_rules (
                rule_id TEXT NOT NULL,
                pattern TEXT NOT NULL,
                created_at TEXT,
                PRIMARY KEY(rule_id, pattern)
            );

            CREATE INDEX IF NOT EXISTS idx_regex_rules_rule_id
            ON regex_rules(rule_id);
            """
        )

    @classmethod
    def load(cls, conn: sqlite3.Connection) -> "RegexModel":
        model = cls()

        cursor = conn.execute(
            """
            SELECT rule_id, pattern
            FROM regex_rules
            """
        )

        for rule_id, pattern in cursor:
            try:
                model.add_rule(rule_id, pattern)
            except re.error:
                # Ignore invalid regex stored in DB
                continue

        return model

    def save(
        self,
        conn: sqlite3.Connection,
        overwrite: bool = True,
    ) -> None:
        cursor = conn.cursor()

        if overwrite:
            cursor.execute("DELETE FROM regex_rules")

        now = datetime.now(UTC).isoformat()

        for rule_id, rules in self.rules.items():
            cursor.executemany(
                """
                INSERT OR REPLACE
                INTO regex_rules(rule_id, pattern, created_at)
                VALUES (?, ?, ?)
                """,
                [
                    (rule_id, rule.pattern, now)
                    for rule in rules
                ],
            )

        conn.commit()

    def add_rule(
        self,
        rule_id: str,
        pattern: str,
    ) -> None:
        rule = RegexRule(pattern)

        self.rules.setdefault(rule_id, []).append(rule)

    def remove_rule(self, rule_id: str) -> None:
        self.rules.pop(rule_id, None)

    def clear(self) -> None:
        self.rules.clear()

    def to_dict(self):
        return {
            rule_id: [r.pattern for r in rules]
            for rule_id, rules in self.rules.items()
        }
