import re


class Tokenizer:
    _TOKEN_RE = re.compile(r"\S+")

    _PUNCT_RE = re.compile(
        r"""[\.’'\[\](){}⟨⟩:,،、‒–—―…!.‹›«»‐\-?‘’“”";/⁄·&*@•^†‡°¡¿※#№÷×ºª%‰+−=‱¶′″‴§~_|‖¦©℗®℠™¤₳฿₵¢₡₢$₫₯֏₠€ƒ₣₲₴₭₺₾ℳ₥₦₧₱₰£៛₽₹₨₪৳₸₮₩¥]"""
    )

    _NUMBER_RE = re.compile(r"-?\d+(?:[\d,])*(?:\.\d+)?")

    _CAMEL_RE = re.compile(r".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)")

    @staticmethod
    def removeDuplicates(seq):
        seen = set()
        result = []

        for item in seq:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result

    @staticmethod
    def _add(results, seen, text, start, end):
        if not text:
            return

        token = (text, (start, end), len(text))

        if token not in seen:
            seen.add(token)
            results.append(token)

    @staticmethod
    def tokenize(message, include_subtokens=True):
        results = []
        seen = set()

        for match in Tokenizer._TOKEN_RE.finditer(message):
            text = match.group()
            start = match.start()
            end = match.end() - 1

            # Primary token
            Tokenizer._add(results, seen, text, start, end)

            if not include_subtokens:
                continue

            # punctuation + left/right fragments
            for punct in Tokenizer._PUNCT_RE.finditer(text):
                p_start = start + punct.start()
                p_end = start + punct.end() - 1

                Tokenizer._add(results, seen, punct.group(), p_start, p_end)
                Tokenizer._add(results, seen, text[: punct.start()], start, p_start)
                Tokenizer._add(results, seen, text[punct.end() :], p_end + 1, end)

            # numbers
            for number in Tokenizer._NUMBER_RE.finditer(text):
                Tokenizer._add(
                    results,
                    seen,
                    number.group(),
                    start + number.start(),
                    start + number.end() - 1,
                )

            # camelCase
            for part in Tokenizer._CAMEL_RE.finditer(text):
                Tokenizer._add(
                    results,
                    seen,
                    part.group(),
                    start + part.start(),
                    start + part.end() - 1,
                )

        return sorted(results, key=lambda token: token[1][0])
