#!/usr/bin/env python3
"""
Textual TUI entry point for productivity tools.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tui import ProductivityApp


def main():
    """Run the TUI application."""
    app = ProductivityApp()
    app.run()


if __name__ == "__main__":
    main()
