import threading

from fastapi import FastAPI
from contextlib import asynccontextmanager
from talkingdb_nel.services.workers import start_workers
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=start_workers, daemon=True).start()
    yield
    # Shutdown code can go here


app = FastAPI(lifespan=lifespan, title="Named Entity Linker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
