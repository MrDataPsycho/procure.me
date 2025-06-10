# SPDX-FileCopyrightText: 2024-present MrDataPsycho <mr.data.psycho@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import sys

# Set up root logger
logging.basicConfig(
    level=logging.INFO,  # or DEBUG for more verbosity
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout
)