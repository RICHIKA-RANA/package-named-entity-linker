from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talkingdb_nel import __version__
from talkingdb_nel.api import nel

DESCRIPTION_FILE = Path(__file__).parent / "DESCRIPTION.md"

description = DESCRIPTION_FILE.read_text(encoding="utf-8")


app = FastAPI(
    title="TalkingDB Named Entity Linker",
    description=description,
    version=__version__,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(nel.router)
