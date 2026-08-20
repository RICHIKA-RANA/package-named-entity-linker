from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import (
    FactNotFoundError,
    create_fact,
    delete_fact,
    get_fact,
    list_facts,
    update_fact,
)
from talkingdb_nel.services.namespace.registry import NamespaceBundle

router = APIRouter(
    prefix="/api/namespaces/{namespace}/facts",
    tags=["Facts"],
)


class FactCreateRequest(BaseModel):
    source: str = Field(..., description="entity_id of the fact's source entity.")
    predicate: str = Field(
        ..., description="Relationship type connecting source and target."
    )
    target: str = Field(..., description="entity_id of the fact's target entity.")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary additional attributes to attach to this fact.",
    )


class FactResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Unique identifier generated for this fact.")
    source: str = Field(..., description="entity_id of the fact's source entity.")
    target: str = Field(..., description="entity_id of the fact's target entity.")
    predicate: str = Field(
        ..., description="Relationship type connecting source and target."
    )


class FactUpdateRequest(BaseModel):
    predicate: Optional[str] = Field(
        None, description="New predicate. Omit to leave unchanged."
    )
    attributes: Optional[Dict[str, Any]] = Field(
        None, description="Replace all attributes. Omit to leave unchanged."
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FactResponse,
    summary="Create a fact",
    description="Creates a relationship (fact) between two entities.",
)
def create_new_fact(
    payload: FactCreateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> FactResponse:
    return create_fact(
        bundle,
        source=payload.source,
        predicate=payload.predicate,
        target=payload.target,
        **payload.attributes,
    )


@router.get(
    "",
    response_model=List[FactResponse],
    summary="List facts",
    description="Returns every fact currently registered in this namespace.",
)
def get_all_facts(
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> List[FactResponse]:
    return list_facts(bundle)


@router.get(
    "/{fact_id}",
    response_model=FactResponse,
    summary="Get a fact",
    description="Returns a single fact by id. 404 if it doesn't exist.",
)
def get_fact_by_id(
    fact_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> FactResponse:
    result = get_fact(bundle, fact_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact '{fact_id}' not found",
        )

    return result


@router.patch(
    "/{fact_id}",
    response_model=FactResponse,
    summary="Update a fact",
    description=(
        "Updates a fact's predicate and/or attributes. 404 if it doesn't exist."
    ),
)
def update_fact_by_id(
    fact_id: str,
    payload: FactUpdateRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> FactResponse:
    try:
        return update_fact(
            bundle,
            fact_id=fact_id,
            predicate=payload.predicate,
            attributes=payload.attributes,
        )
    except FactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact '{exc}' not found",
        ) from exc


@router.delete(
    "/{fact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a fact",
    description="Permanently deletes a fact. 404 if it doesn't exist.",
)
def delete_fact_by_id(
    fact_id: str,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> None:
    try:
        delete_fact(bundle, fact_id=fact_id)
    except FactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact '{exc}' not found",
        ) from exc
