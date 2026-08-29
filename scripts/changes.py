"""Entry point for the change feed — see `changefeed.cli` for the commands.

Named `changes.py` rather than `changefeed.py` on purpose: a script whose name matches an
installed package shadows it, because Python puts the script's directory first on
`sys.path`. The import would then resolve back to this file instead of the package.
"""

from changefeed.cli import main

if __name__ == "__main__":
    main()
