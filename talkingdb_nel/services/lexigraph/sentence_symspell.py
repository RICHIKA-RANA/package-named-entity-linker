from collections import deque

from talkingdb_nel.services.lexigraph.distance import (
    damerau_levenshtein,
)


class SentenceSymSpell:
    """
    SymSpell implementation operating on complete
    surface-text phrases instead of individual words.
    """

    def __init__(self, store, max_edit_distance=2):
        self.store = store
        self.max_edit_distance = max_edit_distance

        self.longest_word_length = (
            self.store.get_metadata(
                "sentence_longest_length",
                0,
            )
        )

    def _update_longest(self, sentence):

        if len(sentence) > self.longest_word_length:
            self.longest_word_length = len(sentence)

            self.store.set_metadata(
                "sentence_longest_length",
                self.longest_word_length,
            )

    def get_deletes_list(self, word):
        deletes = set()

        queue = deque([word])

        for _ in range(self.max_edit_distance):

            next_queue = deque()

            while queue:

                current = queue.popleft()

                if len(current) <= 1:
                    continue

                for i in range(len(current)):

                    delete = current[:i] + current[i + 1 :]

                    if delete in deletes:
                        continue

                    deletes.add(delete)
                    next_queue.append(delete)

            queue = next_queue

        return deletes

    def create_dictionary_entry(self, sentence):

        sentence = sentence.lower().strip()

        if not sentence:
            return False

        if self.store.has_word(sentence):
            self.store.increment_frequency(sentence)
            return False

        self.store.insert_word(sentence)

        self._update_longest(sentence)

        for delete in self.get_deletes_list(sentence):
            self.store.add_suggestion(delete, sentence)

        return True

    def get_suggestions(
        self,
        sentence,
        max_edit_distance=None,
    ):

        if max_edit_distance is None:
            max_edit_distance = self.max_edit_distance

        sentence = sentence.lower()

        if (
            len(sentence) - self.longest_word_length
            > max_edit_distance
        ):
            return []

        suggestions = {}
        queue = deque([sentence])
        visited = {sentence}

        while queue:

            candidate = queue.popleft()

            if self.store.has_word(candidate):

                if self.store.get_frequency(candidate):

                    suggestions[candidate] = (
                        self.store.get_frequency(candidate),
                        damerau_levenshtein(
                            sentence,
                            candidate,
                        ),
                    )

                for real in self.store.get_suggestions(candidate):

                    if real in suggestions:
                        continue

                    distance = damerau_levenshtein(
                        sentence,
                        real,
                    )

                    if distance <= max_edit_distance:

                        suggestions[real] = (
                            self.store.get_frequency(real),
                            distance,
                        )

            if (
                len(sentence)
                - len(candidate)
                < max_edit_distance
            ):

                for i in range(len(candidate)):

                    delete = (
                        candidate[:i]
                        + candidate[i + 1 :]
                    )

                    if delete not in visited:
                        visited.add(delete)
                        queue.append(delete)

        return sorted(
            suggestions.items(),
            key=lambda x: (
                x[1][1],
                -x[1][0],
            ),
        )