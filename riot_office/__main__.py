"""Entry point for ``python -m riot_office``: the window without arguments, the CLI otherwise."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
