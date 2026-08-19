from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.base import entity_conn
from talkingdb_nel.services.namespace import store
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.namespace.versioning import (
    commit_namespace,
    purge_namespace_data,
    rollback_namespace,
)

router = APIRouter(
    prefix="/api/namespaces",
    tags=["Namespaces"],
)


class NamespaceCreateRequest(BaseModel):
    name: str = Field(..., description="Unique identifier for the namespace.")
    description: Optional[str] = Field(
        None, description="Human-readable description of this namespace."
    )


class NamespaceResponse(BaseModel):
    name: str = Field(..., description="Unique identifier for the namespace.")
    description: Optional[str] = Field(None, description="Human-readable description.")
    created_at: str = Field(..., description="ISO-8601 creation timestamp (UTC).")


class NamespaceUpdateRequest(BaseModel):
    description: Optional[str] = Field(None, description="New description.")


class CommitCreateRequest(BaseModel):
    message: str = Field(..., description="Description of what this commit changes.")


class CommitResponse(BaseModel):
    commit_id: str = Field(..., description="Unique identifier for this commit.")
    parent_commit_id: Optional[str] = Field(
        None, description="The commit this one was created on top of, if any."
    )
    message: str = Field(..., description="Description of what this commit changes.")
    created_at: str = Field(..., description="ISO-8601 creation timestamp (UTC).")


class CommitDetailResponse(CommitResponse):
    snapshot: Dict[str, Any] = Field(
        ..., description="Full entity graph + regex rules captured at this commit."
    )


class GraphResponse(BaseModel):
    directed: bool = Field(..., description="Whether facts are directional.")
    multigraph: bool = Field(
        ..., description="Whether multiple facts can connect the same two entities."
    )
    nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Entities, as graph nodes."
    )
    edges: List[Dict[str, Any]] = Field(
        default_factory=list, description="Facts, as graph edges."
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=NamespaceResponse,
    summary="Create a namespace",
    description="Registers a new, fully isolated training namespace.",
)
def create_new_namespace(payload: NamespaceCreateRequest) -> NamespaceResponse:
    try:
        return store.create_namespace(
            entity_conn,
            name=payload.name,
            description=payload.description,
        )
    except store.NamespaceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Namespace '{exc}' already exists",
        ) from exc


@router.get(
    "",
    response_model=List[NamespaceResponse],
    summary="List namespaces",
    description="Returns every namespace currently registered.",
)
def get_all_namespaces() -> List[NamespaceResponse]:
    return store.list_namespaces(entity_conn)


@router.get(
    "/{namespace}",
    response_model=NamespaceResponse,
    summary="Get a namespace",
    description="Returns a single namespace by name. 404 if it doesn't exist.",
)
def get_namespace_by_name(namespace: str) -> NamespaceResponse:
    result = store.get_namespace(entity_conn, namespace)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Namespace '{namespace}' not found",
        )

    return result


@router.patch(
    "/{namespace}",
    response_model=NamespaceResponse,
    summary="Update a namespace",
    description="Updates a namespace's description. 404 if it doesn't exist.",
)
def update_namespace_by_name(
    namespace: str,
    payload: NamespaceUpdateRequest,
) -> NamespaceResponse:
    try:
        return store.update_namespace(entity_conn, namespace, payload.description)
    except store.NamespaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Namespace '{exc}' not found",
        ) from exc


@router.delete(
    "/{namespace}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a namespace",
    description=(
        "Permanently deletes a namespace and all its entities, facts, "
        "regex rules, fuzzy-match dictionary, and commit history. "
        "This cannot be undone."
    ),
)
def delete_namespace_by_name(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> None:
    purge_namespace_data(bundle)


@router.post(
    "/{namespace}/commits",
    status_code=status.HTTP_201_CREATED,
    response_model=CommitResponse,
    summary="Commit a namespace's working copy",
    description=(
        "Snapshots the namespace's current entity graph and regex rules "
        "as a new commit, so this training state can be returned to later."
    ),
)
def create_namespace_commit(
    payload: CommitCreateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> CommitResponse:
    return commit_namespace(bundle, payload.message)


@router.get(
    "/{namespace}/commits",
    response_model=List[CommitResponse],
    summary="List a namespace's commit history",
    description="Returns every commit for this namespace, most recent first.",
)
def get_namespace_commits(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[CommitResponse]:
    return store.list_commits(entity_conn, bundle.namespace)


@router.get(
    "/{namespace}/commits/{commit_id}",
    response_model=CommitDetailResponse,
    summary="Get a commit",
    description="Returns one commit, including its full snapshot.",
)
def get_namespace_commit(
    commit_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> CommitDetailResponse:
    result = store.get_commit(entity_conn, bundle.namespace, commit_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commit '{commit_id}' not found",
        )

    return result


@router.post(
    "/{namespace}/commits/{commit_id}/rollback",
    status_code=status.HTTP_201_CREATED,
    response_model=CommitResponse,
    summary="Roll back to a prior commit",
    description=(
        "Restores the namespace's entity graph and regex rules to a prior "
        "commit's state, then records the rollback itself as a new commit "
        "(history is never destroyed)."
    ),
)
def rollback_namespace_commit(
    commit_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> CommitResponse:
    try:
        return rollback_namespace(bundle, commit_id)
    except store.CommitNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commit '{exc}' not found",
        ) from exc


@router.get(
    "/{namespace}/graph",
    response_model=GraphResponse,
    summary="Get the entity graph",
    description="Returns the namespace's entities and facts as a graph.",
)
def get_namespace_graph(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> GraphResponse:
    return bundle.entity_model.g_json()
