import sqlite3
from dataclasses import dataclass

from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb.models.entity.entity import EntityModel
from talkingdb.models.rule.regex import RegexModel

from talkingdb_nel.services.entity.base import (
    dictionary_conn,
    entity_conn,
    regex_conn,
)
from talkingdb_nel.services.symbolic.extractor import SurfaceTextExtractor
from talkingdb_nel.services.symbolic.lemmatizer import Lemmatizer
from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher
from talkingdb_nel.services.symbolic.matcher.word import WordMatcher
from talkingdb_nel.services.symbolic.regex import RegexController


@dataclass
class NamespaceBundle:
    namespace: str
    dictionary: DictionaryModel
    entity_model: EntityModel
    regex_model: RegexModel
    word_matcher: WordMatcher
    phrase_matcher: PhraseMatcher
    lemmatizer: Lemmatizer
    regex_controller: RegexController
    surface_text_extractor: SurfaceTextExtractor
    # The connections entity_model/regex_model were loaded from - kept on
    # the bundle (rather than imported as globals in entity.py) so save()
    # calls always target the same store the model was read from, in
    # production and in tests alike.
    entity_conn: sqlite3.Connection
    regex_conn: sqlite3.Connection


def _build_bundle(namespace: str) -> NamespaceBundle:
    dictionary = DictionaryModel.create(
        conn=dictionary_conn,
        dictionary_id=DictionaryModel.make_id(namespace),
    )

    entity_model = EntityModel.load(
        conn=entity_conn,
        entity_id=EntityModel.make_id(namespace),
    )

    regex_model = RegexModel.load(
        conn=regex_conn,
        regex_id=RegexModel.make_id(namespace),
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
        lemmatizer=Lemmatizer(dictionary),
        regex_controller=RegexController(regex_model),
        surface_text_extractor=SurfaceTextExtractor(word_matcher, phrase_matcher),
        entity_conn=entity_conn,
        regex_conn=regex_conn,
    )


class NamespaceRegistry:
    """
    Lazily loads and caches one NamespaceBundle per namespace. The
    underlying sqlite connections are shared singletons (see
    talkingdb_nel.services.entity.base) - only the model/matcher
    instances built on top of them are per-namespace.
    """

    def __init__(self):
        self._bundles: dict[str, NamespaceBundle] = {}

    def get(self, namespace: str) -> NamespaceBundle:
        if namespace not in self._bundles:
            self._bundles[namespace] = _build_bundle(namespace)

        return self._bundles[namespace]

    def evict(self, namespace: str) -> None:
        self._bundles.pop(namespace, None)


registry = NamespaceRegistry()
