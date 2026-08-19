import sqlite3

from talkingdb.clients.sqlite import (
    DICTIONARY_DB,
    ENTITY_DB,
    REGEX_DB,
    sqlite_conn,
)
from talkingdb.models.dictionary.dictionary import DictionaryModel
from talkingdb.models.entity.entity import EntityModel
from talkingdb.models.rule.regex import RegexModel

from talkingdb_nel.services.namespace.store import init_db as init_namespace_db
from talkingdb_nel.services.testsuite.store import init_db as init_testsuite_db

dictionary_conn = sqlite_conn(DICTIONARY_DB).__enter__()
entity_conn = sqlite_conn(ENTITY_DB).__enter__()
regex_conn = sqlite_conn(REGEX_DB).__enter__()

dictionary_conn.row_factory = sqlite3.Row

DictionaryModel.init_db(dictionary_conn)
EntityModel.init_db(entity_conn)
RegexModel.init_db(regex_conn)
init_namespace_db(entity_conn)
init_testsuite_db(entity_conn)
