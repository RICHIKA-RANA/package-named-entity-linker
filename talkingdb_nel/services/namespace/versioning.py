from talkingdb_nel.services.entity.entity import index_entity
from talkingdb_nel.services.namespace import store
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.namespace.registry import registry as namespace_registry


def _snapshot(bundle: NamespaceBundle) -> dict:
    return {
        "entities": bundle.entity_model.g_json(),
        "regex_rules": bundle.regex_model.to_dict(),
    }


def commit_namespace(bundle: NamespaceBundle, message: str) -> dict:
    return store.create_commit(
        bundle.entity_conn, bundle.namespace, message, _snapshot(bundle)
    )


def _restore_entities(bundle: NamespaceBundle, entities_snapshot: dict) -> None:
    bundle.entity_model.graph.clear()

    for node in entities_snapshot.get("nodes", []):
        node = dict(node)
        node_id = node.pop("id")

        bundle.entity_model.add_entity(
            entity_id=node_id,
            label=node.get("label", ""),
            surface_texts=node.get("surface_texts", []),
        )

    for edge in entities_snapshot.get("edges", []):
        edge = dict(edge)
        source = edge.pop("source")
        target = edge.pop("target")
        fact_id = edge.pop("key", None)
        predicate = edge.pop("predicate", "")

        bundle.entity_model.add_fact(
            source=source,
            target=target,
            predicate=predicate,
            fact_id=fact_id,
            **edge,
        )

    bundle.entity_model.save(bundle.entity_conn)


def _restore_regex(bundle: NamespaceBundle, regex_snapshot: dict) -> None:
    bundle.regex_model.clear()

    for rule_name, patterns in regex_snapshot.items():
        for pattern in patterns:
            bundle.regex_model.add_rule(rule_name, pattern)

    bundle.regex_model.save(bundle.regex_conn)


def _rebuild_dictionary(bundle: NamespaceBundle) -> None:
    bundle.dictionary.clear()

    # clear() wipes the persisted longest-word metadata, but the matcher
    # objects still cache their pre-clear value in memory (_update_longest
    # only ever grows it) - reset both so the replay below recomputes and
    # persists it correctly instead of silently skipping the write.
    bundle.word_matcher.longest_word_length = 0
    bundle.phrase_matcher.longest_word_length = 0

    for entity in bundle.entity_model.iter_entities():
        index_entity(
            bundle,
            {
                "entity_id": entity["id"],
                "surface_texts": entity["surface_texts"],
            },
        )


def rollback_namespace(bundle: NamespaceBundle, commit_id: str) -> dict:
    commit = store.get_commit(bundle.entity_conn, bundle.namespace, commit_id)

    if commit is None:
        raise store.CommitNotFoundError(commit_id)

    snapshot = commit["snapshot"]

    _restore_entities(bundle, snapshot["entities"])
    _restore_regex(bundle, snapshot["regex_rules"])
    _rebuild_dictionary(bundle)

    result = commit_namespace(bundle, f"Rollback to {commit_id}")

    # Word/phrase matchers cache longest-word metadata that only grows;
    # evict so the next access rebuilds fresh matchers against the
    # rebuilt dictionary instead of carrying stale cached metadata.
    namespace_registry.evict(bundle.namespace)

    return result
