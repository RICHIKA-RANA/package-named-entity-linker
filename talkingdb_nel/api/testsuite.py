from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.testsuite import store
from talkingdb_nel.services.testsuite.bulk import bulk_create_test_cases
from talkingdb_nel.services.testsuite.runner import (
    CaseNotRunError,
    accept_test_case,
    reject_test_case,
    run_test_suite,
)

router = APIRouter(
    prefix="/api/namespaces/{namespace}",
    tags=["Test Suite"],
)


class ExpectedPair(BaseModel):
    surface_text: str = Field(..., description="Surface text expected to be matched.")
    entity_id: str = Field(..., description="entity_id it should link to.")


class TestCaseCreateRequest(BaseModel):
    message_text: str = Field(..., description="Message to run through extraction.")
    word_correction: bool = Field(False, description="Enable fuzzy typo correction.")
    expected: Optional[List[ExpectedPair]] = Field(
        None,
        description=(
            "Expected (surface_text, entity_id) pairs. Omit if unknown - "
            "use accept/reject after a run to establish this instead."
        ),
    )


class TestCaseUpdateRequest(BaseModel):
    message_text: Optional[str] = None
    word_correction: Optional[bool] = None
    expected: Optional[List[ExpectedPair]] = None
    review_status: Optional[str] = None


class TestCaseResponse(BaseModel):
    id: str
    namespace: str
    message_text: str
    word_correction: bool
    expected: Optional[List[ExpectedPair]] = None
    review_status: str = Field(..., description="'pending' | 'accepted' | 'rejected'")
    created_at: str


class BulkUploadRequest(BaseModel):
    format: str = Field(..., description="'csv' or 'json'.")
    content: str = Field(..., description="Raw file content.")


class BulkUploadResponse(BaseModel):
    created: int
    errors: List[Dict[str, Any]]


class TestRunCreateRequest(BaseModel):
    triggering_commit_id: Optional[str] = Field(
        None,
        description="Informational only - the training commit active for this run.",
    )


class TestRunResponse(BaseModel):
    id: str
    namespace: str
    created_at: str
    triggering_commit_id: Optional[str] = None


class TestRunResultResponse(BaseModel):
    id: str
    run_id: str
    test_case_id: str
    actual: List[ExpectedPair]
    passed: Optional[bool]
    status_label: str = Field(
        ...,
        description="'pass' | 'regression' | 'fixed' | 'fail' | 'new' | 'needs_review'",
    )


class TestRunSummaryResponse(BaseModel):
    run: TestRunResponse
    results: List[TestRunResultResponse]
    accuracy: Optional[float] = Field(
        None,
        description="passed / graded, excluding needs_review. Null if none graded",
    )
    graded_count: int
    passed_count: int
    total_count: int


def _expected_to_dicts(expected: Optional[List[ExpectedPair]]):
    if expected is None:
        return None

    return [pair.model_dump() for pair in expected]


@router.post(
    "/test-cases",
    status_code=status.HTTP_201_CREATED,
    response_model=TestCaseResponse,
    summary="Create a test case",
    description="Adds a single test case for this namespace's accuracy suite.",
)
def create_test_case(
    payload: TestCaseCreateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> TestCaseResponse:
    return store.create_test_case(
        bundle.entity_conn,
        bundle.namespace,
        message_text=payload.message_text,
        word_correction=payload.word_correction,
        expected=_expected_to_dicts(payload.expected),
    )


@router.post(
    "/test-cases/bulk",
    response_model=BulkUploadResponse,
    summary="Bulk-upload test cases",
    description=(
        "Creates many test cases from CSV or JSON content (columns/fields: "
        "message_text, word_correction, expected). Rows with expected left "
        "blank are unlabeled - use accept/reject after a run."
    ),
)
def bulk_upload_test_cases(
    payload: BulkUploadRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> BulkUploadResponse:
    return bulk_create_test_cases(
        bundle.entity_conn, bundle.namespace, payload.format, payload.content
    )


@router.get(
    "/test-cases",
    response_model=List[TestCaseResponse],
    summary="List test cases",
    description="Returns every test case registered for this namespace.",
)
def get_all_test_cases(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[TestCaseResponse]:
    return store.list_test_cases(bundle.entity_conn, bundle.namespace)


@router.patch(
    "/test-cases/{test_case_id}",
    response_model=TestCaseResponse,
    summary="Update a test case",
    description="Updates a test case's message, expected pairs, and/or review status.",
)
def update_test_case(
    test_case_id: str,
    payload: TestCaseUpdateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> TestCaseResponse:
    updates = payload.model_dump(exclude_unset=True)

    if "expected" in updates:
        updates["expected"] = _expected_to_dicts(payload.expected)

    try:
        return store.update_test_case(
            bundle.entity_conn, bundle.namespace, test_case_id, **updates
        )
    except store.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{exc}' not found",
        ) from exc


@router.delete(
    "/test-cases/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test case",
    description="Permanently deletes a test case and its run history.",
)
def delete_test_case(
    test_case_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> None:
    try:
        store.delete_test_case(bundle.entity_conn, bundle.namespace, test_case_id)
    except store.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{exc}' not found",
        ) from exc


@router.post(
    "/test-cases/{test_case_id}/accept",
    response_model=TestCaseResponse,
    summary="Accept a test case's latest result",
    description=(
        "Sets this case's expected pairs to whatever its most recent run "
        "actually produced, and marks it accepted - the ground-truth flow "
        "for test cases uploaded without an expected result."
    ),
)
def accept_test_case_result(
    test_case_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> TestCaseResponse:
    try:
        return accept_test_case(bundle.entity_conn, bundle.namespace, test_case_id)
    except CaseNotRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Test case '{exc}' has never been run",
        ) from exc
    except store.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{exc}' not found",
        ) from exc


@router.post(
    "/test-cases/{test_case_id}/reject",
    response_model=TestCaseResponse,
    summary="Reject a test case's latest result",
    description="Flags the current output as wrong. expected is left as-is.",
)
def reject_test_case_result(
    test_case_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> TestCaseResponse:
    try:
        return reject_test_case(bundle.entity_conn, bundle.namespace, test_case_id)
    except store.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case '{exc}' not found",
        ) from exc


@router.post(
    "/test-runs",
    status_code=status.HTTP_201_CREATED,
    response_model=TestRunSummaryResponse,
    summary="Run the test suite",
    description=(
        "Runs every test case through extraction now, labels each result "
        "relative to its previous run (pass/regression/fixed/fail/new/"
        "needs_review), and returns the accuracy summary."
    ),
)
def create_test_run(
    payload: TestRunCreateRequest = TestRunCreateRequest(),
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> TestRunSummaryResponse:
    return run_test_suite(bundle, bundle.entity_conn, payload.triggering_commit_id)


@router.get(
    "/test-runs",
    response_model=List[TestRunResponse],
    summary="List test runs",
    description="Returns every past run for this namespace, most recent first.",
)
def get_all_test_runs(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[TestRunResponse]:
    return store.list_runs(bundle.entity_conn, bundle.namespace)


@router.get(
    "/test-runs/{run_id}",
    response_model=List[TestRunResultResponse],
    summary="Get a test run's results",
    description="Returns one run's full per-case results.",
)
def get_test_run_results(
    run_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[TestRunResultResponse]:
    return store.list_run_results(bundle.entity_conn, run_id)
