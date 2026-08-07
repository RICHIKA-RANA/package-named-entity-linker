from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talkingdb_nel.api import nel

app = FastAPI(title="Named Entity Linker")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nel.router)
