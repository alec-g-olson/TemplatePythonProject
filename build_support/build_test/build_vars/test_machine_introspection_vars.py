import multiprocessing

from build_vars.machine_introspection_vars import THREADS_AVAILABLE


def test_get_threads():
    assert THREADS_AVAILABLE == multiprocessing.cpu_count()
