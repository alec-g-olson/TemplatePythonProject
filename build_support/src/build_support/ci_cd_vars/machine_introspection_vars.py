"""Collection of all functions and variable that report machine properties.

Attributes:
    | THREADS_AVAILABLE: The number of threads available on this machine.
"""

import multiprocessing

THREADS_AVAILABLE = multiprocessing.cpu_count()
