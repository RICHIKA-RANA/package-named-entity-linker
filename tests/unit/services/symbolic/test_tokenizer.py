from talkingdb_nel.services.symbolic.tokenizer import Tokenizer


def test_simple_tokenization():
    tokens = Tokenizer.tokenize("Hello World")
    assert ("Hello", (0, 4), 5) in tokens
    assert ("World", (6, 10), 5) in tokens


def test_camel_case():
    tokens = Tokenizer.tokenize("helloWorld")
    assert any(t[0] == "hello" for t in tokens)
    assert any(t[0] == "World" for t in tokens)


def test_numbers():
    tokens = Tokenizer.tokenize("Price is 12.50")
    assert any(t[0] == "12.50" for t in tokens)