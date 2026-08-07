from talkingdb.models.rule.regex import RegexModel

from talkingdb_nel.services.symbolic.regex import RegexController


def build_controller():
    model = RegexModel.create(
        RegexModel.make_id("test"),
    )

    model.add_rule("phone", r"\d{10}")
    model.add_rule("email", r"\S+@\S+")

    return RegexController(model)


def test_no_match():
    controller = build_controller()

    assert controller.process("hello world") == []


def test_phone():
    controller = build_controller()

    results = controller.process("Call me on 9876543210 tomorrow.")

    assert len(results) == 1
    assert results[0]["surfaceText"] == "9876543210"
    assert results[0]["rule"] == "phone"


def test_email():
    controller = build_controller()

    results = controller.process("Mail john@test.com today.")

    assert len(results) == 1
    assert results[0]["surfaceText"] == "john@test.com"
    assert results[0]["rule"] == "email"


def test_multiple_matches():
    controller = build_controller()

    results = controller.process("1111111111 2222222222")

    assert len(results) == 2


def test_case_insensitive():
    model = RegexModel.create(
        RegexModel.make_id("test"),
    )

    model.add_rule("hello", "hello")

    controller = RegexController(model)

    results = controller.process("HELLO")

    assert len(results) == 1
    assert results[0]["surfaceText"] == "HELLO"


def test_multiple_rules():
    model = RegexModel.create(
        RegexModel.make_id("test"),
    )

    model.add_rule("number", r"\d+")
    model.add_rule("word", r"abc")

    controller = RegexController(model)

    results = controller.process("abc 123")

    assert len(results) == 2

    rules = {result["rule"] for result in results}

    assert rules == {"number", "word"}
