import json
import sqlite3

import pytest

from talkingdb_nel.services.testsuite import store
from talkingdb_nel.services.testsuite.bulk import bulk_create_test_cases


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store.init_db(connection)
    yield connection
    connection.close()


def test_bulk_create_test_cases_json_mixed_labeled_and_unlabeled(conn):
    rows = [
        {
            "message_text": "mayank works at acme",
            "expected": [{"surface_text": "mayank", "entity_id": "mayank"}],
        },
        {"message_text": "unlabeled query"},
    ]

    result = bulk_create_test_cases(conn, "ns1", "json", json.dumps(rows))

    assert result == {"created": 2, "errors": []}

    cases = store.list_test_cases(conn, "ns1")
    assert cases[0]["expected"] == [{"surface_text": "mayank", "entity_id": "mayank"}]
    assert cases[1]["expected"] is None


def test_bulk_create_test_cases_csv_with_json_encoded_expected(conn):
    expected_cell = '"[{""surface_text"": ""mayank"", ""entity_id"": ""mayank""}]"'
    content = f"message_text,word_correction,expected\nhi mayank,true,{expected_cell}\n"

    result = bulk_create_test_cases(conn, "ns1", "csv", content)

    assert result == {"created": 1, "errors": []}

    cases = store.list_test_cases(conn, "ns1")
    assert cases[0]["message_text"] == "hi mayank"
    assert cases[0]["word_correction"] is True
    assert cases[0]["expected"] == [{"surface_text": "mayank", "entity_id": "mayank"}]


def test_bulk_create_test_cases_csv_blank_expected_is_unlabeled(conn):
    content = "message_text,word_correction,expected\nhello,false,\n"

    result = bulk_create_test_cases(conn, "ns1", "csv", content)

    assert result == {"created": 1, "errors": []}
    assert store.list_test_cases(conn, "ns1")[0]["expected"] is None


def test_bulk_create_test_cases_collects_row_errors(conn):
    rows = [{"message_text": "ok"}, {"no_message_text_here": True}]

    result = bulk_create_test_cases(conn, "ns1", "json", json.dumps(rows))

    assert result["created"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row"] == 1


def test_bulk_create_test_cases_invalid_expected_json_collected_as_error(conn):
    content = "message_text,word_correction,expected\nhello,false,not valid json\n"

    result = bulk_create_test_cases(conn, "ns1", "csv", content)

    assert result["created"] == 0
    assert len(result["errors"]) == 1
