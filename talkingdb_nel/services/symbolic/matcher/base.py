from collections import deque

from talkingdb.models.dictionary.dictionary import DictionaryModel

from ..distance import damerau_levenshtein


class BaseMatcher:
    """
    Base matcher operating on arbitrary strings.
    """

    def __init__(
        self,
        dictionary: DictionaryModel,
        *,
        max_edit_distance: int = 2,
        metadata_key: str = "longest_word_length",
    ):
        self.dictionary = dictionary
        self.max_edit_distance = max_edit_distance
        self._metadata_key = metadata_key

        self.longest_word_length = self.dictionary.get_metadata(
            metadata_key,
            0,
        )

    def _update_longest(self, text: str):
        if len(text) > self.longest_word_length:
            self.longest_word_length = len(text)

            self.dictionary.set_metadata(
                self._metadata_key,
                self.longest_word_length,
            )

    def get_deletes_list(self, text: str):
        deletes = set()

        queue = deque([text])

        for _ in range(self.max_edit_distance):
            next_queue = deque()

            while queue:
                candidate = queue.popleft()

                if len(candidate) <= 1:
                    continue

                for i in range(len(candidate)):
                    delete = candidate[:i] + candidate[i + 1 :]

                    if delete in deletes:
                        continue

                    deletes.add(delete)
                    next_queue.append(delete)

            queue = next_queue

        return deletes

    def create_dictionary_entry(self, text: str):
        text = text.lower().strip()

        if not text:
            return False

        if self.dictionary.has_word(text):
            self.dictionary.increment_frequency(text)
            self._update_longest(text)
            return False

        self.dictionary.insert_word(text)

        self._update_longest(text)

        for delete in self.get_deletes_list(text):
            self.dictionary.add_suggestion(delete, text)

        return True

    def get_suggestions(
        self,
        text: str,
        *,
        max_edit_distance=None,
        least_word_suggestions: int = 1,
    ):
        if max_edit_distance is None:
            max_edit_distance = self.max_edit_distance

        text = text.lower().strip()

        if text.isdigit():
            return [(text, (0, 0))]

        if len(text) - self.longest_word_length > max_edit_distance:
            return []

        suggestions = {}
        queue = deque([text])
        visited = {text}

        min_distance = float("inf")

        while queue:
            candidate = queue.popleft()

            if (
                len(suggestions) >= least_word_suggestions
                and len(text) - len(candidate) > min_distance
            ):
                break

            if self.dictionary.has_word(candidate):
                frequency = self.dictionary.get_frequency(candidate)

                if frequency > 0:
                    suggestions[candidate] = (
                        frequency,
                        len(text) - len(candidate),
                    )

                    min_distance = min(
                        min_distance,
                        len(text) - len(candidate),
                    )

                for real_text in self.dictionary.get_suggestions(candidate):
                    if real_text in suggestions:
                        continue

                    distance = damerau_levenshtein(
                        real_text,
                        text,
                    )

                    if distance <= max_edit_distance:
                        suggestions[real_text] = (
                            self.dictionary.get_frequency(real_text),
                            distance,
                        )

                        min_distance = min(
                            min_distance,
                            distance,
                        )

            if len(text) - len(candidate) < max_edit_distance:
                for i in range(len(candidate)):
                    delete = candidate[:i] + candidate[i + 1 :]

                    if delete in visited:
                        continue

                    visited.add(delete)
                    queue.append(delete)

        return sorted(
            suggestions.items(),
            key=lambda item: (
                item[1][1],
                -item[1][0],
            ),
        )

    def contains(self, text: str):
        return self.dictionary.has_word(text.lower().strip())

    def frequency(self, text: str):
        return self.dictionary.get_frequency(text.lower().strip())

    def close(self):
        self.dictionary.close()

    def __contains__(self, text):
        return self.contains(text)

    def __len__(self):
        return self.dictionary.word_count()
