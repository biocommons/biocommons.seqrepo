# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import pkg_resources
import warnings

logger = logging.getLogger(__name__)

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound as e:    # pragma: no cover
    warnings.warn("can't get __version__ because %s package isn't installed" % __package__, Warning)
    __version__ = None

logger.info(__name__ + " " + __version__)

from .seqrepo import SeqRepo

# <LICENSE>
# Copyright 2016 biocommons.fastadir Contributors (https://github.com/biocommons/biocommons.fastadir/)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
