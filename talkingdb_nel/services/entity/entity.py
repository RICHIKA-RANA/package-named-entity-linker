from talkingdb_nel.services.entity.base import (
    entity_model,
    lemmatizer,
    phrase_matcher,
    regex_conn,
    regex_controller,
    regex_model,
    surface_text_extractor,
    word_matcher,
)
from talkingdb_nel.services.symbolic.notag import NoTag


class EntityNotFoundError(Exception):
    """Raised when a referenced entity_id does not exist."""


class EntityAlreadyExistsError(Exception):
    """Raised when creating an entity_id that already exists."""


class SurfaceTextAlreadyExistsError(Exception):
    """Raised when adding a surface text an entity already has."""


def index_entity(entity: dict):
    word_matcher.load([entity])
    phrase_matcher.load([entity])


def create_entity(
    entity_id: str,
    label: str | None = None,
    surface_texts: list[str] | None = None,
) -> dict:
    if entity_model.has_entity(entity_id):
        raise EntityAlreadyExistsError(entity_id)

    surface_texts = list(surface_texts or [])
    resolved_label = label or entity_id

    entity_model.add_entity(
        entity_id=entity_id,
        label=resolved_label,
        surface_texts=surface_texts,
    )

    index_entity({"entity_id": entity_id, "surface_texts": surface_texts})

    return {
        "entity_id": entity_id,
        "label": resolved_label,
        "surface_texts": surface_texts,
    }


def get_entity(entity_id: str) -> dict | None:
    entity = entity_model.get_entity(entity_id)

    if entity is None:
        return None

    return {
        "entity_id": entity["id"],
        "label": entity["label"],
        "surface_texts": entity["surface_texts"],
    }


def list_entities() -> list[dict]:
    return [
        {
            "entity_id": entity["id"],
            "label": entity["label"],
            "surface_texts": entity["surface_texts"],
        }
        for entity in entity_model.iter_entities()
    ]


def add_surface_text(entity_id: str, surface_text: str) -> dict:
    entity = entity_model.get_entity(entity_id)

    if entity is None:
        raise EntityNotFoundError(entity_id)

    texts = entity["surface_texts"]

    if surface_text in texts:
        raise SurfaceTextAlreadyExistsError(surface_text)

    texts.append(surface_text)

    entity_model.update_surface_texts(
        entity_id,
        texts,
    )

    index_entity(
        {
            "entity_id": entity_id,
            "surface_texts": [surface_text],
        }
    )

    return {
        "entity_id": entity_id,
        "label": entity["label"],
        "surface_texts": texts,
    }


def create_fact(
    source: str,
    predicate: str,
    target: str,
    **attributes,
) -> dict:
    fact_id = entity_model.add_fact(
        source=source,
        target=target,
        predicate=predicate,
        **attributes,
    )

    return {
        "id": fact_id,
        "source": source,
        "target": target,
        "predicate": predicate,
        **attributes,
    }


def get_fact(fact_id: str) -> dict | None:
    return entity_model.get_fact(fact_id)


def list_facts() -> list[dict]:
    return list(entity_model.iter_facts())


def _suggestion_parts(suggestion):
    if isinstance(suggestion, tuple):
        text, (_, distance) = suggestion
        return text, distance

    return suggestion.term, suggestion.distance


def _resolve_entities(suggestions):
    """
    Resolve raw matcher suggestions (surface text + edit distance) to the
    entity `entity_id`(s) they were trained under.
    """

    resolved = []
    seen_ids = set()

    for suggestion in suggestions:
        text, _ = _suggestion_parts(suggestion)

        for entity in entity_model.get_entities_by_surface_text(text):
            if entity["id"] in seen_ids:
                continue

            seen_ids.add(entity["id"])

            resolved.append(
                {
                    "entity_id": entity["id"],
                    "label": entity["label"],
                    "surface_text": text,
                }
            )

    return resolved


MAX_FUZZY_WINDOW_WORDS = 4


def _iter_no_tag_windows(message_text: str, no_tags: list[dict]):
    """
    Yield (start, end, text) windows over contiguous runs of no-tag tokens,
    joining up to MAX_FUZZY_WINDOW_WORDS whitespace-adjacent tokens so
    multi-word surface texts can be fuzzy-matched as a single phrase.
    """

    for i in range(len(no_tags)):
        start = no_tags[i]["index"][0]
        end = no_tags[i]["index"][1]

        yield start, end, message_text[start : end + 1]

        for j in range(i + 1, min(i + MAX_FUZZY_WINDOW_WORDS, len(no_tags))):
            gap = message_text[no_tags[j - 1]["index"][1] + 1 : no_tags[j]["index"][0]]

            if gap.strip():
                break

            end = no_tags[j]["index"][1]

            yield start, end, message_text[start : end + 1]


def _find_fuzzy_matches(message_text: str, no_tags: list[dict]):
    seen = set()

    for start, end, window_text in _iter_no_tag_windows(message_text, no_tags):
        for suggestion in phrase_matcher.get_suggestions(
            window_text,
            max_edit_distance=1,
        ):
            candidate, distance = _suggestion_parts(suggestion)

            seen_key = (start, end, candidate)

            if seen_key in seen:
                continue

            entities = _resolve_entities([suggestion])

            if not entities:
                continue

            seen.add(seen_key)

            yield {
                "index": [start, end],
                "surface_text": message_text[start : end + 1],
                "corrected_text": candidate,
                "score": -distance,
                "entities": entities,
            }


def create_regex(entity_id: str, regex: str) -> dict:
    if not entity_model.has_entity(entity_id):
        raise EntityNotFoundError(entity_id)

    regex_model.add_rule(
        entity_id,
        regex,
    )
    regex_model.save(regex_conn)

    return {"entity_id": entity_id, "regex": regex}


def get_surface_texts(
    message_text: str,
    word_correction: bool = False,
):
    universal_entities = surface_text_extractor.extract(
        message_text,
        [],
        word_correction=word_correction,
    )

    for entity in universal_entities:
        entity["entities"] = _resolve_entities(entity["entities"])

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
        start, end = chunk["index"]
        text = " ".join(chunk["lemmatized_tokens"])

        additional = phrase_matcher.get_suggestions(
            text,
            max_edit_distance=1 if word_correction else 0,
        )

        for suggestion in additional:
            candidate, distance = _suggestion_parts(suggestion)

            seen_key = (start, end, candidate)

            if seen_key in seen:
                continue

            entities = _resolve_entities([suggestion])

            if not entities:
                continue

            universal_entities.append(
                {
                    "index": [start, end],
                    "surface_text": message_text[start : end + 1],
                    "corrected_text": candidate,
                    "score": -distance,
                    "entities": entities,
                }
            )

            seen.add(seen_key)

    if word_correction:
        for match in _find_fuzzy_matches(message_text, no_tags):
            seen_key = tuple(match["index"]) + (match["corrected_text"],)

            if seen_key in seen:
                continue

            universal_entities.append(match)
            seen.add(seen_key)

    matched_ranges = [tuple(entity["index"]) for entity in universal_entities]

    remaining_no_tags = [
        tag
        for tag in remaining_no_tags
        if not any(
            tag["index"][0] <= end and start <= tag["index"][1]
            for start, end in matched_ranges
        )
    ]

    return {
        "universal_entities": universal_entities,
        "regex_entities": filtered_regex,
        "no_tag_entities": remaining_no_tags,
    }
