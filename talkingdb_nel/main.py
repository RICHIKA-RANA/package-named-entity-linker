from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talkingdb_nel import __version__
from talkingdb_nel.api import entities, extraction, facts, namespaces

DESCRIPTION_FILE = Path(__file__).parent / "DESCRIPTION.md"

description = DESCRIPTION_FILE.read_text(encoding="utf-8")

OPENAPI_TAGS = [
    {
        "name": "Namespaces",
        "description": "Isolated training environments, and their commit history.",
    },
    {
        "name": "Entities",
        "description": "Canonical entities, their surface texts, and regex rules.",
    },
    {
        "name": "Facts",
        "description": "Relationships (facts) between entities.",
    },
    {
        "name": "Extraction",
        "description": "Extracting and linking entities from free text.",
    },
]


app = FastAPI(
    title="TalkingDB Named Entity Linker",
    description=description,
    version=__version__,
    openapi_tags=OPENAPI_TAGS,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(namespaces.router)
app.include_router(entities.router)
app.include_router(facts.router)
app.include_router(extraction.router)
