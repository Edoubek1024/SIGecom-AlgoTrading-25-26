"""
Strategies package for algorithmic trading.
Automatically imports all strategy classes from .py files in this directory.
"""

import os
import importlib
from pathlib import Path

# Get the directory of this __init__.py file
_current_dir = Path(__file__).parent

# Automatically discover and import all strategy classes
__all__ = []

for file in _current_dir.glob("*.py"):
    # Skip __init__.py and any private files
    if file.stem.startswith("_"):
        continue
    
    module_name = file.stem
    
    try:
        # Import the module
        module = importlib.import_module(f".{module_name}", package=__name__)
        
        # Find all classes in the module (assumes class name matches file name or is a capitalized strategy)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Check if it's a class and not a built-in
            if isinstance(attr, type) and not attr_name.startswith("_"):
                # Add to current namespace
                globals()[attr_name] = attr
                __all__.append(attr_name)
    except Exception as e:
        print(f"Warning: Could not import {module_name}: {e}")

# Explicit imports for better IDE support and reliability
from .MeanReversionTrader import MeanReversionTrader
from .MomentumTrader import MomentumTrader

# Ensure they're in __all__
if 'MeanReversionTrader' not in __all__:
    __all__.append('MeanReversionTrader')
if 'MomentumTrader' not in __all__:
    __all__.append('MomentumTrader')
