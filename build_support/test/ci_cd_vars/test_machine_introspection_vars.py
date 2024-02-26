import multiprocessing
from copy import copy

from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE


def test_get_threads() -> None:
    assert copy(THREADS_AVAILABLE) == multiprocessing.cpu_count()
