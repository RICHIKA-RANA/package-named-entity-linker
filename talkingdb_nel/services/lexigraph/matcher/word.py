from collections.abc import Iterable

from talkingdb.models.dictionary.dictionary import DictionaryModel

from talkingdb_nel.services.lexigraph.tokenizer import Tokenizer

from .base import BaseMatcher


class WordMatcher(BaseMatcher):
    """
    Matcher operating on individual words.

    Surface text is tokenized before being added to the
    dictionary.
    """

    def __init__(
        self,
        dictionary: DictionaryModel,
        *,
        max_edit_distance: int = 2,
    ):
        super().__init__(
            dictionary,
            max_edit_distance=max_edit_distance,
            metadata_key="longest_word_length",
        )

    def load(self, entities):
        """
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

            surface_texts = entity.get(
                "surface_text",
                [],
            )

            for surface in surface_texts:

                if isinstance(surface, dict):
                    surface = surface.get(
                        "surface_text",
                        "",
                    )

                if not surface:
                    continue

                for token, *_ in Tokenizer.tokenize(
                    surface.lower()
                ):
                    self.create_dictionary_entry(token)
                    count += 1

        return count

    def load_words(
        self,
        words: Iterable[str],
    ):
        count = 0

        for word in words:
            self.create_dictionary_entry(word)
            count += 1

        return count