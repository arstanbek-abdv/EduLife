#!/usr/bin/env python3
"""Entry point for Railway: run the app from edulife/ directory."""
import os
import subprocess
import sys

if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    edulife_dir = os.path.join(root, "edulife")
    os.chdir(edulife_dir)
    code = subprocess.run(["sh", "start.sh"]).returncode
    sys.exit(code)
