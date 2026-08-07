class RegexController:
    def __init__(self, regex_model):
        self.regex_model = regex_model

    def process(self, input_query: str):
        results = []

        for rule_id, rules in self.regex_model.rules.items():
            for rule in rules:
                for match in rule.compiled.finditer(input_query):
                    results.append(
                        {
                            "surfaceText": match.group(),
                            "rule": rule_id,
                            "index": [
                                match.start(),
                                match.end(),
                            ],
                            "regex": rule.pattern,
                            "meronyms": [],
                        }
                    )

        return results
