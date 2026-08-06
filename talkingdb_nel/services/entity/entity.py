import sqlite3

from talkingdb.clients.sqlite import sqlite_conn,DICTIONARY_DB, ENTITY_DB, REGEX_DB
from talkingdb_nel.model.dictionary_model import DictionaryModel
from talkingdb_nel.model.entity_model import EntityModel
from talkingdb_nel.model.regex_model import RegexModel
from talkingdb_nel.services.lexigraph.extract_surface_text import (
    SurfaceTextExtractor,
)
from talkingdb_nel.services.lexigraph.lemmatizer import Lemmatizer
from talkingdb_nel.services.lexigraph.lexigraph import LexiGraph
from talkingdb_nel.services.lexigraph.notag import NoTag
from talkingdb_nel.services.rule.regex_controller import RegexController
from talkingdb_nel.services.sentencegraph.sentence_symspell import (
    SentenceSymSpell,
)

dictionary_conn = sqlite_conn(DICTIONARY_DB).__enter__()
entity_conn = sqlite_conn(ENTITY_DB).__enter__()
regex_conn = sqlite_conn(REGEX_DB).__enter__()

dictionary_conn.row_factory = sqlite3.Row

DictionaryModel.init_db(dictionary_conn)
RegexModel.init_db(regex_conn)
EntityModel.init_db(entity_conn)

dictionary = DictionaryModel.create(
    conn=dictionary_conn,
    dictionary_id=DictionaryModel.make_id("default"),
)

regex_model = RegexModel.load(
    conn=regex_conn,
    regex_id=RegexModel.make_id("default"),
)

entity_model = EntityModel.load(
    conn=entity_conn,
    entity_id=EntityModel.make_id("default"),
)

lexigraph = LexiGraph(dictionary)
sentence_symspell = SentenceSymSpell(dictionary)
lemmatizer = Lemmatizer(dictionary)

regex_controller = RegexController(regex_model)

surface_text_extractor = SurfaceTextExtractor(
    lexigraph.symspell,
    sentence_symspell,
)

def index_entity(entity: dict):
    # Word dictionary
    lexigraph.load([entity])

    # Sentence dictionary
    for surface_text in entity.get("surface_texts", []):
        sentence_symspell.create_dictionary_entry(surface_text)


def create_entity(entity: dict):
    entity_model.add_entity(
        entity_id=entity["_id"],
        label=entity.get("label", entity["_id"]),
        surface_texts=entity.get("surface_texts", []),
    )

    index_entity(entity)

    return {"success": True}


def add_surface_text(entity_id: str, surface_text: str):
    entity = entity_model.get_entity(entity_id)

    if entity is None:
        return {"success": False, "message": "Entity not found"}

    texts = entity["surface_texts"]

    if surface_text in texts:
        return {"success": False, "message": "Already exists"}

    texts.append(surface_text)

    entity_model.update_surface_texts(
        entity_id,
        texts,
    )

    sentence_symspell.create_dictionary_entry(surface_text)

    lexigraph.load(
        [
            {
                "_id": entity_id,
                "surface_texts": [surface_text],
            }
        ]
    )

    return {"success": True}


def create_fact(
    source: str,
    predicate: str,
    target: str,
    **attributes,
):
    entity_model.add_fact(
        source=source,
        target=target,
        predicate=predicate,
        **attributes,
    )

    return {"success": True}


def create_regex(entity_id: str, regex: str):
    regex_model.add_rule(
        entity_id,
        regex,
    )
    regex_model.save(regex_conn)
    return {"success": True}


def get_surface_texts(
    message_text: str,
    word_correction: bool = False,
):
    # ------------------------------------------------------------------
    # Universal entities (SentenceSymSpell + LexiGraph)
    # ------------------------------------------------------------------

    universal_entities = surface_text_extractor.extract(
        message_text,
        [],
        word_correction=word_correction,
    )

    universal_entities = [
        entity
        for entity in universal_entities
        if entity["entities"]
    ]

    # ------------------------------------------------------------------
    # Regex entities
    # ------------------------------------------------------------------

    regex_entities = regex_controller.process(message_text)

    date_locations = set()

    for entity in regex_entities:
        if entity["rule"] == "Date_Regex":
            start, end = entity["index"]
            date_locations.update(range(start, end))

    filtered_regex = []

    for entity in regex_entities:
        if entity["rule"] == "Date_Regex":
            filtered_regex.append(entity)
            continue

        start, end = entity["index"]

        if not set(range(start, end)).intersection(date_locations):
            filtered_regex.append(entity)

    # ------------------------------------------------------------------
    # Untagged text
    # ------------------------------------------------------------------

    no_tags = NoTag.get_no_tags(
        message_text,
        universal_entities + regex_entities,
    )

    remaining_no_tags, lemmatized = lemmatizer.lemmatize(no_tags)

    seen = set()

    for chunk in lemmatized:
        start = chunk["index"][0]
        text = " ".join(chunk["lemmatized_tokens"])

        additional = sentence_symspell.get_suggestions(
            text,
            max_edit_distance=1,
        )

        offset = start

        for entity in additional:
            index = (
                offset,
                offset + len(entity[0]),
            )

            if index in seen:
                continue

            universal_entities.append(
                {
                    "index": index,
                    "surface_texts": [entity],
                }
            )

            seen.add(index)

    return {
        "UniversalEntities": universal_entities,
        "RegexEntities": filtered_regex,
        "NoTagEntities": remaining_no_tags,
    }
