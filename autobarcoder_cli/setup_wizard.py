"""PyPI-installable entry point for the setup wizard.

Delegates to the bin/autobarcoder-setup script when run from the source tree,
or runs an equivalent in-process flow when installed via ``pip install``.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    script = here.parent / "bin" / "autobarcoder-setup"
    if script.exists():
        sys.argv[0] = str(script)
        runpy.run_path(str(script), run_name="__main__")
        return
    print("Setup wizard script not bundled in this install.\n"
          "Clone the source repo to access bin/autobarcoder-setup:\n"
          "  git clone https://github.com/abachu2005/AutoBarcoder-OS-.git")


if __name__ == "__main__":
    main()
