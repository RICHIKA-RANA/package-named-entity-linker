from collections.abc import Iterable

from .symspell import SymSpell
from ...model.lex_sqlite_store import SQLiteStore
from .tokenizer import Tokenizer


class LexiGraph:
    """
    SQLite-backed lexical graph.

    Example
    -------
    lexi = LexiGraph("lexigraph.db")

    lexi.load(entities)

    suggestions = lexi.get_suggestions("artifical")
    """

    def __init__(
        self,
        sqlite_path=":memory:",
        *,
        max_edit_distance=2,
    ):
        self.store = SQLiteStore(sqlite_path)

        self.symspell = SymSpell(
            self.store,
            max_edit_distance=max_edit_distance,
        )

    @property
    def max_edit_distance(self):
        return self.symspell.max_edit_distance

    @property
    def longest_word_length(self):
        return self.symspell.longest_word_length

    def create_dictionary_entry(self, word):
        return self.symspell.create_dictionary_entry(word)

    def get_suggestions(
        self,
        word,
        *,
        max_edit_distance=None,
        least_word_suggestions=1,
    ):
        return self.symspell.get_suggestions(
            word,
            max_edit_distance=max_edit_distance,
            least_word_suggestions=least_word_suggestions,
        )

    def load(self, entities):
        """
        Load entities into the dictionary.

        Supported formats

        {
            "surface_text": [
                "United States",
                "USA"
            ]
        }

        or

        {
            "surface_text": [
                {
                    "surface_text": "United States"
                },
                {
                    "surface_text": "USA"
                }
            ]
        }
        """

        count = 0

        for entity in entities:

            surface_texts = entity.get("surface_text", [])

            for surface in surface_texts:

                if isinstance(surface, dict):
                    surface = surface.get("surface_text", "")

                if not surface:
                    continue

                surface = surface.lower()

                for token, *_ in Tokenizer.tokenize(surface):
                    self.create_dictionary_entry(token)
                    count += 1

        return count

    def load_words(self, words: Iterable[str]):
        """
        Load an iterable of words directly.
        """

        count = 0

        for word in words:
            self.create_dictionary_entry(word.lower())
            count += 1

        return count

    def contains(self, word):
        return self.store.has_word(word.lower())

    def frequency(self, word):
        return self.store.get_frequency(word.lower())

    def close(self):
        self.store.close()

    def __contains__(self, word):
        return self.contains(word)

    def __len__(self):
        return self.store.word_count()