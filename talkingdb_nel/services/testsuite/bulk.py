import json
import sqlite3

from talkingdb_nel.services.bulk import parse_bulk_rows
from talkingdb_nel.services.testsuite import store

TRUTHY = {"true", "1", "yes"}


def bulk_create_test_cases(
    conn: sqlite3.Connection, namespace: str, format: str, content: str
) -> dict:
    rows = parse_bulk_rows(format, content)

    created = 0
    errors = []

    for index, row in enumerate(rows):
        try:
            message_text = row["message_text"]
            word_correction_raw = row.get("word_correction", False)

            if isinstance(word_correction_raw, str):
                word_correction = word_correction_raw.strip().lower() in TRUTHY
            else:
                word_correction = bool(word_correction_raw)

            expected_raw = row.get("expected")

            if isinstance(expected_raw, str) and expected_raw.strip():
                expected = json.loads(expected_raw)
            elif isinstance(expected_raw, list):
                expected = expected_raw
            else:
                expected = None

            store.create_test_case(
                conn,
                namespace,
                message_text=message_text,
                word_correction=word_correction,
                expected=expected,
            )
            created += 1
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"row": index, "error": str(exc)})

    return {"created": created, "errors": errors}
