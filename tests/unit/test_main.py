from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from talkingdb_nel.main import app

client = TestClient(app)


def test_app_title():
    assert app.title == "TalkingDB Named Entity Linker"


def test_cors_middleware_registered():
    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)
