#!/usr/bin/env python3
"""Thin CLI entry point — see src/tb_generator.py for the implementation."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tb_generator import main

if __name__ == "__main__":
    main()
