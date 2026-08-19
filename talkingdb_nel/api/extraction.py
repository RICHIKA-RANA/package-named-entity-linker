from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import get_surface_texts
from talkingdb_nel.services.namespace.registry import NamespaceBundle

router = APIRouter(
    prefix="/namespaces/{namespace}/extractions",
    tags=["Extraction"],
)


class ExtractionRequest(BaseModel):
    message_text: str = Field(
        ..., description="Free text to extract and link entities from."
    )
    word_correction: bool = Field(
        False,
        description=(
            "Enable fuzzy typo correction (insertions, deletions, "
            "substitutions) when matching surface texts."
        ),
    )


class LinkedEntity(BaseModel):
    entity_id: str = Field(..., description="Entity this surface text belongs to.")
    label: str = Field(..., description="Entity's human-readable label.")
    surface_text: str = Field(
        ..., description="The trained surface text that was matched."
    )


class UniversalEntity(BaseModel):
    index: List[int] = Field(
        ..., description="[start, end] inclusive character offsets in message_text."
    )
    surface_text: str = Field(..., description="Original text matched at this span.")
    corrected_text: str = Field(
        ...,
        description="Dictionary surface text this span was matched/corrected to.",
    )
    score: float = Field(
        ...,
        description="0 for an exact match, negative for a fuzzy correction.",
    )
    entities: List[LinkedEntity] = Field(
        default_factory=list, description="Entities this span resolves to."
    )


class RegexEntity(BaseModel):
    index: List[int] = Field(
        ..., description="[start, end] character offsets in message_text."
    )
    surface_text: str = Field(..., description="Text matched by the regex rule.")
    rule: str = Field(..., description="entity_id the matching rule belongs to.")
    regex: str = Field(..., description="Regular expression pattern that matched.")
    meronyms: List[str] = Field(default_factory=list)


class NoTagEntity(BaseModel):
    index: List[int] = Field(
        ..., description="[start, end] character offsets in message_text."
    )
    surface_text: str = Field(..., description="Token text that matched nothing.")


class ExtractionResponse(BaseModel):
    universal_entities: List[UniversalEntity] = Field(
        default_factory=list,
        description="Spans matched (exactly or fuzzily) to trained entities.",
    )
    regex_entities: List[RegexEntity] = Field(
        default_factory=list, description="Spans matched by registered regex rules."
    )
    no_tag_entities: List[NoTagEntity] = Field(
        default_factory=list,
        description="Remaining tokens that matched nothing.",
    )


@router.post(
    "",
    response_model=ExtractionResponse,
    summary="Extract and link entities from text",
    description=(
        "Runs the symbolic matching pipeline (tokenization, lemmatization, "
        "phrase/word matching, regex matching) over message_text and "
        "resolves matches to trained entities."
    ),
)
def create_extraction(
    payload: ExtractionRequest,
    bundle: NamespaceBundle = Depends(get_namespace_bundle),
) -> ExtractionResponse:
    return get_surface_texts(
        bundle,
        message_text=payload.message_text,
        word_correction=payload.word_correction,
    )
