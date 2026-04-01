Contribuer
==========

Environnement de développement
------------------------------

Prérequis :

- Python 3.14+
- uv
- Nix (optionnel)

Installation :

.. code-block:: bash

   git clone https://github.com/user/onyva.git
   cd onyva
   uv sync

Scripts disponibles
-------------------

.. code-block:: bash

   uv run check      # Vérifications de code
   uv run docs       # Documentation
   uv run i18n       # Internationalisation

Tests
-----

.. code-block:: bash

   uv run pytest

Conventions de code
-------------------

- Formatage : Ruff
- Types : Basedpyright en mode strict
- Tests : pytest + pytest-bdd
