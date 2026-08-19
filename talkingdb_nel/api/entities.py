from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    RegexRuleNotFoundError,
    SurfaceTextAlreadyExistsError,
    add_surface_text,
    bulk_create_entities,
    create_entity,
    create_regex,
    delete_entity,
    delete_regex_rule,
    get_entity,
    list_entities,
    list_regex_rules,
    update_entity,
    update_regex_rule,
)
from talkingdb_nel.services.namespace.registry import NamespaceBundle

router = APIRouter(
    prefix="/api/namespaces/{namespace}/entities",
    tags=["Entities"],
)


class EntityCreateRequest(BaseModel):
    entity_id: str = Field(..., description="Unique identifier for the entity.")
    label: Optional[str] = Field(
        None,
        description="Human-readable label. Defaults to entity_id when omitted.",
    )
    surface_texts: List[str] = Field(
        default_factory=list,
        description="Surface texts (aliases) this entity should be recognized by.",
    )


class EntityResponse(BaseModel):
    entity_id: str = Field(..., description="Unique identifier for the entity.")
    label: str = Field(..., description="Human-readable label.")
    surface_texts: List[str] = Field(
        ..., description="Surface texts this entity is recognized by."
    )


class EntityUpdateRequest(BaseModel):
    label: Optional[str] = Field(
        None, description="New label. Omit to leave unchanged."
    )
    surface_texts: Optional[List[str]] = Field(
        None, description="Replace the full surface-text list. Omit to leave unchanged."
    )


class SurfaceTextAddRequest(BaseModel):
    surface_text: str = Field(..., description="Surface text to add to the entity.")


class RegexRuleCreateRequest(BaseModel):
    regex: str = Field(..., description="Regular expression pattern for this entity.")


class RegexRuleResponse(BaseModel):
    entity_id: str = Field(..., description="Entity this rule was added to.")
    regex: str = Field(..., description="Regular expression pattern.")


class BulkUploadRequest(BaseModel):
    format: str = Field(..., description="'csv' or 'json'.")
    content: str = Field(..., description="Raw file content.")


class BulkUploadResponse(BaseModel):
    created: int = Field(..., description="Number of entities created.")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Per-row errors, if any."
    )


class RegexRuleDeleteRequest(BaseModel):
    regex: str = Field(..., description="Exact pattern to delete.")


class RegexRuleUpdateRequest(BaseModel):
    old_regex: str = Field(..., description="Exact pattern to replace.")
    new_regex: str = Field(..., description="Replacement pattern.")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EntityResponse,
    summary="Create an entity",
    description=(
        "Registers a new canonical entity with an optional label and "
        "initial surface texts. Fails with 409 if entity_id already exists."
    ),
)
def create_new_entity(
    payload: EntityCreateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> EntityResponse:
    try:
        return create_entity(
            bundle,
            entity_id=payload.entity_id,
            label=payload.label,
            surface_texts=payload.surface_texts,
        )
    except EntityAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entity '{exc}' already exists",
        ) from exc


