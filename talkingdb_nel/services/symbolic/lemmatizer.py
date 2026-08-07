from __future__ import annotations

import copy

from talkingdb.models.dictionary.dictionary import DictionaryModel


class Lemmatizer:
    """
    Compound-word lemmatizer.

    Input:
        [
            {
                "surface_text": "...",
                "index": [start, end],
                ...
            }
        ]

    Output:
        (
            remaining_no_tags,
            [
                {
                    "index": [...],
                    "lemmatized_tokens": [...]
                }
            ]
        )
    """

    def __init__(self, dictionary: DictionaryModel):
        self.dictionary = dictionary
        self.ans = []
        self.remaining_no_tags = []

    def lemmatize(self, tokenlist):
        self.ans = []
        self.remaining_no_tags = []
        self._break_into_unbound_morphemes_util(tokenlist)
        return self.remaining_no_tags, self.ans

    def _break_into_unbound_morphemes_util(self, tokenlist):
        for token in tokenlist:
            word = token["surface_text"]
            index = token["index"]

            token_added = False

            for split in range(3, len(word) + 1):
                prefix = word[:split]

                if self.dictionary.has_word(prefix):
                    current = [prefix]
                    if self._break_into_unbound_morphemes(
                        word[split:],
                        current,
                        index,
                    ):
                        token_added = True

            if not token_added:
                self.remaining_no_tags.append(token)

    def _break_into_unbound_morphemes(
        self,
        word,
        current,
        index,
    ):
        if not word:
            self.ans.append(
                {
                    "index": index,
                    "lemmatized_tokens": copy.deepcopy(current),
                }
            )
            return True

        found = False

        for split in range(3, len(word) + 1):
            prefix = word[:split]

            if self.dictionary.has_word(prefix):
                current.append(prefix)

                if self._break_into_unbound_morphemes(
                    word[split:],
                    current,
                    index,
                ):
                    found = True

                current.pop()

        return found