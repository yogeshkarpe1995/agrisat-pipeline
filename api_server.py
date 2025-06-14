#!/usr/bin/env python3
"""
Main API server entry point - imports from reorganized structure
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.api.server import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)