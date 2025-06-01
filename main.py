#!/usr/bin/env python3
"""
Main entry point for the Nova Sonic Speech Agent application.
"""

import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strands_live.cli import run_cli

if __name__ == "__main__":
    run_cli()