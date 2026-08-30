"""Entry point for the corpus graph — see `corpusgraph.cli` for the commands.

Named `graph.py` rather than `corpusgraph.py` for the reason `scripts/changes.py` records:
a script whose name matches an installed package shadows it, because Python puts the
script's directory first on `sys.path`.
"""

from corpusgraph.cli import main

if __name__ == "__main__":
    main()
