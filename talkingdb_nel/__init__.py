from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib


def _get_version() -> str:
    try:
        return version("package-named-entity-linker")
    except PackageNotFoundError:
        pass

    try:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"

        with pyproject.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
        return "0.0.0"


__version__ = _get_version()