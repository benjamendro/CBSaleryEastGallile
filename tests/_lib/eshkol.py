"""Access to the Eshkol target list through the project's own matcher.

eshkol_matcher.py is the implementation the pipeline itself relies on, so the
tests import and exercise it rather than restating its rules.
"""

import importlib.util
import sys

from . import paths

EAST_GALILEE = "גליל מזרחי"
WEST_GALILEE = "גליל מערבי"
AUTHORITY = "רשות"


def load_matcher():
    """Import eshkol_matcher.py from its non-package location."""
    spec = importlib.util.spec_from_file_location("eshkol_matcher", paths.ESHKOL_MATCHER_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("eshkol_matcher", module)
    spec.loader.exec_module(module)
    return module


def targets(matcher, affiliation=EAST_GALILEE, entity_type=AUTHORITY):
    """The mapping records for one cluster's authorities."""
    return [matcher.by_code[code] for code in matcher.target_codes(entity_type, affiliation)]
