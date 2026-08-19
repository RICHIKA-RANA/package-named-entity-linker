import sqlite3

from talkingdb_nel.services.entity.entity import get_surface_texts
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.testsuite import store


class CaseNotRunError(Exception):
    """Raised when accepting a test case that has never been run."""


def flatten_actual(extraction_result: dict) -> list[dict]:
    """
    Reduces an extraction response to the (surface_text, entity_id) pairs a
    trainer actually cares about validating - ignoring spans/scores, which
    are too brittle to assert on in a regression suite.
    """

    pairs = set()

    for match in extraction_result.get("universal_entities", []):
        for linked in match.get("entities", []):
            pairs.add((match["surface_text"], linked["entity_id"]))

    for match in extraction_result.get("regex_entities", []):
        pairs.add((match["surface_text"], match["rule"]))

    return [
        {"surface_text": surface_text, "entity_id": entity_id}
        for surface_text, entity_id in sorted(pairs)
    ]


def _pairs_set(pairs: list[dict] | None) -> set:
    if not pairs:
        return set()

    return {(pair["surface_text"], pair["entity_id"]) for pair in pairs}


def compute_status_label(
    expected: list[dict] | None,
    passed: bool | None,
    previous_passed: bool | None,
) -> str:
    if expected is None:
        return "needs_review"

    if previous_passed is None:
        return "new"

    if previous_passed and passed:
        return "pass"

    if previous_passed and not passed:
        return "regression"

    if not previous_passed and passed:
        return "fixed"

    return "fail"


def run_test_suite(
    bundle: NamespaceBundle,
    conn: sqlite3.Connection,
    triggering_commit_id: str | None = None,
) -> dict:
    test_cases = store.list_test_cases(conn, bundle.namespace)

    computed = []

    for case in test_cases:
        extraction = get_surface_texts(
            bundle,
            message_text=case["message_text"],
            word_correction=case["word_correction"],
        )
        actual = flatten_actual(extraction)

        expected = case["expected"]
        passed = (
            None if expected is None else _pairs_set(expected) == _pairs_set(actual)
        )

        previous = store.get_latest_result_for_case(conn, case["id"])
        previous_passed = previous["passed"] if previous else None

        computed.append(
            {
                "test_case_id": case["id"],
                "actual": actual,
                "passed": passed,
                "status_label": compute_status_label(expected, passed, previous_passed),
            }
        )

    run = store.create_run(conn, bundle.namespace, triggering_commit_id)

    results = [
        store.create_run_result(
            conn,
            run["id"],
            item["test_case_id"],
            item["actual"],
            item["passed"],
            item["status_label"],
        )
        for item in computed
    ]

    graded = [result for result in results if result["passed"] is not None]
    passed_count = sum(1 for result in graded if result["passed"])

    return {
        "run": run,
        "results": results,
        "accuracy": (passed_count / len(graded)) if graded else None,
        "graded_count": len(graded),
        "passed_count": passed_count,
        "total_count": len(results),
    }


def accept_test_case(
    conn: sqlite3.Connection, namespace: str, test_case_id: str
) -> dict:
    latest = store.get_latest_result_for_case(conn, test_case_id)

    if latest is None:
        raise CaseNotRunError(test_case_id)

    return store.update_test_case(
        conn,
        namespace,
        test_case_id,
        expected=latest["actual"],
        review_status="accepted",
    )


def reject_test_case(
    conn: sqlite3.Connection, namespace: str, test_case_id: str
) -> dict:
    return store.update_test_case(
        conn,
        namespace,
        test_case_id,
        review_status="rejected",
    )
