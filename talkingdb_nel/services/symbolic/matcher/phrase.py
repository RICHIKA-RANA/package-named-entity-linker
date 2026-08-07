from collections.abc import Iterable

from talkingdb.models.dictionary.dictionary import DictionaryModel

from .base import BaseMatcher


class PhraseMatcher(BaseMatcher):
    """
    Matcher operating on complete surface-text phrases.
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
            metadata_key="sentence_longest_length",
        )

    def load(self, entities):
        """
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

        count = 0

        for entity in entities:
            surface_texts = entity.get(
                "surface_texts",
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

                self.create_dictionary_entry(surface)

                count += 1

        return count

    def load_sentences(
        self,
        sentences: Iterable[str],
    ):
        count = 0

        for sentence in sentences:
            self.create_dictionary_entry(sentence)
            count += 1

        return count
