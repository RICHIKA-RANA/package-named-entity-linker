import json
import sqlite3
import uuid
from pathlib import Path

import networkx as nx


class SQLiteGraphStore:
    def __init__(self, db_path=":memory:"):
        self.db_path = str(Path(db_path))
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    # ------------------------------------------------------------------

    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entities(
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                surface_texts TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS facts(
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                predicate TEXT NOT NULL,
                attributes TEXT NOT NULL,

                FOREIGN KEY(source) REFERENCES entities(id),
                FOREIGN KEY(target) REFERENCES entities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_fact_source
                ON facts(source);

            CREATE INDEX IF NOT EXISTS idx_fact_target
                ON facts(target);

            CREATE INDEX IF NOT EXISTS idx_fact_predicate
                ON facts(predicate);
            """
        )

        self.conn.commit()

    # ------------------------------------------------------------------
    # metadata
    # ------------------------------------------------------------------

    def set_metadata(self, key, value):
        self.conn.execute(
            """
            INSERT INTO metadata(key,value)
            VALUES(?,?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (key, json.dumps(value)),
        )

        self.conn.commit()

    def get_metadata(self, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM metadata WHERE key=?",
            (key,),
        ).fetchone()

        if row is None:
            return default

        return json.loads(row["value"])

    # ------------------------------------------------------------------
    # entities
    # ------------------------------------------------------------------

    def add_entity(self, entity_id, label, surface_texts=None):
        if surface_texts is None:
            surface_texts = []

        self.conn.execute(
            """
            INSERT INTO entities(id,label,surface_texts)
            VALUES(?,?,?)
            """,
            (
                entity_id,
                label,
                json.dumps(surface_texts),
            ),
        )

        self.conn.commit()

    def has_entity(self, entity_id):
        row = self.conn.execute(
            "SELECT 1 FROM entities WHERE id=?",
            (entity_id,),
        ).fetchone()

        return row is not None

    def get_entity(self, entity_id):
        row = self.conn.execute(
            """
            SELECT *
            FROM entities
            WHERE id=?
            """,
            (entity_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "label": row["label"],
            "surface_texts": json.loads(row["surface_texts"]),
        }

    def update_surface_texts(self, entity_id, surface_texts):
        self.conn.execute(
            """
            UPDATE entities
            SET surface_texts=?
            WHERE id=?
            """,
            (
                json.dumps(surface_texts),
                entity_id,
            ),
        )

        self.conn.commit()

    def iter_entities(self):
        rows = self.conn.execute(
            "SELECT * FROM entities"
        )

        for row in rows:
            yield {
                "id": row["id"],
                "label": row["label"],
                "surface_texts": json.loads(row["surface_texts"]),
            }

    # ------------------------------------------------------------------
    # facts (edges)
    # ------------------------------------------------------------------

    def add_fact(
        self,
        source,
        target,
        predicate,
        fact_id=None,
        **attributes,
    ):
        if fact_id is None:
            fact_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO facts(
                id,
                source,
                target,
                predicate,
                attributes
            )
            VALUES(?,?,?,?,?)
            """,
            (
                fact_id,
                source,
                target,
                predicate,
                json.dumps(attributes),
            ),
        )

        self.conn.commit()

        return fact_id

    def get_fact(self, fact_id):
        row = self.conn.execute(
            """
            SELECT *
            FROM facts
            WHERE id=?
            """,
            (fact_id,),
        ).fetchone()

        if row is None:
            return None

        data = json.loads(row["attributes"])

        data.update(
            {
                "id": row["id"],
                "source": row["source"],
                "target": row["target"],
                "predicate": row["predicate"],
            }
        )

        return data

    def iter_facts(self):
        rows = self.conn.execute(
            "SELECT * FROM facts"
        )

        for row in rows:
            attrs = json.loads(row["attributes"])

            attrs.update(
                {
                    "id": row["id"],
                    "source": row["source"],
                    "target": row["target"],
                    "predicate": row["predicate"],
                }
            )

            yield attrs

    # ------------------------------------------------------------------
    # NetworkX
    # ------------------------------------------------------------------

    def to_networkx(self):
        graph = nx.MultiDiGraph()

        for entity in self.iter_entities():
            graph.add_node(
                entity["id"],
                label=entity["label"],
                surface_texts=entity["surface_texts"],
            )

        for fact in self.iter_facts():
            graph.add_edge(
                fact["source"],
                fact["target"],
                key=fact["id"],
                predicate=fact["predicate"],
                **{
                    k: v
                    for k, v in fact.items()
                    if k
                    not in {
                        "id",
                        "source",
                        "target",
                        "predicate",
                    }
                },
            )

        return graph

    @classmethod
    def from_networkx(cls, graph, db_path=":memory:"):
        store = cls(db_path)

        for node, attrs in graph.nodes(data=True):
            store.add_entity(
                entity_id=node,
                label=attrs.get("label", ""),
                surface_texts=attrs.get("surface_texts", []),
            )

        for u, v, key, attrs in graph.edges(
            keys=True,
            data=True,
        ):
            attrs = dict(attrs)

            predicate = attrs.pop("predicate", "")

            store.add_fact(
                source=u,
                target=v,
                predicate=predicate,
                fact_id=key,
                **attrs,
            )

        return store

    # ------------------------------------------------------------------

    def close(self):
        self.conn.close()