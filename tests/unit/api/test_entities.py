import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from talkingdb_nel.api import entities
from talkingdb_nel.api.dependencies import get_namespace_bundle
from talkingdb_nel.services.entity.entity import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    RegexRuleNotFoundError,
    SurfaceTextAlreadyExistsError,
)

NS = "test-ns"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(entities.router)
    app.dependency_overrides[get_namespace_bundle] = lambda: object()
    return TestClient(app)


def test_create_entity_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "create_entity",
        lambda bundle, **kwargs: {
            "entity_id": kwargs["entity_id"],
            "label": kwargs["label"] or kwargs["entity_id"],
            "surface_texts": kwargs["surface_texts"],
        },
    )

    response = client.post(
        f"/api/namespaces/{NS}/entities",
        json={"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]},
    )

    assert response.status_code == 201
    assert response.json() == {
        "entity_id": "Q1",
        "label": "Apple",
        "surface_texts": ["Apple"],
    }


def test_create_entity_conflict(client, monkeypatch):
    def raise_conflict(bundle, **kwargs):
        raise EntityAlreadyExistsError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "create_entity", raise_conflict)

    response = client.post(f"/api/namespaces/{NS}/entities", json={"entity_id": "Q1"})

    assert response.status_code == 409


def test_list_entities(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "list_entities",
        lambda bundle: [
            {"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]}
        ],
    )

    response = client.get(f"/api/namespaces/{NS}/entities")

    assert response.status_code == 200
    assert response.json() == [
        {"entity_id": "Q1", "label": "Apple", "surface_texts": ["Apple"]}
    ]


def test_get_entity_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "get_entity",
        lambda bundle, entity_id: {
            "entity_id": entity_id,
            "label": "Apple",
            "surface_texts": ["Apple"],
        },
    )

    response = client.get(f"/api/namespaces/{NS}/entities/Q1")

    assert response.status_code == 200
    assert response.json()["entity_id"] == "Q1"


def test_get_entity_not_found(client, monkeypatch):
    monkeypatch.setattr(entities, "get_entity", lambda bundle, entity_id: None)

    response = client.get(f"/api/namespaces/{NS}/entities/Q1")

    assert response.status_code == 404


def test_update_entity_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "update_entity",
        lambda bundle, **kwargs: {
            "entity_id": kwargs["entity_id"],
            "label": kwargs["label"],
            "surface_texts": ["Apple"],
        },
    )

    response = client.patch(
        f"/api/namespaces/{NS}/entities/Q1",
        json={"label": "New Label"},
    )

    assert response.status_code == 200
    assert response.json()["label"] == "New Label"


def test_update_entity_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "update_entity", raise_not_found)

    response = client.patch(
        f"/api/namespaces/{NS}/entities/Q1",
        json={"label": "New Label"},
    )

    assert response.status_code == 404


def test_delete_entity_success(client, monkeypatch):
    called = []

    monkeypatch.setattr(
        entities,
        "delete_entity",
        lambda bundle, **kwargs: called.append(kwargs["entity_id"]),
    )

    response = client.delete(f"/api/namespaces/{NS}/entities/Q1")

    assert response.status_code == 204
    assert called == ["Q1"]


def test_delete_entity_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "delete_entity", raise_not_found)

    response = client.delete(f"/api/namespaces/{NS}/entities/Q1")

    assert response.status_code == 404


def test_add_surface_text_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "add_surface_text",
        lambda bundle, **kwargs: {
            "entity_id": kwargs["entity_id"],
            "label": "Apple",
            "surface_texts": ["Apple", kwargs["surface_text"]],
        },
    )

    response = client.post(
        f"/api/namespaces/{NS}/entities/Q1/surface-texts",
        json={"surface_text": "Apple Inc"},
    )

    assert response.status_code == 201
    assert response.json()["surface_texts"] == ["Apple", "Apple Inc"]


def test_add_surface_text_entity_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "add_surface_text", raise_not_found)

    response = client.post(
        f"/api/namespaces/{NS}/entities/Q1/surface-texts",
        json={"surface_text": "Apple Inc"},
    )

    assert response.status_code == 404


def test_add_surface_text_duplicate(client, monkeypatch):
    def raise_conflict(bundle, **kwargs):
        raise SurfaceTextAlreadyExistsError(kwargs["surface_text"])

    monkeypatch.setattr(entities, "add_surface_text", raise_conflict)

    response = client.post(
        f"/api/namespaces/{NS}/entities/Q1/surface-texts",
        json={"surface_text": "Apple"},
    )

    assert response.status_code == 409


def test_add_regex_rule_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "create_regex",
        lambda bundle, **kwargs: {
            "entity_id": kwargs["entity_id"],
            "regex": kwargs["regex"],
        },
    )

    response = client.post(
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 201
    assert response.json() == {"entity_id": "Date", "regex": r"\d{4}"}


def test_add_regex_rule_entity_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "create_regex", raise_not_found)

    response = client.post(
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 404


def test_list_regex_rules_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "list_regex_rules",
        lambda bundle, **kwargs: [r"\d{4}", r"\d{2}/\d{2}"],
    )

    response = client.get(f"/api/namespaces/{NS}/entities/Date/regex-rules")

    assert response.status_code == 200
    assert response.json() == [r"\d{4}", r"\d{2}/\d{2}"]


def test_list_regex_rules_entity_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise EntityNotFoundError(kwargs["entity_id"])

    monkeypatch.setattr(entities, "list_regex_rules", raise_not_found)

    response = client.get(f"/api/namespaces/{NS}/entities/Date/regex-rules")

    assert response.status_code == 404


def test_update_regex_rule_success(client, monkeypatch):
    monkeypatch.setattr(
        entities,
        "update_regex_rule",
        lambda bundle, **kwargs: {
            "entity_id": kwargs["entity_id"],
            "regex": kwargs["new_pattern"],
        },
    )

    response = client.patch(
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"old_regex": r"\d{4}", "new_regex": r"\d{2}"},
    )

    assert response.status_code == 200
    assert response.json() == {"entity_id": "Date", "regex": r"\d{2}"}


def test_update_regex_rule_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise RegexRuleNotFoundError(kwargs["old_pattern"])

    monkeypatch.setattr(entities, "update_regex_rule", raise_not_found)

    response = client.patch(
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"old_regex": r"\d{4}", "new_regex": r"\d{2}"},
    )

    assert response.status_code == 404


def test_delete_regex_rule_success(client, monkeypatch):
    called = []

    monkeypatch.setattr(
        entities,
        "delete_regex_rule",
        lambda bundle, **kwargs: called.append(
            (kwargs["entity_id"], kwargs["pattern"])
        ),
    )

    response = client.request(
        "DELETE",
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 204
    assert called == [("Date", r"\d{4}")]


def test_delete_regex_rule_not_found(client, monkeypatch):
    def raise_not_found(bundle, **kwargs):
        raise RegexRuleNotFoundError(kwargs["pattern"])

    monkeypatch.setattr(entities, "delete_regex_rule", raise_not_found)

    response = client.request(
        "DELETE",
        f"/api/namespaces/{NS}/entities/Date/regex-rules",
        json={"regex": r"\d{4}"},
    )

    assert response.status_code == 404
