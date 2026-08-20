import csv
import io
import json


class BulkFormatError(Exception):
    """Raised when bulk upload content can't be parsed in the requested format."""


def parse_bulk_rows(format: str, content: str) -> list[dict]:
    if format == "json":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise BulkFormatError(f"Invalid JSON: {exc}") from exc

        if not isinstance(data, list):
            raise BulkFormatError("JSON content must be an array of row objects")

        return data

    if format == "csv":
        return list(csv.DictReader(io.StringIO(content)))

    raise BulkFormatError(f"Unsupported format: {format!r} (expected 'csv' or 'json')")
