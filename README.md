<div align="center">

<img src="docs/images/hero.png" alt="TalkingDB Named Entity Linker">

# TalkingDB Named Entity Linker

**Symbolic Named Entity Linking for canonical entity resolution**

<p>

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pytest](https://img.shields.io/badge/Tested_with-Pytest-0A9EDC?logo=pytest)
![License](https://img.shields.io/badge/License-AGPL_v3-blue)

</p>

</div>

---

TalkingDB Named Entity Linker (NEL) identifies named entities in text and resolves them to canonical entities stored in a knowledge base using a symbolic matching pipeline.

<p align="center">
    <img src="docs/images/architecture.png" width="90%" alt="Architecture">
</p>

## Features

- Phrase matching
- Word matching
- Regex matching
- Tokenization
- Lemmatization
- Canonical entity resolution
- SQLite-backed dictionaries
- FastAPI REST API

## Installation

```bash
poetry install --with dev
```

## Development

```bash
make local
make format
make lint
make test
make coverage
make check
```

## Project Structure

```text
talkingdb_nel/
├── api/
├── services/
│   ├── entity/
│   └── symbolic/
└── main.py
```

## License

GNU Affero General Public License v3.0 (AGPL-3.0).

## Maintainer

**Mayank Gupta**  
mayank.g@smarter.codes