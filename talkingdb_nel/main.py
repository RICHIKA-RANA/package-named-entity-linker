from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from talkingdb_nel import __version__
from talkingdb_nel.api import entities, extraction, facts, namespaces, testsuite

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
    {
        "name": "Test Suite",
        "description": (
            "Regression test cases and accuracy runs for validating training."
        ),
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
app.include_router(testsuite.router)


def mount_playground(app: FastAPI, dist_dir: Path) -> None:
    """
    Serve the built playground SPA, if present. A no-op when dist_dir
    doesn't exist, so running the API alone (no frontend build) still
    works exactly as it does without this - /docs included.
    """

    if not dist_dir.is_dir():
        return

    app.mount(
        "/assets",
        StaticFiles(directory=dist_dir / "assets"),
        name="playground-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_playground(full_path: str) -> FileResponse:
        candidate = dist_dir / full_path

        if full_path and candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(dist_dir / "index.html")


PLAYGROUND_DIST = Path(__file__).resolve().parent.parent / "playground" / "dist"

mount_playground(app, PLAYGROUND_DIST)
