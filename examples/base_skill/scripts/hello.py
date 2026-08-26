#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    _ = here  # the path is here only to demonstrate pathlib usage
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
