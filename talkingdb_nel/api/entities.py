from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    SurfaceTextAlreadyExistsError,
    add_surface_text,
    create_entity,
    create_regex,
    get_entity,
    list_entities,
)
from talkingdb_nel.services.namespace.registry import NamespaceBundle

router = APIRouter(
    prefix="/namespaces/{namespace}/entities",
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


class SurfaceTextAddRequest(BaseModel):
    surface_text: str = Field(..., description="Surface text to add to the entity.")


class RegexRuleCreateRequest(BaseModel):
    regex: str = Field(..., description="Regular expression pattern for this entity.")


class RegexRuleResponse(BaseModel):
    entity_id: str = Field(..., description="Entity this rule was added to.")
    regex: str = Field(..., description="Regular expression pattern.")


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
