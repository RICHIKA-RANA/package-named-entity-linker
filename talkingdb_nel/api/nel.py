from typing import List, Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from talkingdb_nel.services.entity.entity import (
    add_surface_text,
    create_entity,
    create_fact,
    create_regex,
    get_surface_texts,
)

router = APIRouter(
    prefix="/nel",
    tags=["NEL"],
)


class SurfaceTextRequest(BaseModel):
    message_text: str
    word_correction: bool = False


class EntityCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    label: str | None = None
    surface_texts: List[str] = Field(default_factory=list)


class AddSurfaceTextRequest(BaseModel):
    entity_id: str
    surface_text: str


class FactCreateRequest(BaseModel):
    source: str
    predicate: str
    target: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class RegexCreateRequest(BaseModel):
    entity_id: str
    regex: str


@router.post("/surface-text")
async def extract_surface_text(
    request: SurfaceTextRequest,
):
    return get_surface_texts(
        message_text=request.message_text,
        word_correction=request.word_correction,
    )


@router.post("/entity")
async def create_new_entity(
    request: EntityCreateRequest,
):
    return create_entity(
        request.model_dump(by_alias=True)
    )


@router.put("/surface-text")
async def add_entity_surface_text(
    request: AddSurfaceTextRequest,
):
    return add_surface_text(
        entity_id=request.entity_id,
        surface_text=request.surface_text,
    )


@router.post("/fact")
async def create_new_fact(
    request: FactCreateRequest,
):
    return create_fact(
        source=request.source,
        predicate=request.predicate,
        target=request.target,
        **request.attributes,
    )


@router.post("/regex")
async def create_new_regex(
    request: RegexCreateRequest,
):
    return create_regex(
        entity_id=request.entity_id,
        regex=request.regex,
    )