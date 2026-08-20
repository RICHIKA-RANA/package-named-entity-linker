import json

import pytest

from talkingdb_nel.services import bulk


def test_parse_bulk_rows_json():
    content = json.dumps([{"a": 1}, {"a": 2}])

    assert bulk.parse_bulk_rows("json", content) == [{"a": 1}, {"a": 2}]


def test_parse_bulk_rows_json_invalid():
    with pytest.raises(bulk.BulkFormatError):
        bulk.parse_bulk_rows("json", "{not valid json")


def test_parse_bulk_rows_json_must_be_array():
    with pytest.raises(bulk.BulkFormatError):
        bulk.parse_bulk_rows("json", json.dumps({"a": 1}))


def test_parse_bulk_rows_csv():
    content = "a,b\n1,2\n3,4\n"

    assert bulk.parse_bulk_rows("csv", content) == [
        {"a": "1", "b": "2"},
        {"a": "3", "b": "4"},
    ]


def test_parse_bulk_rows_unsupported_format():
    with pytest.raises(bulk.BulkFormatError):
        bulk.parse_bulk_rows("yaml", "a: 1")
