import pytest

import timetree.backend

# Persistence levels from lowest to highest
persistence_levels = [
    pytest.mark.persistence_none,
    pytest.mark.persistence_partial,
    pytest.mark.persistence_full,
    pytest.mark.persistence_confluent,
]

backend_info = [
    (timetree.backend.NopBackend, pytest.mark.persistence_none),
    (timetree.backend.CopyBackend, pytest.mark.persistence_confluent),
    (timetree.backend.BsearchPartialBackend, pytest.mark.persistence_partial),
    (timetree.backend.SplitPartialBackend, pytest.mark.persistence_partial),
    (timetree.backend.BsearchLinearizedFullBackend, pytest.mark.persistence_full),
    (timetree.backend.SplitLinearizedFullBackend, pytest.mark.persistence_full),
]


@pytest.fixture(
    params=backend_info,
    ids=[backend_cls.__name__ for backend_cls, *_ in backend_info],
)
def backend(request):
    """ Fixture to get a backend object """
    backend_cls, backend_level = request.param

    # Find the test's pesistence level
    for level in reversed(persistence_levels):
        if request.node.get_marker(level.name) is not None:
            test_level = level
            break
    else:
        raise ValueError("Test was not marked with a persistence level, "
                         "but requested a backend")

    if persistence_levels.index(backend_level)\
            < persistence_levels.index(test_level):
        request.applymarker(pytest.mark.xfail(
            reason="Persistence level: test needs {} but backend has {}".format(
                test_level.name,
                backend_level.name,
            ),
            raises=NotImplementedError,
        ))

    return backend_cls()


backend2 = backend  # A second backend fixture, if we want two in the same test
