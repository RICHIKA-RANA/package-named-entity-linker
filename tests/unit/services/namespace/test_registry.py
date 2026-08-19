import uuid

from talkingdb_nel.services.namespace import registry as registry_module
from talkingdb_nel.services.namespace.registry import NamespaceBundle, NamespaceRegistry


def test_registry_caches_bundle_per_namespace(monkeypatch):
    build_calls = []

    def fake_build(namespace):
        build_calls.append(namespace)
        return object()

    monkeypatch.setattr(registry_module, "_build_bundle", fake_build)

    reg = NamespaceRegistry()

    first = reg.get("ns1")
    second = reg.get("ns1")

    assert first is second
    assert build_calls == ["ns1"]


def test_registry_isolates_different_namespaces(monkeypatch):
    monkeypatch.setattr(registry_module, "_build_bundle", lambda namespace: object())

    reg = NamespaceRegistry()

    assert reg.get("ns1") is not reg.get("ns2")


def test_registry_evict_forces_rebuild(monkeypatch):
    build_calls = []

    monkeypatch.setattr(
        registry_module,
        "_build_bundle",
        lambda namespace: build_calls.append(namespace) or object(),
    )

    reg = NamespaceRegistry()

    first = reg.get("ns1")
    reg.evict("ns1")
    second = reg.get("ns1")

    assert first is not second
    assert build_calls == ["ns1", "ns1"]


def test_evict_unknown_namespace_is_a_noop():
    reg = NamespaceRegistry()

    reg.evict("never-loaded")  # should not raise


def test_build_bundle_wires_up_matchers_against_own_namespace_dictionary():
    namespace = f"test-{uuid.uuid4()}"

    bundle = registry_module._build_bundle(namespace)

    assert isinstance(bundle, NamespaceBundle)
    assert bundle.namespace == namespace
    assert bundle.word_matcher.dictionary is bundle.dictionary
    assert bundle.phrase_matcher.dictionary is bundle.dictionary
    assert bundle.surface_text_extractor.word_matcher is bundle.word_matcher
    assert bundle.surface_text_extractor.phrase_matcher is bundle.phrase_matcher
    assert bundle.regex_controller.regex_model is bundle.regex_model
    assert not bundle.entity_model.has_entity("nonexistent")
