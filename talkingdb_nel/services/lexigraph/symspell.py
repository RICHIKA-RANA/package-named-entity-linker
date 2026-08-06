from collections import deque

from .distance import damerau_levenshtein
from talkingdb.models.dictionary.dictionary import DictionaryModel


class SymSpell:
    def __init__(
        self,
        dictionary: DictionaryModel,
        max_edit_distance: int = 2,
    ):
        self.dictionary = dictionary
        self.max_edit_distance = max_edit_distance
        self.longest_word_length = (
            self.dictionary.get_metadata("longest_word_length", 0)
        )

    def _update_longest_word(self, word):
        if len(word) > self.longest_word_length:
            self.longest_word_length = len(word)
            self.dictionary.set_metadata(
                "longest_word_length",
                self.longest_word_length,
            )

    def get_deletes_list(self, word):
        deletes = set()

        queue = deque([word])

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

    def create_dictionary_entry(self, word):
        word = word.lower()

        if self.dictionary.has_word(word):
            self.dictionary.increment_frequency(word)
            return False

        self.dictionary.insert_word(word)

        self._update_longest_word(word)

        for delete in self.get_deletes_list(word):
            self.dictionary.add_suggestion(delete, word)

        return True

    def get_suggestions(
        self,
        word,
        max_edit_distance=None,
        least_word_suggestions=1,
    ):
        if max_edit_distance is None:
            max_edit_distance = self.max_edit_distance

        word = word.lower()

        if word.isdigit():
            return [(word, (0, 0))]

        if (
            len(word) - self.longest_word_length
        ) > max_edit_distance:
            return []

        suggestions = {}
        queue = deque([word])
        visited = {word}

        min_distance = float("inf")

        while queue:
            candidate = queue.popleft()

            if (
                len(suggestions) >= least_word_suggestions
                and len(word) - len(candidate) > min_distance
            ):
                break

            if self.dictionary.has_word(candidate):

                freq = self.dictionary.get_frequency(candidate)

                if freq > 0:
                    suggestions[candidate] = (
                        freq,
                        len(word) - len(candidate),
                    )

                    min_distance = min(
                        min_distance,
                        len(word) - len(candidate),
                    )

                for real_word in self.dictionary.get_suggestions(candidate):

                    if real_word in suggestions:
                        continue

                    distance = damerau_levenshtein(
                        real_word,
                        word,
                    )

                    if distance <= max_edit_distance:

                        suggestions[real_word] = (
                            self.dictionary.get_frequency(real_word),
                            distance,
                        )

                        min_distance = min(
                            min_distance,
                            distance,
                        )

            if (
                len(word) - len(candidate)
                < max_edit_distance
            ):
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