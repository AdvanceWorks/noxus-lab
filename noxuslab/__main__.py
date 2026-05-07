"""Allow `python -m noxuslab ...` as an alternative to the console script."""

from noxuslab.cli import main

raise SystemExit(main())
