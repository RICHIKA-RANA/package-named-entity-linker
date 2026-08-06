from collections.abc import Iterable

from talkingdb_nel.model.dictionary_model import DictionaryModel

from .sentence_symspell import SentenceSymSpell


class SentenceGraph:
    """
    SQLite-backed sentence dictionary.

    Stores complete surface-text phrases instead of individual words.

    Supported formats

    {
        "surface_texts": [
            "New York City",
            "NYC"
        ]
    }

    or

    {
        "surface_texts": [
            {
                "surface_text": "New York City"
            }
        ]
    }
    """

    def __init__(
        self,
        dictionary: DictionaryModel,
        *,
        max_edit_distance=2,
    ):
        self.dictionary = dictionary

        self.symspell = SentenceSymSpell(
            self.dictionary,
            max_edit_distance=max_edit_distance,
        )

    @property
    def max_edit_distance(self):
        return self.symspell.max_edit_distance

    @property
    def longest_word_length(self):
        return self.symspell.longest_word_length

    def create_dictionary_entry(self, sentence: str):
        return self.symspell.create_dictionary_entry(sentence)

    def get_suggestions(
        self,
        sentence: str,
        *,
        max_edit_distance=None,
    ):
        return self.symspell.get_suggestions(
            sentence,
            max_edit_distance=max_edit_distance,
        )

    def load(self, entities):
        count = 0

        for entity in entities:
            for surface in entity.get(
                "surface_texts",
                [],
            ):
                if isinstance(surface, dict):
                    surface = surface.get(
                        "surface_text",
                        "",
                    )

                if not surface:
                    continue

                self.create_dictionary_entry(
                    surface.strip().lower()
                )

                count += 1

        return count

    def load_sentences(
        self,
        sentences: Iterable[str],
    ):
        count = 0

        for sentence in sentences:
            self.create_dictionary_entry(
                sentence.strip().lower()
            )

            count += 1

        return count

    def contains(self, sentence):
        return self.dictionary.has_word(
            sentence.strip().lower()
        )

    def frequency(self, sentence):
        return self.dictionary.get_frequency(
            sentence.strip().lower()
        )

    def __contains__(self, sentence):
        return self.contains(sentence)

    def __len__(self):
        return self.dictionary.word_count()