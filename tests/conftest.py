import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Suppress Python 3.12 unittest RuntimeWarning about missing addDuration
try:
    import unittest

    if not hasattr(unittest.TestResult, "addDuration"):

        def addDuration(self, test, elapsed):  # type: ignore
            # No-op shim to satisfy Python 3.12 expectation
            return None

        unittest.TestResult.addDuration = addDuration  # type: ignore[attr-defined]
except Exception:
    pass
