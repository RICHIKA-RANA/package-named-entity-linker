import sqlite3

import pytest
from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb.models.entity.entity import EntityModel
from talkingdb.models.rule.regex import RegexModel

from talkingdb_nel.services.entity.entity import create_entity, create_regex
from talkingdb_nel.services.namespace import store, versioning
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.symbolic.extractor import SurfaceTextExtractor
from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher
from talkingdb_nel.services.symbolic.matcher.word import WordMatcher
from talkingdb_nel.services.symbolic.regex import RegexController


class FakeRegistry:
    def __init__(self):
        self.evicted = []

    def evict(self, namespace):
        self.evicted.append(namespace)


def make_bundle(namespace: str) -> NamespaceBundle:
    dict_conn = sqlite3.connect(":memory:")
    dict_conn.row_factory = sqlite3.Row
    DictionaryModel.init_db(dict_conn)
    dictionary = DictionaryModel.create(
        conn=dict_conn, dictionary_id=DictionaryModel.make_id(namespace)
    )

    # Same connection backs entity storage AND namespace/commit
    # bookkeeping, mirroring how base.py wires the real entity_conn.
    entity_conn = sqlite3.connect(":memory:")
    entity_conn.row_factory = sqlite3.Row
    EntityModel.init_db(entity_conn)
    store.init_db(entity_conn)
    entity_model = EntityModel.load(
        conn=entity_conn, entity_id=EntityModel.make_id(namespace)
    )

    regex_conn = sqlite3.connect(":memory:")
    regex_conn.row_factory = sqlite3.Row
    RegexModel.init_db(regex_conn)
    regex_model = RegexModel.load(
        conn=regex_conn, regex_id=RegexModel.make_id(namespace)
    )

    word_matcher = WordMatcher(dictionary)
    phrase_matcher = PhraseMatcher(dictionary)

    return NamespaceBundle(
        namespace=namespace,
        dictionary=dictionary,
        entity_model=entity_model,
        regex_model=regex_model,
        word_matcher=word_matcher,
        phrase_matcher=phrase_matcher,
        lemmatizer=None,
        regex_controller=RegexController(regex_model),
        surface_text_extractor=SurfaceTextExtractor(word_matcher, phrase_matcher),
        entity_conn=entity_conn,
        regex_conn=regex_conn,
    )


@pytest.fixture
def bundle():
    return make_bundle("versioning-test")


@pytest.fixture(autouse=True)
def fake_registry(monkeypatch):
    fake = FakeRegistry()
    monkeypatch.setattr(versioning, "namespace_registry", fake)
    return fake


def test_commit_namespace_snapshots_entities_and_regex(bundle):
    create_entity(bundle, "Q1", label="Mayank", surface_texts=["mayank"])
    create_regex(bundle, "Q1", r"\d{4}")

    commit = versioning.commit_namespace(bundle, "initial commit")

    stored = store.get_commit(
        bundle.entity_conn, "versioning-test", commit["commit_id"]
    )
    assert stored["message"] == "initial commit"

    node_ids = {node["id"] for node in stored["snapshot"]["entities"]["nodes"]}
    assert node_ids == {"Q1"}
    assert stored["snapshot"]["regex_rules"] == {"Q1": [r"\d{4}"]}


def test_rollback_restores_prior_entity_state(bundle, fake_registry):
    create_entity(bundle, "Q1", label="Mayank", surface_texts=["mayank"])
    first_commit = versioning.commit_namespace(bundle, "just mayank")

    create_entity(bundle, "Q2", label="Satyam", surface_texts=["satyam"])
    versioning.commit_namespace(bundle, "added satyam")

    assert bundle.entity_model.has_entity("Q2")
    assert bundle.phrase_matcher.get_suggestions("satyam", max_edit_distance=0)

    rollback_commit = versioning.rollback_namespace(bundle, first_commit["commit_id"])

    assert not bundle.entity_model.has_entity("Q2")
    assert bundle.entity_model.has_entity("Q1")
    assert rollback_commit["message"] == f"Rollback to {first_commit['commit_id'][:8]}"

    # dictionary rebuilt from scratch: satyam should no longer resolve,
    # mayank should still resolve at distance 0 (regression test for the
    # longest_word_length staleness bug found while implementing this).
    assert bundle.phrase_matcher.get_suggestions("satyam", max_edit_distance=0) == []
    assert bundle.phrase_matcher.get_suggestions("mayank", max_edit_distance=0)

    assert fake_registry.evicted == ["versioning-test"]


def test_rollback_is_non_destructive_to_history(bundle):
    create_entity(bundle, "Q1", label="Mayank", surface_texts=["mayank"])
    first_commit = versioning.commit_namespace(bundle, "initial")

    create_entity(bundle, "Q2", label="Satyam", surface_texts=["satyam"])
    second_commit = versioning.commit_namespace(bundle, "added satyam")

    versioning.rollback_namespace(bundle, first_commit["commit_id"])

    history = store.list_commits(bundle.entity_conn, "versioning-test")

    assert len(history) == 3
    assert {c["commit_id"] for c in history} >= {
        first_commit["commit_id"],
        second_commit["commit_id"],
    }


def test_rollback_missing_commit_raises(bundle):
    with pytest.raises(store.CommitNotFoundError):
        versioning.rollback_namespace(bundle, "nonexistent")


def test_purge_namespace_data_wipes_everything(bundle, fake_registry):
    store.create_namespace(bundle.entity_conn, "versioning-test")
    create_entity(bundle, "Q1", label="Mayank", surface_texts=["mayank"])
    create_regex(bundle, "Q1", r"\d{4}")
    versioning.commit_namespace(bundle, "initial")

    versioning.purge_namespace_data(bundle)

    assert store.namespace_exists(bundle.entity_conn, "versioning-test") is False
    assert store.list_commits(bundle.entity_conn, "versioning-test") == []
    assert not bundle.entity_model.has_entity("Q1")
    assert bundle.regex_model.rules == {}
    assert fake_registry.evicted == ["versioning-test"]
