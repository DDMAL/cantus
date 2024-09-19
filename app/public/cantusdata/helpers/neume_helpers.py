"""
Contains various neume-related constructs that are used throughout the backend,
especially for MEI parsing and OMR search.
"""

from typing import Literal, Dict

# NEUME_NAMES contains the currently-supported neumes. They are
# included in the order used for UI (esp. as neume exemplars).
# Ordering is by:
#   1. The number of pitches in the neume (ascending)
#   2. The the direction of the first interval in the neume (first ascending,
#      then pitch repetition, then descending)
#   3+. The direction of following intervals in the neume (according to 2.)
#   N. The all-purpose "compound" neume at the end
NEUME_NAMES = [
    "punctum",
    "pes",
    "distropha",
    "clivis",
    "scandicus",
    "torculus",
    "tristopha",
    "pressus",
    "porrectus",
    "climacus",
    "scandicus-flexus",
    "torculus-resupinus",
    "pes-subpunctis",
    "porrectus-flexus",
    "climacus-resupinus",
    "scandicus-subpunctis",
    "porrectus-subpunctis",
    "compound",
]

NeumeName = Literal[
    "punctum",
    "pes",
    "distropha",
    "clivis",
    "scandicus",
    "torculus",
    "tristopha",
    "pressus",
    "porrectus",
    "climacus",
    "scandicus-flexus",
    "torculus-resupinus",
    "pes-subpunctis",
    "porrectus-flexus",
    "climacus-resupinus",
    "scandicus-subpunctis",
    "porrectus-subpunctis",
    "compound",
]

# Mapping from neume contours to neume names
NEUME_GROUPS: Dict[str, NeumeName] = {
    "": "punctum",
    "u": "pes",
    "r": "distropha",
    "d": "clivis",
    "uu": "scandicus",
    "ud": "torculus",
    "rr": "tristopha",
    "rd": "pressus",
    "du": "porrectus",
    "dd": "climacus",
    "uud": "scandicus-flexus",
    "udu": "torculus-resupinus",
    "udd": "pes-subpunctis",
    "dud": "porrectus-flexus",
    "ddu": "climacus-resupinus",
    "uudd": "scandicus-subpunctis",
    "dudd": "porrectus-subpunctis",
}
