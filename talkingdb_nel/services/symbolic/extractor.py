from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .distance import get_distance
from .tokenizer import Tokenizer


@dataclass(slots=True)
class Token:
    text: str
    start: int
    end: int


@dataclass(slots=True)
class ActiveMatch:
    """
    A phrase currently being matched while scanning the sentence.
    """

    phrase: str
    start_word: int
    end_word: int

    # Remaining words that must still be matched.
    remaining: list[str] = field(default_factory=list)

    # Legacy "length budget".
    budget: float = 3.0

    # Additional penalty accumulated when crossing breakpoints.
    penalty: float = 0.0

    crossed_breakpoint: bool = False

    @property
    def complete(self) -> bool:
        return not self.remaining


class SurfaceTextExtractor:
    def __init__(self, word_matcher, phrase_matcher):
        self.word_matcher = word_matcher
        self.phrase_matcher = phrase_matcher

    @staticmethod
    def _penalize(distance: int) -> float:
        """
        Legacy penalty function.

        One skipped word costs 0.5 budget,
        two skipped words costs 1.5,
        three skipped words costs 2.5, etc.
        """
        return distance - 0.5

    @staticmethod
    def _new_match(
        phrase: str,
        token_index: int,
    ) -> ActiveMatch:
        words = phrase.lower().split()

        remaining = words.copy()

        if words:
            remaining.remove(words[0])

        return ActiveMatch(
            phrase=phrase.lower(),
            start_word=token_index,
            end_word=token_index,
            remaining=remaining,
        )

    @staticmethod
    def _clone_match(match: ActiveMatch) -> ActiveMatch:
        return ActiveMatch(
            phrase=match.phrase,
            start_word=match.start_word,
            end_word=match.end_word,
            remaining=match.remaining.copy(),
            budget=match.budget,
            penalty=match.penalty,
            crossed_breakpoint=match.crossed_breakpoint,
        )

    def extract(
        self,
        text: str,
        breakpoints: list[tuple[int, int]],
        *,
        word_correction: bool = True,
        max_word_edit_distance: int = 1,
        least_each_word_suggestions: int = 1,
    ):
        """
        Step 1:
            • normalize breakpoints
            • tokenize
            • build word-index mapping

        Remaining stages are implemented in subsequent steps.
        """

        # Replace breakpoint regions with spaces so token positions remain stable.
        normalized = text
        for start, length in breakpoints:
            normalized = (
                normalized[:start] + (" " * length) + normalized[start + length :]
            )

        breakpoint_starts = {start for start, _ in breakpoints}

        # Primary tokens only.
        raw_tokens = Tokenizer.tokenize(
            normalized,
            include_subtokens=False,
        )

        tokens: list[Token] = [
            Token(
                text=value.lower(),
                start=start,
                end=end,
            )
            for value, (start, end), _ in raw_tokens
        ]

        # Map token index -> Token
        word_index_reference = {i: token for i, token in enumerate(tokens)}

        # Determine which token immediately follows a breakpoint.
        breakpoints_next_word_indices: set[int] = set()

        for index, token in enumerate(tokens):
            for bp in breakpoint_starts:
                if bp < token.start:
                    breakpoints_next_word_indices.add(index)
                    break

        # Continue with remaining extraction pipeline.
        return self._extract(
            normalized_text=normalized.lower(),
            original_text=text,
            tokens=tokens,
            word_index_reference=word_index_reference,
            breakpoints_next_word_indices=breakpoints_next_word_indices,
            word_correction=word_correction,
            max_word_edit_distance=max_word_edit_distance,
            least_each_word_suggestions=least_each_word_suggestions,
        )

    def _build_word_corrections(
        self,
        tokens: list[Token],
        *,
        word_correction: bool,
        max_word_edit_distance: int,
        least_each_word_suggestions: int,
    ) -> dict[str, dict[str, tuple[int, int]]]:
        """
        Build

            {
                original_word: {
                    candidate: (frequency, edit_distance)
                }
            }

        Equivalent to the legacy `possible_corrections`.
        """

        cache: dict[str, list] = {}
        corrections: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)

        lookup_distance = max_word_edit_distance if word_correction else 0

        for token in tokens:
            word = token.text

            if word not in cache:
                suggestions = self.word_matcher.get_suggestions(
                    word,
                    max_edit_distance=lookup_distance,
                    least_word_suggestions=least_each_word_suggestions,
                )

                cache[word] = suggestions

            found_original = False

            for suggestion in cache[word]:
                #
                # Supports both:
                #
                # ("apple", (123,0))
                #
                # and
                #
                # Suggestion(...)
                #
                if isinstance(suggestion, tuple):
                    candidate, score = suggestion
                    freq, distance = score
                else:
                    candidate = suggestion.term
                    freq = suggestion.count
                    distance = suggestion.distance

                corrections[word][candidate] = (freq, distance)

                if candidate.lower() == word:
                    found_original = True

            # Preserve the original word even if not in dictionary.
            if not found_original:
                corrections[word][word] = (0, 0)

        return corrections

    def _build_phrase_cache(
        self,
        possible_corrections: dict[str, dict[str, tuple[int, int]]],
        tokens: list[Token],
    ) -> dict[str, list]:
        """
        Cache all phrase suggestions required by the extraction algorithm.

        Returns

            {
                "new": [...],
                "new york": [...],
                ...
            }

        Every key is lower-case.
        """

        cache: dict[str, list] = {}

        def lookup(
            text: str,
            *,
            required_words: list[str] | None = None,
        ) -> list:
            key = text.lower()

            if key not in cache:
                suggestions = self.phrase_matcher.get_suggestions(
                    key,
                    max_edit_distance=0,
                )

                if required_words:
                    filtered = []

                    for suggestion in suggestions:
                        phrase = (
                            suggestion[0]
                            if isinstance(suggestion, tuple)
                            else suggestion.term
                        ).lower()

                        words = phrase.split()

                        phrase_counter = Counter(words)
                        required_counter = Counter(required_words)

                        if all(
                            phrase_counter[word] >= count
                            for word, count in required_counter.items()
                        ):
                            filtered.append(suggestion)

                    suggestions = filtered

                #
                # Store under the lookup key.
                #
                cache[key] = suggestions

                #
                # Also index every phrase by each constituent word so
                # _process_token() can find multi-word phrases while
                # processing subsequent tokens.
                #
                if required_words:
                    for word in required_words:
                        bucket = cache.setdefault(word.lower(), [])

                        existing = {
                            (s[0] if isinstance(s, tuple) else s.term).lower()
                            for s in bucket
                        }

                        for suggestion in suggestions:
                            phrase = (
                                suggestion[0]
                                if isinstance(suggestion, tuple)
                                else suggestion.term
                            ).lower()

                            if phrase not in existing:
                                bucket.append(suggestion)
                                existing.add(phrase)

            return cache[key]

        #
        # Single-word phrases
        #
        for token in tokens:
            for candidate in possible_corrections[token.text]:
                lookup(
                    candidate,
                    required_words=[candidate.lower()],
                )

        #
        # Adjacent two-word phrases
        #
        for i in range(len(tokens) - 1):
            left = tokens[i].text
            right = tokens[i + 1].text

            for left_candidate in possible_corrections[left]:
                for right_candidate in possible_corrections[right]:
                    lookup(
                        f"{left_candidate} {right_candidate}",
                        required_words=[
                            left_candidate.lower(),
                            right_candidate.lower(),
                        ],
                    )

        return cache

    def _process_token(
        self,
        *,
        token_index: int,
        token: Token,
        possible_corrections: dict[str, dict[str, tuple[int, int]]],
        phrase_cache: dict[str, list],
        tokens: list[Token],
        current_queue,
        next_queue,
    ):
        """
        Port of alternate_extract() queue update logic.
        """

        word_options = list(
            {option.lower() for option in possible_corrections[token.text]}
        )
        #
        # Current-word phrase suggestions
        #
        for option in word_options:
            for suggestion in phrase_cache.get(option, []):
                phrase = (
                    suggestion[0] if isinstance(suggestion, tuple) else suggestion.term
                ).lower()

                words = phrase.split()

                if option not in words:
                    continue

                remaining = words.copy()

                if option in remaining:
                    remaining.remove(option)

                if phrase not in current_queue and phrase not in next_queue:
                    next_queue[phrase].append(
                        ActiveMatch(
                            phrase=phrase,
                            start_word=token_index,
                            end_word=token_index,
                            remaining=remaining,
                        )
                    )

                elif phrase in current_queue and phrase not in next_queue:
                    moved = []
                    stayed = []

                    for state in current_queue.pop(phrase):
                        if state.crossed_breakpoint:
                            # Legacy behavior:
                            # once a breakpoint has been crossed, an existing phrase
                            # cannot continue matching.
                            stayed.append(state)

                        elif option in state.remaining:
                            state.remaining.remove(option)
                            state.end_word = token_index
                            moved.append(state)

                        else:
                            stayed.append(state)

                    if stayed:
                        current_queue[phrase] = stayed

                    if moved:
                        next_queue[phrase].extend(moved)

                    #
                    # Legacy duplicate-start behaviour.
                    #
                    if not moved or any(s.crossed_breakpoint for s in moved):
                        next_queue[phrase].append(
                            ActiveMatch(
                                phrase=phrase,
                                start_word=token_index,
                                end_word=token_index,
                                remaining=remaining.copy(),
                            )
                        )

                elif phrase not in current_queue and phrase in next_queue:
                    continue

                else:
                    stayed = []
                    moved = []

                    for state in current_queue.pop(phrase):
                        if state.crossed_breakpoint:
                            # Legacy behavior:
                            # once a breakpoint has been crossed, an existing phrase
                            # cannot continue matching.
                            stayed.append(state)

                        elif option in state.remaining:
                            state.remaining.remove(option)
                            state.end_word = token_index
                            moved.append(state)

                        else:
                            stayed.append(state)

                    if stayed:
                        current_queue[phrase] = stayed

                    if moved:
                        next_queue[phrase].extend(moved)

                        #
                        # Preserve legacy ordering.
                        #
                        next_queue[phrase].sort(
                            key=lambda s: (s.start_word, s.end_word)
                        )

        #
        # Adjacent 2-word phrase suggestions
        #
        if token_index + 1 < len(tokens):
            next_token = tokens[token_index + 1]

            next_options = {
                option.lower() for option in possible_corrections[next_token.text]
            }

            for option in word_options:
                for next_option in next_options:
                    key = f"{option} {next_option}"

                    for suggestion in phrase_cache.get(key, []):
                        phrase = (
                            suggestion[0]
                            if isinstance(suggestion, tuple)
                            else suggestion.term
                        ).lower()

                        if option not in phrase:
                            continue

                        remaining = phrase.split()

                        if option in remaining:
                            remaining.remove(option)

                        if phrase not in current_queue and phrase not in next_queue:
                            next_queue[phrase].append(
                                ActiveMatch(
                                    phrase=phrase,
                                    start_word=token_index,
                                    end_word=token_index,
                                    remaining=remaining,
                                )
                            )

                        elif phrase in current_queue and phrase not in next_queue:
                            moved = []
                            stayed = []

                            for state in current_queue.pop(phrase):
                                if state.crossed_breakpoint:
                                    # Legacy behavior:
                                    # once a breakpoint has been crossed
                                    # an existing phrase cannot continue matching.
                                    stayed.append(state)

                                elif option in state.remaining:
                                    state.remaining.remove(option)
                                    state.end_word = token_index
                                    moved.append(state)
                                else:
                                    stayed.append(state)

                            if stayed:
                                current_queue[phrase] = stayed

                            if moved:
                                next_queue[phrase].extend(moved)

                            if not moved or any(s.crossed_breakpoint for s in moved):
                                next_queue[phrase].append(
                                    ActiveMatch(
                                        phrase=phrase,
                                        start_word=token_index,
                                        end_word=token_index,
                                        remaining=remaining.copy(),
                                    )
                                )

                        elif phrase not in current_queue and phrase in next_queue:
                            continue

                        else:
                            stayed = []
                            moved = []

                            for state in current_queue.pop(phrase):
                                if state.crossed_breakpoint:
                                    # Legacy behavior:
                                    # once a breakpoint has been crossed,
                                    # an existing phrase cannot continue matching.
                                    stayed.append(state)

                                elif option in state.remaining:
                                    state.remaining.remove(option)
                                    state.end_word = token_index
                                    moved.append(state)

                                else:
                                    stayed.append(state)

                            if stayed:
                                current_queue[phrase] = stayed

                            if moved:
                                next_queue[phrase].extend(moved)

                                #
                                # Preserve legacy ordering.
                                #
                                next_queue[phrase].sort(
                                    key=lambda s: (s.start_word, s.end_word)
                                )

    def _flush_matches(
        self,
        matches: list[ActiveMatch],
    ) -> list[ActiveMatch]:
        """
        Remove duplicate phrase matches, keeping the best (lowest penalty)
        occurrence for each (phrase, span).
        """

        best: dict[tuple[str, int, int], ActiveMatch] = {}

        for match in matches:
            key = (
                match.phrase,
                match.start_word,
                match.end_word,
            )

            previous = best.get(key)

            if (
                previous is None
                or match.penalty < previous.penalty
                or (
                    match.penalty == previous.penalty and match.budget > previous.budget
                )
            ):
                best[key] = match

        return list(best.values())

    def _score_matches(
        self,
        matches: list[ActiveMatch],
        *,
        tokens: list[Token],
    ):
        """
        Convert ActiveMatch objects into scored phrase matches.
        """

        scored = []

        for match in matches:
            token_text = " ".join(
                token.text for token in tokens[match.start_word : match.end_word + 1]
            )

            score = (
                get_distance(
                    token_text,
                    match.phrase,
                    "s",
                )
                + match.penalty
            )

            scored.append((match, score))

        scored.sort(key=lambda item: item[1])

        return scored

    def _build_results(
        self,
        scored_matches,
        *,
        tokens: list[Token],
        normalized_text: str,
    ):
        """
        Convert scored phrase matches into the legacy output format.
        """

        results = []

        for match, score in scored_matches:
            # Preserve legacy behaviour:
            # ignore corrected phrases whose edit distance is non-zero.
            if abs(score - match.penalty) > 1e-9:
                continue

            start = tokens[match.start_word].start
            end = tokens[match.end_word].end

            entities = []

            suggestions = self.phrase_matcher.get_suggestions(match.phrase)
            if suggestions is not None:
                entities = suggestions

            results.append(
                {
                    "index": [start, end],
                    "surface_text": normalized_text[start : end + 1],
                    "corrected_text": match.phrase,
                    "score": -score,
                    "entities": entities,
                }
            )

        return results

    def _extract(
        self,
        *,
        normalized_text: str,
        original_text: str,
        tokens: list[Token],
        word_index_reference: dict[int, Token],
        breakpoints_next_word_indices: set[int],
        word_correction: bool,
        max_word_edit_distance: int,
        least_each_word_suggestions: int,
    ):
        """
        Step 2 onwards.

        To be implemented next:
            - word correction cache
            - phrase cache
            - queue engine
            - scoring
            - entity lookup
        """
        possible_corrections = self._build_word_corrections(
            tokens,
            word_correction=word_correction,
            max_word_edit_distance=max_word_edit_distance,
            least_each_word_suggestions=least_each_word_suggestions,
        )

        phrase_cache = self._build_phrase_cache(
            possible_corrections,
            tokens,
        )

        current_queue: dict[str, list[ActiveMatch]] = defaultdict(list)
        next_queue: dict[str, list[ActiveMatch]] = defaultdict(list)

        completed_matches: list[ActiveMatch] = []
        done_indices: set[tuple[str, int, int]] = set()

        BREAKPOINT_PENALTY = 1.5

        for index, token in enumerate(tokens):
            #
            # Breakpoint handling (legacy behaviour)
            #
            if index in breakpoints_next_word_indices:
                for phrase, states in current_queue.items():
                    for state in states:
                        key = (
                            phrase,
                            state.start_word,
                            state.end_word,
                        )

                        if key not in done_indices:
                            completed_matches.append(self._clone_match(state))

                            done_indices.add(key)

                        state.penalty += BREAKPOINT_PENALTY
                        state.crossed_breakpoint = True

            next_queue.clear()

            #
            # Process current token.
            #
            self._process_token(
                token_index=index,
                token=token,
                tokens=tokens,
                possible_corrections=possible_corrections,
                phrase_cache=phrase_cache,
                current_queue=current_queue,
                next_queue=next_queue,
            )

            #
            # Expire old matches exactly like alternate_extract().
            #
            for phrase in list(current_queue.keys()):
                survivors = []

                for state in current_queue[phrase]:
                    state.budget -= self._penalize(index - state.end_word)

                    if state.budget <= 0:
                        key = (phrase, state.start_word, state.end_word)

                        if key not in done_indices:
                            completed_matches.append(self._clone_match(state))

                            done_indices.add(key)

                    else:
                        survivors.append(state)

                if survivors:
                    next_queue[phrase].extend(survivors)

            current_queue = defaultdict(list)

            for phrase, states in next_queue.items():
                current_queue[phrase].extend(states)

        #
        # Flush remaining queue.
        #
        for phrase, states in current_queue.items():
            for state in states:
                key = (phrase, state.start_word, state.end_word)

                if key not in done_indices:
                    completed_matches.append(self._clone_match(state))

                    done_indices.add(key)

        completed_matches = self._flush_matches(completed_matches)

        scored_matches = self._score_matches(
            completed_matches,
            tokens=tokens,
        )

        return self._build_results(
            scored_matches,
            tokens=tokens,
            normalized_text=normalized_text,
        )
