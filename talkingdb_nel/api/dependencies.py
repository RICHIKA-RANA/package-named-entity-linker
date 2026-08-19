from fastapi import HTTPException, status

from talkingdb_nel.services.entity.base import entity_conn
from talkingdb_nel.services.namespace.registry import NamespaceBundle
from talkingdb_nel.services.namespace.registry import registry as namespace_registry
from talkingdb_nel.services.namespace.store import namespace_exists


def get_namespace_bundle(namespace: str) -> NamespaceBundle:
    if not namespace_exists(entity_conn, namespace):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Namespace '{namespace}' not found",
        )

    return namespace_registry.get(namespace)
