"""The shared managers are sibling-imported by the skills that use them,
so their own tests need this directory on sys.path -- the same flat shape
a deployed Skill has."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
