from talkingdb_nel.services.entity.base import (
    entity_model,
    lemmatizer,
    regex_conn,
    regex_controller,
    regex_model,
    sentence_matcher,
    surface_text_extractor,
    word_matcher,
)
from talkingdb_nel.services.symbolic.notag import NoTag


def index_entity(entity: dict):
    word_matcher.load([entity])
    sentence_matcher.load([entity])


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

    index_entity(
        {
            "_id": entity_id,
            "surface_text": [surface_text],
            "surface_texts": [surface_text],
        }
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
    universal_entities = surface_text_extractor.extract(
        message_text,
        [],
        word_correction=word_correction,
    )

    universal_entities = [entity for entity in universal_entities if entity["entities"]]

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

    no_tags = NoTag.get_no_tags(
        message_text,
        universal_entities + regex_entities,
    )

    remaining_no_tags, lemmatized = lemmatizer.lemmatize(no_tags)

    seen = set()

    for chunk in lemmatized:
        start = chunk["index"][0]
        text = " ".join(chunk["lemmatized_tokens"])

        additional = sentence_matcher.get_suggestions(
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
