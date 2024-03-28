"""emits a warning when imported under Python < 3.9"""

import logging
import sys

__all__ = []

version_warning = "This package is tested and supported only on Python >= 3.9."

_logger = logging.getLogger(__package__)

if sys.version_info < (3, 9):
    _logger.warning(version_warning)
