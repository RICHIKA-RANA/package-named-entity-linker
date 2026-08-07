import sqlite3

from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb.models.entity.entity import EntityModel
from talkingdb.models.rule.regex import RegexModel

from talkingdb_nel.services.entity import base
from talkingdb_nel.services.symbolic.extractor import SurfaceTextExtractor
from talkingdb_nel.services.symbolic.lemmatizer import Lemmatizer
from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher
from talkingdb_nel.services.symbolic.matcher.word import WordMatcher
from talkingdb_nel.services.symbolic.regex import RegexController


def test_connections_created():
    assert base.dictionary_conn is not None
    assert base.entity_conn is not None
    assert base.regex_conn is not None


def test_dictionary_row_factory():
    assert base.dictionary_conn.row_factory is sqlite3.Row


def test_models_created():
    assert isinstance(base.dictionary, DictionaryModel)
    assert isinstance(base.entity_model, EntityModel)
    assert isinstance(base.regex_model, RegexModel)


def test_services_created():
    assert isinstance(base.word_matcher, WordMatcher)
    assert isinstance(base.phrase_matcher, PhraseMatcher)
    assert isinstance(base.lemmatizer, Lemmatizer)
    assert isinstance(base.regex_controller, RegexController)
    assert isinstance(base.surface_text_extractor, SurfaceTextExtractor)


def test_services_share_dictionary():
    assert base.word_matcher.dictionary is base.dictionary
    assert base.phrase_matcher.dictionary is base.dictionary
    assert base.lemmatizer.dictionary is base.dictionary


def test_regex_controller_dependency():
    assert base.regex_controller.regex_model is base.regex_model
