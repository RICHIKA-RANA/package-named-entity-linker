from talkingdb_nel.services.symbolic.tokenizer import Tokenizer


class NoTag:
    skip_list = {
        ':', ';', '"', "'", '<', ',', '>', '.', '/', '?', '{', '[',
        '}', ']', '\\', '|', '+', '=', '-', '_', ')', '(', '*', '&',
        '^', '%', '$', '#', '@', '!', '~', '`'
    }

    @classmethod
    def get_no_tags(cls, input_text, found_texts, tokenize=True):
        """
        Return portions of the input not covered by NER entities.

        Parameters
        ----------
        input_text : str
        found_texts : list[dict]
            Expected entity format:
                {
                    "index": [start, end],   # inclusive
                    ...
                }
        tokenize : bool
            If True, split untagged spans into tokens.
        """
        entities = sorted(
            (
                {
                    **entity,
                    "index": [
                        entity["index"][0],
                        entity["index"][1] + 1,  # inclusive -> exclusive
                    ],
                }
                for entity in found_texts
            ),
            key=lambda e: e["index"][0],
        )

        current = 0
        spans = []

        for entity in entities:
            start, end = entity["index"]

            if start > current:
                text = input_text[current:start].strip()
                if cls.check(text):
                    spans.append(
                        {
                            "index": [current, start],
                            "surface_text": text.lower(),
                        }
                    )

            current = max(current, end)

        if current < len(input_text):
            text = input_text[current:].strip()
            if cls.check(text):
                spans.append(
                    {
                        "index": [current, len(input_text)],
                        "surface_text": text.lower(),
                    }
                )

        return cls.tokenize_no_tags(spans) if tokenize else spans

    @classmethod
    def tokenize_no_tags(cls, spans):
        """
        Tokenize no-tag spans using the shared tokenizer.
        Only retain the primary lexical tokens.
        """
        output = []

        for span in spans:
            base = span["index"][0]
            span_text = span["surface_text"]

            for token, (start, end), length in Tokenizer.tokenize(span_text, include_subtokens=False):
                # Skip punctuation/subtokens. Keep only the primary token.
                if length != (end - start + 1):
                    continue

                if not cls.check(token):
                    continue

                if not any(ch.isalnum() for ch in token):
                    continue
                
                output.append(
                    {
                        "index": [base + start, base + end],
                        "surface_text": token.lower(),
                    }
                )

        return output

    @classmethod
    def check(cls, text):
        text = text.strip().lower()
        return bool(text) and text not in cls.skip_list