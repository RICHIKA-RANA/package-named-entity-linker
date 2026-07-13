import sqlite3

from talkingdb_nel.services.rule.regex_model import RegexModel


def create_db():
    conn = sqlite3.connect(":memory:")
    RegexModel.init_db(conn)
    return conn


def test_make_id():
    assert RegexModel.make_id("Phone Number") == "regex::phone-number"


def test_add_rule():
    model = RegexModel()

    model.add_rule("phone", r"\d+")

    assert "phone" in model.rules
    assert len(model.rules["phone"]) == 1
    assert model.rules["phone"][0].pattern == r"\d+"


def test_remove_rule():
    model = RegexModel()

    model.add_rule("phone", r"\d+")
    model.remove_rule("phone")

    assert "phone" not in model.rules


def test_clear():
    model = RegexModel()

    model.add_rule("phone", r"\d+")
    model.add_rule("email", r".*@.*")

    model.clear()

    assert model.rules == {}


def test_save_and_load():
    conn = create_db()

    model = RegexModel()
    model.add_rule("phone", r"\d+")
    model.add_rule("email", r"\S+@\S+")

    model.save(conn)

    loaded = RegexModel.load(conn)

    assert "phone" in loaded.rules
    assert "email" in loaded.rules

    assert loaded.rules["phone"][0].pattern == r"\d+"
    assert loaded.rules["email"][0].pattern == r"\S+@\S+"


def test_overwrite():
    conn = create_db()

    model = RegexModel()
    model.add_rule("phone", r"\d+")
    model.save(conn)

    model.clear()
    model.add_rule("email", r"\S+@\S+")
    model.save(conn)

    loaded = RegexModel.load(conn)

    assert "phone" not in loaded.rules
    assert "email" in loaded.rules


def test_to_dict():
    model = RegexModel()

    model.add_rule("phone", r"\d+")

    assert model.to_dict() == {
        "phone": [r"\d+"]
    }


def test_invalid_regex_rejected():
    model = RegexModel()

    try:
        model.add_rule("bad", "(")
        assert False
    except Exception:
        pass