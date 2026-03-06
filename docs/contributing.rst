Contributing
============

Development Setup
-----------------

chardet uses `uv <https://docs.astral.sh/uv/>`_ for dependency management:

.. code-block:: bash

   git clone https://github.com/chardet/chardet.git
   cd chardet
   uv sync                    # install Python dependencies
   uv pip install -e rust     # build/install Rust extension in editable mode
   prek install               # set up pre-commit hooks (ruff lint+format, etc.)

You need a Rust toolchain (stable) for local builds of the extension module.

Running Tests
-------------

Tests use pytest. Test data is auto-cloned from the
`chardet/test-data <https://github.com/chardet/test-data>`_ repo on
first run (cached in ``tests/data/``, gitignored).

.. code-block:: bash

   uv run python -m pytest                              # run all tests
   uv run python -m pytest tests/test_api.py            # single file
   uv run python -m pytest tests/test_api.py::test_detect_empty  # single test
   uv run python -m pytest -x                           # stop on first failure

Accuracy tests are dynamically parametrized from the test data via
``conftest.py``.

Linting and Formatting
----------------------

chardet uses `Ruff <https://docs.astral.sh/ruff/>`_ with
``select = ["ALL"]`` and targeted ignores (see ``pyproject.toml``):

.. code-block:: bash

   uv run ruff check .        # lint
   uv run ruff check --fix .  # lint with auto-fix
   uv run ruff format .       # format

Pre-commit hooks run ruff automatically on each commit.

Training Models
---------------

Bigram frequency models are trained from the
`CulturaX <https://huggingface.co/datasets/uonlp/CulturaX>`_ multilingual
corpus (via Hugging Face) plus HTML data (separate from the evaluation
test suite):

.. code-block:: bash

   uv run python scripts/train.py

Training data is cached in ``data/`` (gitignored). Models are saved to
``src/chardet/models/models.bin``.

Benchmarks and Diagnostics
--------------------------

.. code-block:: bash

   uv run python scripts/benchmark_time.py     # latency benchmarks
   uv run python scripts/benchmark_memory.py   # memory usage benchmarks
   uv run python scripts/diagnose_accuracy.py  # detailed accuracy diagnostics
   uv run python scripts/compare_detectors.py  # compare against other detectors

Building Documentation
----------------------

.. code-block:: bash

   uv sync --group docs                          # install Sphinx, Furo, etc.
   uv run sphinx-build docs docs/_build          # build HTML docs
   uv run sphinx-build -W docs docs/_build       # build with warnings as errors

Docs are published to `ReadTheDocs <https://chardet.readthedocs.io>`_
on tag push.

Architecture Overview
---------------------

The public Python API lives in ``src/chardet`` and forwards detection calls to
the Rust extension module ``chardet_rs._chardet_rs``.

The detection pipeline itself is implemented in ``rust/src/pipeline``.
Stages are executed in order — each stage either returns a definitive result
or passes to the next:

1. **BOM** (``bom.rs``) — byte order mark
2. **UTF-16/32 patterns** (``utf1632.rs``) — null-byte patterns
3. **Escape sequences** (``escape.rs``) — ISO-2022-JP/KR, HZ-GB-2312
4. **Binary detection** (``binary.rs``) — null bytes / control chars
5. **Markup charset** (``markup.rs``) — ``<meta charset>`` / ``<?xml encoding>``
6. **ASCII** (``ascii.rs``) — pure 7-bit check
7. **UTF-8** (``utf8.rs``) — structural multi-byte validation
8. **Byte validity** (``validity.rs``) — eliminate invalid encodings
9. **CJK gating** (in orchestrator) — eliminate spurious CJK candidates
10. **Structural probing** (``structural.rs``) — multi-byte encoding fit
11. **Statistical scoring** (``statistical.rs``) — bigram frequency models
12. **Post-processing** (orchestrator) — confusion groups, niche demotion

Key Rust types:

- ``DetectionResult`` (``models.rs``) — ``encoding``, ``confidence``,
  ``language``
- ``EncodingInfo`` (``registry.rs``) — name/aliases/era/codec metadata
- ``EncodingEra`` (``enums.rs``) — bitflag for filtering candidates
- model tables loaded from ``src/chardet/models/models.bin``

Model format: binary file ``src/chardet/models/models.bin`` — sparse
bigram tables loaded via ``struct.unpack``. Each model is a 65,536-byte
lookup table indexed by ``(b1 << 8) | b2``.

Rust Extension Build
--------------------

The Python extension module is built from ``rust/`` using maturin:

.. code-block:: bash

   uv pip install -e rust

For direct Rust-only checks:

.. code-block:: bash

   cargo test --manifest-path rust/Cargo.toml

Versioning
----------

Version is derived from git tags via ``hatch-vcs``. The tag is the
single source of truth — no hardcoded version strings. The generated
``src/chardet/_version.py`` is gitignored and should never be committed.

Conventions
-----------

- ``from __future__ import annotations`` in all source files (except
  generated/version files when applicable)
- Frozen dataclasses with ``slots=True`` for data types
- Ruff with ``select = ["ALL"]`` and targeted ignores
- Training data (CulturaX corpus + HTML) is never the same as
  evaluation data (chardet test suite)
