import sqlite3

from talkingdb.clients.sqlite import (
    sqlite_conn,
    DICTIONARY_DB,
    ENTITY_DB,
    REGEX_DB,
)
from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb.models.entity.entity import EntityModel
from talkingdb.models.rule.regex import RegexModel
from talkingdb_nel.services.symbolic.extractor import SurfaceTextExtractor
from talkingdb_nel.services.symbolic.lemmatizer import Lemmatizer
from talkingdb_nel.services.symbolic.matcher.phrase import PhraseMatcher
from talkingdb_nel.services.symbolic.matcher.word import WordMatcher
from talkingdb_nel.services.symbolic.regex import RegexController

dictionary_conn = sqlite_conn(DICTIONARY_DB).__enter__()
entity_conn = sqlite_conn(ENTITY_DB).__enter__()
regex_conn = sqlite_conn(REGEX_DB).__enter__()

dictionary_conn.row_factory = sqlite3.Row

DictionaryModel.init_db(dictionary_conn)
EntityModel.init_db(entity_conn)
RegexModel.init_db(regex_conn)

dictionary = DictionaryModel.create(
    conn=dictionary_conn,
    dictionary_id=DictionaryModel.make_id("default"),
)

entity_model = EntityModel.load(
    conn=entity_conn,
    entity_id=EntityModel.make_id("default"),
)

regex_model = RegexModel.load(
    conn=regex_conn,
    regex_id=RegexModel.make_id("default"),
)

word_matcher = WordMatcher(dictionary)
sentence_matcher = PhraseMatcher(dictionary)

lemmatizer = Lemmatizer(dictionary)
regex_controller = RegexController(regex_model)

surface_text_extractor = SurfaceTextExtractor(
    word_matcher,
    sentence_matcher,
)