@router.post(
    "/bulk",
    response_model=BulkUploadResponse,
    summary="Bulk-create entities",
    description=(
        "Creates many entities from CSV or JSON content (columns/fields: "
        "entity_id, label, surface_texts - pipe-separated in CSV, an "
        "array in JSON). Per-row errors (e.g. duplicate entity_id) are "
        "collected rather than failing the whole upload."
    ),
)
def bulk_upload_entities(
    payload: BulkUploadRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> BulkUploadResponse:
    return bulk_create_entities(bundle, payload.format, payload.content)


@router.get(
    "",
    response_model=List[EntityResponse],
    summary="List entities",
    description="Returns every entity currently registered in this namespace.",
)
def get_all_entities(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[EntityResponse]:
    return list_entities(bundle)


@router.get(
    "/{entity_id}",
    response_model=EntityResponse,
    summary="Get an entity",
    description="Returns a single entity by id. 404 if it doesn't exist.",
)
def get_entity_by_id(
    entity_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> EntityResponse:
    result = get_entity(bundle, entity_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found",
        )

    return result


@router.patch(
    "/{entity_id}",
    response_model=EntityResponse,
    summary="Update an entity",
    description=(
        "Updates an entity's label and/or its full surface-text list. "
        "404 if the entity doesn't exist."
    ),
)
def update_entity_by_id(
    entity_id: str,
    payload: EntityUpdateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> EntityResponse:
    try:
        return update_entity(
            bundle,
            entity_id=entity_id,
            label=payload.label,
            surface_texts=payload.surface_texts,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{exc}' not found",
        ) from exc


@router.delete(
    "/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an entity",
    description=(
        "Permanently deletes an entity and every fact referencing it. "
        "404 if the entity doesn't exist."
    ),
)
def delete_entity_by_id(
    entity_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> None:
    try:
        delete_entity(bundle, entity_id=entity_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{exc}' not found",
        ) from exc


@router.post(
    "/{entity_id}/surface-texts",
    status_code=status.HTTP_201_CREATED,
    response_model=EntityResponse,
    summary="Add a surface text to an entity",
    description=(
        "Registers an additional surface text (alias) for an existing "
        "entity. 404 if the entity doesn't exist, 409 if it already has "
        "this surface text."
    ),
)
def add_entity_surface_text(
    entity_id: str,
    payload: SurfaceTextAddRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> EntityResponse:
    try:
        return add_surface_text(
            bundle,
            entity_id=entity_id,
            surface_text=payload.surface_text,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{exc}' not found",
        ) from exc
    except SurfaceTextAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Surface text '{exc}' already exists on this entity",
        ) from exc


@router.post(
    "/{entity_id}/regex-rules",
    status_code=status.HTTP_201_CREATED,
    response_model=RegexRuleResponse,
    summary="Add a regex rule to an entity",
    description=(
        "Registers a regular-expression matching rule for an existing "
        "entity. 404 if the entity doesn't exist."
    ),
)
def add_entity_regex_rule(
    entity_id: str,
    payload: RegexRuleCreateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> RegexRuleResponse:
    try:
        return create_regex(bundle, entity_id=entity_id, regex=payload.regex)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{exc}' not found",
        ) from exc


@router.get(
    "/{entity_id}/regex-rules",
    response_model=List[str],
    summary="List an entity's regex rules",
    description="Returns every regex pattern registered for this entity.",
)
def get_entity_regex_rules(
    entity_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[str]:
    try:
        return list_regex_rules(bundle, entity_id=entity_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{exc}' not found",
        ) from exc


@router.patch(
    "/{entity_id}/regex-rules",
    response_model=RegexRuleResponse,
    summary="Replace a regex rule",
    description=(
        "Replaces one existing pattern with a new one. 404 if the old "
        "pattern doesn't exist for this entity."
    ),
)
def update_entity_regex_rule(
    entity_id: str,
    payload: RegexRuleUpdateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> RegexRuleResponse:
    try:
        return update_regex_rule(
            bundle,
            entity_id=entity_id,
            old_pattern=payload.old_regex,
            new_pattern=payload.new_regex,
        )
    except RegexRuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regex pattern '{exc}' not found",
        ) from exc


@router.delete(
    "/{entity_id}/regex-rules",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a regex rule",
    description=(
        "Deletes one specific pattern (identified by an exact match in "
        "the request body, not the URL, since a pattern may contain "
        "'/'). 404 if it doesn't exist for this entity."
    ),
)
def delete_entity_regex_rule(
    entity_id: str,
    payload: RegexRuleDeleteRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> None:
    try:
        delete_regex_rule(bundle, entity_id=entity_id, pattern=payload.regex)
    except RegexRuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regex pattern '{exc}' not found",
        ) from exc
