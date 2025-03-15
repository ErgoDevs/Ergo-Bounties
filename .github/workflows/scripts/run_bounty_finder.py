#!/usr/bin/env python3
"""
Wrapper script to run the bounty finder.
This script imports and runs the main bounty_finder.py script.
"""

import sys
import os

# Add the current directory to the path so Python can find the bounty_modules package
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the main function from bounty_finder
from bounty_finder import main

if __name__ == "__main__":
    main()
