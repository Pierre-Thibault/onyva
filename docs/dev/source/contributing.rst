Contributing
============

Setup
-----

Requirements:

- Python 3.14+
- `uv <https://docs.astral.sh/uv/>`_
- Nix (optional, for reproducible environments via uv2nix)

Install dependencies:

.. code-block:: bash

   git clone https://github.com/user/onyva.git
   cd onyva
   uv sync


Commands
--------

All commands are run with ``uv run <command>``.

check
~~~~~

Runs all code quality checks in sequence:

.. code-block:: bash

   uv run check

Steps executed:

1. **Ruff lint** — enforces code style and docstring conventions
2. **Ruff format** — verifies formatting without modifying files
3. **Basedpyright** — strict static type checking
4. **pytest** — runs all tests with 100% branch coverage required
5. **Translations** — checks that all strings are translated in fr, en, and es (if ``locales/`` exists)

All steps must pass. Exit code is non-zero if any step fails.

i18n
~~~~

Manages translation catalogs using Babel. Supported locales: ``fr``, ``en``, ``es``.

.. code-block:: bash

   uv run i18n extract    # Extract translatable strings from source code to locales/messages.pot
   uv run i18n init-all   # Create catalogs for all locales (skips existing ones)
   uv run i18n update     # Merge new strings into existing catalogs
   uv run i18n compile    # Compile .po files to .mo for production

Typical workflow for adding new translatable strings:

.. code-block:: bash

   uv run i18n extract
   uv run i18n update
   # Edit .po files in locales/<lang>/LC_MESSAGES/messages.po
   uv run i18n compile

docs
~~~~

Builds Sphinx documentation for users and developers.

.. code-block:: bash

   uv run docs user                # Build user docs for all languages (fr, en, es)
   uv run docs user --lang en      # Build user docs for a specific language
   uv run docs user extract        # Extract translatable strings from user docs
   uv run docs user update         # Update user doc translation catalogs
   uv run docs dev                 # Build developer documentation
   uv run docs publish             # Build all user docs and prepare for GitHub Pages

The ``publish`` command outputs to ``docs/_publish/`` with an ``index.html`` language selector
that redirects to English by default.

onyva
~~~~~

Starts the web application:

.. code-block:: bash

   uv run onyva


Coding Standards
----------------

Formatting
~~~~~~~~~~

`Ruff <https://docs.astral.sh/ruff/>`_ is used for both linting and formatting.

- Line length: 120 characters
- Docstrings follow the `Google style <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_
  and are enforced by pydocstyle (Ruff D rules with ``convention = "google"``)
- Docstrings are required on all public functions, classes, and modules
- Use ``# pragma: no cover`` to exclude unreachable or stub code from coverage
- Use ``# pyright: ignore[<rule>]`` to suppress specific type errors when the pattern is valid
  but cannot be inferred by basedpyright

Docstrings are not required in:

- Test files (``tests/**/*.py``)
- Sphinx config files (``docs/**/conf.py``)

Example of a Google-style docstring:

.. code-block:: python

   def parse_file(file: Path) -> list[ToDo]:
       """Parse a Markdown file and return a list of todos.

       Args:
           file: Path to the Markdown file to parse.

       Returns:
           List of ToDo objects in file order.
       """

Type Checking
~~~~~~~~~~~~~

`basedpyright <https://github.com/DetachHead/basedpyright>`_ runs in strict mode targeting
Python 3.14. All code must be fully typed. Private Pydantic fields use ``PrivateAttr``;
class-level constants use ``ClassVar``.


Tests
-----

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   uv run pytest                                   # Run all tests
   uv run pytest --cov --cov-report=term-missing   # With coverage report

100% branch coverage is required. The ``check`` command enforces this.

Test Structure
~~~~~~~~~~~~~~

The ``tests/`` directory mirrors the ``src/`` structure:

.. code-block:: text

   src/onyva/core/models.py   →  tests/onyva/core/test_models.py
   src/onyva/core/parser.py   →  tests/onyva/core/test_parser.py
   src/onyva/web/app.py       →  tests/onyva/web/test_app.py
   src/scripts/check.py       →  tests/scripts/test_check.py

Parser tests use paired fixture files:

.. code-block:: text

   tests/onyva/core/fixtures/parser/simple.md      # Markdown input
   tests/onyva/core/fixtures/parser/simple.yaml    # Expected output as YAML

Script Test Caching
~~~~~~~~~~~~~~~~~~~

Script tests (``tests/scripts/``) invoke external tools and are slow to run. To avoid
re-running them unnecessarily, a hash-based cache skips tests when the script file has not
changed since the last successful run.

How it works:

1. Before each script test, ``conftest.py`` computes the SHA-256 hash of the script file.
2. It compares this hash against the value stored in ``tests/scripts/.script_hashes.json``.
3. If the hash is unchanged, the test is skipped via ``pytest.skip()``.
4. When a test passes, the hash is updated in the cache file.

To opt in, a test module must declare a ``SCRIPT_NAME`` module-level variable matching the
script filename (without ``.py``):

.. code-block:: python

   SCRIPT_NAME = "check"  # targets src/scripts/check.py

   @pytest.fixture(autouse=True)
   def _skip(skip_if_unchanged: None) -> None:
       pass

The cache file ``tests/scripts/.script_hashes.json`` is committed to version control so that
CI also skips unchanged scripts between runs.

.. note::

   Script source files are excluded from the coverage requirement
   (``omit = ["src/scripts/*"]`` in ``pyproject.toml``), but their tests still run when the
   script has changed.
