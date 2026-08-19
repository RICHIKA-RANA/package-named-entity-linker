from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from talkingdb_nel.main import app, mount_playground

client = TestClient(app)


def test_app_title():
    assert app.title == "TalkingDB Named Entity Linker"


def test_cors_middleware_registered():
    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)


def _build_fake_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>playground shell</html>")
    (dist / "assets" / "app.js").write_text("console.log('hi')")
    (dist / "favicon.svg").write_text("<svg></svg>")
    return dist


def test_mount_playground_serves_assets_and_root_files(tmp_path):
    dist = _build_fake_dist(tmp_path)
    test_app = FastAPI()
    mount_playground(test_app, dist)
    test_client = TestClient(test_app)

    root = test_client.get("/")
    assert root.status_code == 200
    assert "playground shell" in root.text

    asset = test_client.get("/assets/app.js")
    assert asset.status_code == 200

    favicon = test_client.get("/favicon.svg")
    assert favicon.status_code == 200


def test_mount_playground_spa_fallback_for_client_routes(tmp_path):
    dist = _build_fake_dist(tmp_path)
    test_app = FastAPI()
    mount_playground(test_app, dist)
    test_client = TestClient(test_app)

    response = test_client.get("/namespaces/some-namespace")

    assert response.status_code == 200
    assert "playground shell" in response.text


def test_mount_playground_is_noop_when_dist_missing(tmp_path):
    test_app = FastAPI()
    mount_playground(test_app, tmp_path / "does-not-exist")
    test_client = TestClient(test_app)

    response = test_client.get("/")

    assert response.status_code == 404
